"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { DailyReport } from "@/lib/types";
import { formatDate, DAILY_REPORT_STATUS_LABELS } from "@/lib/utils";
import Link from "next/link";

export default function ReportsPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [generating, setGenerating] = useState(false);

  const { data: reports = [], isLoading } = useQuery<DailyReport[]>({
    queryKey: ["daily-reports", id],
    queryFn: () => api.get(`/projects/${id}/daily-reports`).then((r) => r.data),
  });

  async function handleGenerate(formData: Record<string, unknown>) {
    setGenerating(true);
    try {
      await api.post(`/projects/${id}/daily-reports/generate`, formData);
      qc.invalidateQueries({ queryKey: ["daily-reports", id] });
      setShowGenerateForm(false);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            </div>
            <h1>작업일보 · 공정보고서</h1>
          </div>
          <button className="btn-primary" onClick={() => setShowGenerateForm(!showGenerateForm)}>
            🤖 AI 일보 생성
          </button>
        </div>

        {showGenerateForm && (
          <div className="card p-5">
            <h3 className="mb-4">AI 작업일보 생성</h3>
            <GenerateDailyReportForm
              onSubmit={handleGenerate}
              onCancel={() => setShowGenerateForm(false)}
              loading={generating}
            />
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <span className="font-semibold">일보 목록</span>
            <span className="text-gray-400 text-sm">{reports.length}건</span>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>작업일</th>
                  <th>날씨</th>
                  <th>작업내용 (요약)</th>
                  <th>생성방식</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={5} className="text-center py-8 text-gray-400">로딩 중...</td></tr>
                ) : reports.length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-8 text-gray-400">작업일보가 없습니다</td></tr>
                ) : (
                  reports.map((r) => (
                    <tr key={r.id}>
                      <td className="font-medium">{formatDate(r.report_date)}</td>
                      <td>{r.weather_summary || "-"}</td>
                      <td className="max-w-xs truncate text-gray-600">{r.work_content?.slice(0, 60) || "-"}...</td>
                      <td>{r.ai_generated ? <span className="badge badge-blue">AI 생성</span> : <span className="badge badge-gray">수동</span>}</td>
                      <td>
                        <span className={`badge ${r.status === "confirmed" ? "badge-green" : r.status === "submitted" ? "badge-blue" : "badge-gray"}`}>
                          {DAILY_REPORT_STATUS_LABELS[r.status]}
                        </span>
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

function GenerateDailyReportForm({
  onSubmit, onCancel, loading,
}: {
  onSubmit: (data: Record<string, unknown>) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const today = new Date().toISOString().split("T")[0];
  const [reportDate, setReportDate] = useState(today);
  const [workItems, setWorkItems] = useState("");
  const [workers, setWorkers] = useState("");  // "콘크리트 5, 철근 3"
  const [issues, setIssues] = useState("");

  function parseWorkers(input: string): Record<string, number> {
    const result: Record<string, number> = {};
    const parts = input.split(/[,，]/).map((s) => s.trim());
    for (const part of parts) {
      const match = part.match(/^(.+?)\s+(\d+)$/);
      if (match) result[match[1].trim()] = Number(match[2]);
    }
    return result;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      report_date: reportDate,
      workers_count: parseWorkers(workers),
      work_items: workItems.split("\n").filter(Boolean),
      issues: issues || undefined,
      equipment_list: [],
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">작업일 *</label>
          <input className="input" type="date" value={reportDate} onChange={(e) => setReportDate(e.target.value)} required />
        </div>
        <div>
          <label className="label">투입인원 (예: 콘크리트 5, 철근 3)</label>
          <input className="input" value={workers} onChange={(e) => setWorkers(e.target.value)} placeholder="콘크리트 5, 철근 3, 목수 2" />
        </div>
      </div>
      <div>
        <label className="label">작업 항목 (한 줄에 하나씩) *</label>
        <textarea
          className="input min-h-[80px]"
          value={workItems}
          onChange={(e) => setWorkItems(e.target.value)}
          placeholder={"관로매설 50m 완료\n되메우기 작업\n시험성토 진행"}
          required
        />
      </div>
      <div>
        <label className="label">특이사항</label>
        <input className="input" value={issues} onChange={(e) => setIssues(e.target.value)} placeholder="특이사항 없으면 빈칸" />
      </div>
      <div className="flex gap-2 justify-end pt-2">
        <button type="button" className="btn-secondary" onClick={onCancel}>취소</button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "AI 생성중..." : "🤖 일보 생성"}
        </button>
      </div>
    </form>
  );
}
