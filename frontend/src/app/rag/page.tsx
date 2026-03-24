"use client";
import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { RagAnswer } from "@/lib/types";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  sources?: RagAnswer["sources"];
  disclaimer?: string;
}

export default function RagPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      type: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setLoading(true);

    try {
      const resp = await api.post<RagAnswer>("/rag/ask", { question: userMsg.content, top_k: 5 });
      const data = resp.data;
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.answer,
        sources: data.sources,
        disclaimer: data.disclaimer,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), type: "assistant", content: "오류가 발생했습니다. 잠시 후 다시 시도해주세요." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-4">
        <div>
          <h1>법규·시방서 Q&A</h1>
          <p className="text-gray-500 text-sm mt-1">
            건설기술진흥법, 산업안전보건법, 중대재해처벌법, KCS 시방서에 대해 질문하세요
          </p>
        </div>

        {/* Chat history */}
        <div className="card min-h-[400px] flex flex-col">
          <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[500px]">
            {messages.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <div className="text-4xl mb-3">📚</div>
                <p className="font-medium text-gray-600">건설 법규·시방서 질문을 입력하세요</p>
                <div className="mt-4 space-y-2">
                  {[
                    "콘크리트 타설 최저기온 기준은?",
                    "굴착 5m 이상 흙막이 설치 기준",
                    "중대재해처벌법 적용 대상은?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => setQuestion(q)}
                      className="block w-full text-left px-3 py-2 rounded-lg bg-gray-50 hover:bg-brand-50 text-sm text-gray-600 border border-gray-200 transition-colors"
                    >
                      💬 {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[80%] rounded-xl px-4 py-3 ${msg.type === "user" ? "bg-brand-500 text-white" : "bg-gray-100 text-gray-900"}`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs text-gray-500 font-medium mb-1">참고 출처</p>
                        <div className="space-y-1">
                          {msg.sources.slice(0, 3).map((s) => (
                            <div key={s.id} className="text-xs text-gray-600 bg-white rounded px-2 py-1 border border-gray-200">
                              <span className="font-medium">{s.title}</span>
                              <span className="text-gray-400 ml-1">({(s.relevance_score * 100).toFixed(0)}%)</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {msg.disclaimer && (
                      <p className="text-xs text-gray-400 mt-2">⚠️ {msg.disclaimer}</p>
                    )}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-xl px-4 py-3 text-sm text-gray-500">
                  검색 중...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-gray-100 p-4">
            <form onSubmit={handleAsk} className="flex gap-2">
              <input
                className="input flex-1"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="법규 또는 시방서에 대해 질문하세요..."
                disabled={loading}
              />
              <button type="submit" className="btn-primary px-5" disabled={loading || !question.trim()}>
                전송
              </button>
            </form>
          </div>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center">
          이 답변은 참고용이며 법률 자문이 아닙니다. 중요 사항은 전문가에게 확인하세요.
        </p>
      </div>
    </AppLayout>
  );
}
