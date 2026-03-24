"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { CompletionChecklist } from "@/lib/types";

export default function CompletionPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: checklist = [], isLoading } = useQuery<CompletionChecklist[]>({
    queryKey: ["completion-checklist", projectId],
    queryFn: () => api.get(`/projects/${projectId}/completion/checklist`).then((r) => r.data),
  });

  const grouped = checklist.reduce<Record<string, CompletionChecklist[]>>((acc, item) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  const total = checklist.length;
  const ready = checklist.filter((c) => c.available).length;
  const pct = total > 0 ? Math.round((ready / total) * 100) : 0;

  const handleDownload = async () => {
    const res = await api.get(`/projects/${projectId}/completion/download`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `completion_${projectId}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">준공도서 패키지</h1>
          <button
            onClick={handleDownload}
            className="btn-primary"
          >
            ⬇ ZIP 다운로드
          </button>
        </div>

        {/* Progress */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-600">준공 준비도</span>
            <span className="text-xl font-bold text-blue-600">{pct}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${pct >= 80 ? "bg-green-400" : pct >= 50 ? "bg-yellow-400" : "bg-red-400"}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {ready}/{total}개 항목 준비 완료
            {pct < 100 && ` · ${total - ready}개 항목 미비`}
          </p>
        </div>

        {isLoading && <p className="text-gray-400">로딩 중...</p>}

        {/* Checklist by category */}
        {Object.entries(grouped).map(([category, items]) => {
          const catReady = items.filter((i) => i.available).length;
          return (
            <div key={category} className="card p-0 overflow-hidden">
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
                <span className="font-semibold text-sm">{category}</span>
                <span className="text-xs text-gray-500">
                  {catReady}/{items.length}
                </span>
              </div>
              <div className="divide-y divide-gray-50">
                {items.map((item, i) => (
                  <div key={i} className="px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-base">{item.available ? "✅" : "❌"}</span>
                      <span className={`text-sm ${item.available ? "text-gray-800" : "text-gray-400"}`}>
                        {item.item}
                      </span>
                    </div>
                    {item.count != null && (
                      <span className="text-xs text-gray-400">{item.count}건</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {!isLoading && checklist.length === 0 && (
          <div className="card p-8 text-center text-gray-400">
            <p className="text-lg mb-2">체크리스트 항목이 없습니다</p>
            <p className="text-sm">프로젝트 데이터가 입력되면 자동으로 생성됩니다.</p>
          </div>
        )}

        <div className="card p-4 bg-blue-50 border border-blue-100">
          <h3 className="text-sm font-semibold text-blue-700 mb-2">📦 ZIP 패키지 포함 내용</h3>
          <ul className="text-xs text-blue-600 space-y-1">
            <li>• 준공 요약서 (PDF)</li>
            <li>• 품질시험 결과 목록 (PDF)</li>
            <li>• 검측요청서 전체 (PDF)</li>
            <li>• 인허가 현황 (PDF)</li>
            <li>• 현장 사진 원본</li>
          </ul>
        </div>
      </div>
    </AppLayout>
  );
}
