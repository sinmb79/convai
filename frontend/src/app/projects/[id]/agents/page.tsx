"use client";
import { useState, useRef, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { AgentConversation, AgentMessage, AgentType } from "@/lib/types";

const AGENT_INFO: Record<AgentType, { name: string; emoji: string; desc: string; color: string }> = {
  gongsa: { name: "공사 에이전트", emoji: "🏗", desc: "공정 브리핑, 지연 분석", color: "bg-blue-50 border-blue-200" },
  pumjil: { name: "품질 에이전트", emoji: "✅", desc: "품질 체크리스트, KCS 기준", color: "bg-green-50 border-green-200" },
  anjeon: { name: "안전 에이전트", emoji: "⛑", desc: "TBM 자료, 안전 경보", color: "bg-red-50 border-red-200" },
  gumu: { name: "공무 에이전트", emoji: "📋", desc: "인허가 추적, 기성 청구", color: "bg-purple-50 border-purple-200" },
};

const SCENARIOS = [
  { id: "concrete_pour", label: "🪨 콘크리트 타설", desc: "공사→품질→안전 순서로 브리핑" },
  { id: "excavation", label: "⛏ 굴착 작업", desc: "공사→안전→품질 순서로 브리핑" },
  { id: "weekly_report", label: "📊 주간 보고", desc: "공사→품질→공무 순서로 요약" },
];

export default function AgentsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const qc = useQueryClient();

  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [inputText, setInputText] = useState("");
  const [quickInput, setQuickInput] = useState("");
  const [scenarioResult, setScenarioResult] = useState<Array<{ agent: string; agent_name: string; content: string }> | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: conversations = [] } = useQuery<AgentConversation[]>({
    queryKey: ["agents", projectId],
    queryFn: () => api.get(`/projects/${projectId}/agents`).then((r) => r.data),
  });

  const { data: messages = [], isLoading: msgLoading } = useQuery<AgentMessage[]>({
    queryKey: ["agent-messages", selectedConvId],
    queryFn: () => api.get(`/projects/${projectId}/agents/${selectedConvId}/messages`).then((r) => r.data),
    enabled: !!selectedConvId,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMsgMutation = useMutation({
    mutationFn: (content: string) =>
      api.post(`/projects/${projectId}/agents/${selectedConvId}/messages`, { content }).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent-messages", selectedConvId] });
      setInputText("");
    },
  });

  const quickChatMutation = useMutation({
    mutationFn: (content: string) =>
      api.post(`/projects/${projectId}/agents/chat`, { content }).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["agents", projectId] });
      setSelectedConvId(data.conversation_id);
      setQuickInput("");
    },
  });

  const briefingMutation = useMutation({
    mutationFn: () =>
      api.post(`/projects/${projectId}/agents/briefing`).then((r) => r.data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["agents", projectId] });
      setSelectedConvId(data.conversation_id);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (convId: string) => api.delete(`/projects/${projectId}/agents/${convId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agents", projectId] });
      setSelectedConvId(null);
    },
  });

  const runScenario = async (scenarioId: string) => {
    setScenarioLoading(true);
    setScenarioResult(null);
    try {
      const r = await api.post(`/projects/${projectId}/agents/scenario/${scenarioId}`);
      setScenarioResult(r.data.steps);
      qc.invalidateQueries({ queryKey: ["agents", projectId] });
    } finally {
      setScenarioLoading(false);
    }
  };

  const selectedConv = conversations.find((c) => c.id === selectedConvId);

  return (
    <AppLayout>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">AI 에이전트</h1>
          <button
            onClick={() => briefingMutation.mutate()}
            disabled={briefingMutation.isPending}
            className="btn-primary text-sm"
          >
            {briefingMutation.isPending ? "생성 중..." : "🌅 오늘 아침 브리핑"}
          </button>
        </div>

        {/* Agent Cards */}
        <div className="grid grid-cols-4 gap-3">
          {(Object.entries(AGENT_INFO) as [AgentType, typeof AGENT_INFO[AgentType]][]).map(([type, info]) => (
            <div key={type} className={`card p-3 border ${info.color}`}>
              <div className="text-2xl mb-1">{info.emoji}</div>
              <div className="font-semibold text-sm">{info.name}</div>
              <div className="text-xs text-gray-500 mt-0.5">{info.desc}</div>
            </div>
          ))}
        </div>

        {/* Quick Chat */}
        <div className="card p-4">
          <h2 className="font-semibold mb-3 text-sm text-gray-600">빠른 질문 (에이전트 자동 선택)</h2>
          <div className="flex gap-2">
            <input
              className="input flex-1 text-sm"
              placeholder="예: 오늘 콘크리트 타설 전 체크리스트 알려줘"
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && quickInput.trim() && quickChatMutation.mutate(quickInput.trim())}
            />
            <button
              className="btn-primary text-sm"
              onClick={() => quickInput.trim() && quickChatMutation.mutate(quickInput.trim())}
              disabled={quickChatMutation.isPending || !quickInput.trim()}
            >
              {quickChatMutation.isPending ? "..." : "전송"}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Conversation List */}
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 text-sm font-semibold text-gray-600">대화 목록</div>
            <div className="divide-y divide-gray-50 max-h-96 overflow-y-auto">
              {conversations.length === 0 && (
                <p className="text-xs text-gray-400 p-4">대화가 없습니다</p>
              )}
              {conversations.map((conv) => {
                const info = AGENT_INFO[conv.agent_type];
                return (
                  <button
                    key={conv.id}
                    onClick={() => setSelectedConvId(conv.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${selectedConvId === conv.id ? "bg-blue-50" : ""}`}
                  >
                    <div className="flex items-center gap-2">
                      <span>{info.emoji}</span>
                      <span className="text-xs font-medium truncate">{conv.title || info.name}</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">{conv.message_count}개 메시지</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Chat Window */}
          <div className="col-span-2 card p-0 overflow-hidden flex flex-col" style={{ height: 420 }}>
            {!selectedConvId ? (
              <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
                대화를 선택하거나 빠른 질문을 입력하세요
              </div>
            ) : (
              <>
                <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>{AGENT_INFO[selectedConv?.agent_type ?? "gongsa"].emoji}</span>
                    <span className="text-sm font-semibold">{selectedConv?.title}</span>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(selectedConvId)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    삭제
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  {msgLoading && <p className="text-xs text-gray-400">불러오는 중...</p>}
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] text-sm px-3 py-2 rounded-xl whitespace-pre-wrap ${
                          msg.role === "user"
                            ? "bg-blue-500 text-white rounded-br-sm"
                            : "bg-gray-100 text-gray-800 rounded-bl-sm"
                        }`}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {sendMsgMutation.isPending && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 text-gray-400 text-sm px-3 py-2 rounded-xl rounded-bl-sm">
                        답변 생성 중...
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="px-4 py-3 border-t border-gray-100 flex gap-2">
                  <input
                    className="input flex-1 text-sm"
                    placeholder="메시지 입력..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && inputText.trim() && sendMsgMutation.mutate(inputText.trim())
                    }
                  />
                  <button
                    className="btn-primary text-sm"
                    onClick={() => inputText.trim() && sendMsgMutation.mutate(inputText.trim())}
                    disabled={sendMsgMutation.isPending || !inputText.trim()}
                  >
                    전송
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Collaboration Scenarios */}
        <div className="card p-4">
          <h2 className="font-semibold mb-3">협업 시나리오</h2>
          <div className="grid grid-cols-3 gap-3">
            {SCENARIOS.map((s) => (
              <button
                key={s.id}
                onClick={() => runScenario(s.id)}
                disabled={scenarioLoading}
                className="card p-3 text-left hover:shadow-md transition-shadow border border-gray-200"
              >
                <div className="font-medium text-sm">{s.label}</div>
                <div className="text-xs text-gray-500 mt-1">{s.desc}</div>
              </button>
            ))}
          </div>

          {scenarioLoading && (
            <div className="mt-4 text-sm text-blue-500 text-center">에이전트들이 협업 중...</div>
          )}

          {scenarioResult && (
            <div className="mt-4 space-y-3">
              {scenarioResult.map((step, i) => {
                const info = AGENT_INFO[step.agent as AgentType];
                return (
                  <div key={i} className={`rounded-xl p-4 border ${info?.color || "bg-gray-50"}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span>{info?.emoji}</span>
                      <span className="font-semibold text-sm">{step.agent_name}</span>
                      <span className="text-xs text-gray-400">Step {i + 1}</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap text-gray-700">{step.content}</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
