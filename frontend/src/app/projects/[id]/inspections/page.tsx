"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { InspectionRequest } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

const INSPECTION_TYPES = [
  "철근 검측", "거푸집 검측", "콘크리트 타설 전 검측",
  "관로 매설 검측", "성토 다짐 검측", "도로 포장 검측", "기타",
];

export default function InspectionsPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [generating, setGenerating] = useState(false);

  const { data: inspections = [], isLoading } = useQuery<InspectionRequest[]>({
    queryKey: ["inspections", id],
    queryFn: () => api.get(`/projects/${id}/inspections`).then((r) => r.data),
  });

  async function handleGenerate(data: Record<string, unknown>) {
    setGenerating(true);
    try {
      await api.post(`/projects/${id}/inspections/generate`, data);
      qc.invalidateQueries({ queryKey: ["inspections", id] });
      setShowForm(false);
    } finally {
      setGenerating(false);
    }
  }

  const resultLabels: Record<string, { label: string; cls: string }> = {
    pass: { label: "합격", cls: "badge-green" },
    fail: { label: "불합격", cls: "badge-red" },
    conditional_pass: { label: "조건부 합격", cls: "badge-yellow" },
  };

  const statusLabels: Record<string, string> = {
    draft: "초안", sent: "발송완료", completed: "검측완료",
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            <h1 className="mt-1">검측요청서</h1>
          </div>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            🤖 AI 검측요청서 생성
          </button>
        </div>

        {showForm && (
          <div className="card p-5">
            <h3 className="mb-4">검측요청서 AI 생성</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.target as HTMLFormElement);
                handleGenerate({
                  inspection_type: fd.get("inspection_type"),
                  requested_date: fd.get("requested_date"),
                  location_detail: fd.get("location_detail") || undefined,
                });
              }}
              className="grid grid-cols-2 gap-4"
            >
              <div>
                <label className="label">공종 *</label>
                <select name="inspection_type" className="input" required>
                  {INSPECTION_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label">검측 요청일 *</label>
                <input name="requested_date" className="input" type="date" required defaultValue={new Date().toISOString().split("T")[0]} />
              </div>
              <div className="col-span-2">
                <label className="label">위치 상세</label>
                <input name="location_detail" className="input" placeholder="예: 3공구 A구간 STA.1+200~1+350" />
              </div>
              <div className="col-span-2 flex gap-2 justify-end">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>취소</button>
                <button type="submit" className="btn-primary" disabled={generating}>
                  {generating ? "AI 생성중..." : "🤖 체크리스트 생성"}
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>요청일</th>
                  <th>공종</th>
                  <th>위치</th>
                  <th>체크리스트</th>
                  <th>결과</th>
                  <th>상태</th>
                  <th>생성방식</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={7} className="text-center py-8 text-gray-400">로딩 중...</td></tr>
                ) : inspections.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-8 text-gray-400">검측요청서가 없습니다</td></tr>
                ) : (
                  inspections.map((insp) => (
                    <tr key={insp.id}>
                      <td>{formatDate(insp.requested_date)}</td>
                      <td className="font-medium">{insp.inspection_type}</td>
                      <td>{insp.location_detail || "-"}</td>
                      <td>{insp.checklist_items ? `${insp.checklist_items.length}개 항목` : "-"}</td>
                      <td>
                        {insp.result ? (
                          <span className={`badge ${resultLabels[insp.result]?.cls}`}>{resultLabels[insp.result]?.label}</span>
                        ) : "-"}
                      </td>
                      <td><span className="badge badge-gray">{statusLabels[insp.status]}</span></td>
                      <td>{insp.ai_generated ? <span className="badge badge-blue">AI</span> : <span className="badge badge-gray">수동</span>}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
