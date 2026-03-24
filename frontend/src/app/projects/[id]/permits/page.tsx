"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { PermitItem, PermitStatus } from "@/lib/types";
import { formatDate, PERMIT_STATUS_LABELS, PERMIT_STATUS_COLORS } from "@/lib/utils";
import Link from "next/link";

export default function PermitsPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: permits = [], isLoading } = useQuery<PermitItem[]>({
    queryKey: ["permits", id],
    queryFn: () => api.get(`/projects/${id}/permits`).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post(`/projects/${id}/permits`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["permits", id] }); setShowForm(false); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ permitId, status }: { permitId: string; status: PermitStatus }) =>
      api.put(`/projects/${id}/permits/${permitId}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["permits", id] }),
  });

  const approvedCount = permits.filter((p) => p.status === "approved").length;
  const progress = permits.length > 0 ? Math.round((approvedCount / permits.length) * 100) : 0;

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            <h1 className="mt-1">인허가 체크리스트</h1>
          </div>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            ➕ 인허가 추가
          </button>
        </div>

        {/* Progress */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">인허가 진행률</span>
            <span className="text-sm text-gray-500">{approvedCount}/{permits.length} 승인완료</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-green-500 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="text-xs text-gray-400 mt-1">{progress}% 완료</p>
        </div>

        {showForm && (
          <div className="card p-5">
            <h3 className="mb-4">인허가 항목 추가</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.target as HTMLFormElement);
                createMutation.mutate({
                  permit_type: fd.get("permit_type"),
                  authority: fd.get("authority") || undefined,
                  deadline: fd.get("deadline") || undefined,
                  notes: fd.get("notes") || undefined,
                });
              }}
              className="grid grid-cols-2 gap-4"
            >
              <div>
                <label className="label">인허가 종류 *</label>
                <input name="permit_type" className="input" required placeholder="도로점용허가" />
              </div>
              <div>
                <label className="label">관할 관청</label>
                <input name="authority" className="input" placeholder="○○시청 건설과" />
              </div>
              <div>
                <label className="label">제출 기한</label>
                <input name="deadline" className="input" type="date" />
              </div>
              <div>
                <label className="label">비고</label>
                <input name="notes" className="input" />
              </div>
              <div className="col-span-2 flex gap-2 justify-end">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>취소</button>
                <button type="submit" className="btn-primary" disabled={createMutation.isPending}>추가</button>
              </div>
            </form>
          </div>
        )}

        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>인허가 종류</th>
                  <th>관할 관청</th>
                  <th>제출기한</th>
                  <th>제출일</th>
                  <th>승인일</th>
                  <th>상태</th>
                  <th>변경</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={7} className="text-center py-8 text-gray-400">로딩 중...</td></tr>
                ) : permits.length === 0 ? (
                  <tr><td colSpan={7} className="text-center py-8 text-gray-400">인허가 항목이 없습니다</td></tr>
                ) : (
                  permits.map((p) => (
                    <tr key={p.id}>
                      <td className="font-medium">{p.permit_type}</td>
                      <td>{p.authority || "-"}</td>
                      <td>{p.deadline ? formatDate(p.deadline) : "-"}</td>
                      <td>{p.submitted_date ? formatDate(p.submitted_date) : "-"}</td>
                      <td>{p.approved_date ? formatDate(p.approved_date) : "-"}</td>
                      <td>
                        <span className={`badge ${PERMIT_STATUS_COLORS[p.status]}`}>
                          {PERMIT_STATUS_LABELS[p.status]}
                        </span>
                      </td>
                      <td>
                        <select
                          className="text-xs border border-gray-200 rounded px-2 py-1"
                          value={p.status}
                          onChange={(e) => updateMutation.mutate({ permitId: p.id, status: e.target.value as PermitStatus })}
                        >
                          {Object.entries(PERMIT_STATUS_LABELS).map(([k, v]) => (
                            <option key={k} value={k}>{v}</option>
                          ))}
                        </select>
                      </td>
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
