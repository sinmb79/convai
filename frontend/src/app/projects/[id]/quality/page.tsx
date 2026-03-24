"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

interface QualityTest {
  id: string;
  test_type: string;
  test_date: string;
  location_detail?: string;
  design_value?: number;
  measured_value: number;
  unit: string;
  result: "pass" | "fail";
  lab_name?: string;
  notes?: string;
}

const TEST_TYPES = [
  "콘크리트 압축강도", "슬럼프 시험", "공기량 시험",
  "다짐도 시험", "CBR 시험", "체분석 시험", "기타",
];

export default function QualityPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: tests = [], isLoading } = useQuery<QualityTest[]>({
    queryKey: ["quality-tests", id],
    queryFn: () => api.get(`/projects/${id}/quality-tests`).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post(`/projects/${id}/quality-tests`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["quality-tests", id] }); setShowForm(false); },
  });

  const passCount = tests.filter((t) => t.result === "pass").length;
  const failCount = tests.filter((t) => t.result === "fail").length;

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            <h1 className="mt-1">품질시험 기록</h1>
          </div>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>➕ 시험 기록</button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{tests.length}</p>
            <p className="text-xs text-gray-500">전체 시험</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{passCount}</p>
            <p className="text-xs text-gray-500">합격</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-red-600">{failCount}</p>
            <p className="text-xs text-gray-500">불합격</p>
          </div>
        </div>

        {showForm && (
          <div className="card p-5">
            <h3 className="mb-4">품질시험 기록 추가</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.target as HTMLFormElement);
                const designVal = fd.get("design_value");
                const measuredVal = Number(fd.get("measured_value"));
                const designNum = designVal ? Number(designVal) : undefined;
                // Auto-determine result
                const result = designNum != null
                  ? (measuredVal >= designNum ? "pass" : "fail")
                  : (fd.get("result") as string);

                createMutation.mutate({
                  test_type: fd.get("test_type"),
                  test_date: fd.get("test_date"),
                  location_detail: fd.get("location_detail") || undefined,
                  design_value: designNum,
                  measured_value: measuredVal,
                  unit: fd.get("unit"),
                  result,
                  lab_name: fd.get("lab_name") || undefined,
                  notes: fd.get("notes") || undefined,
                });
              }}
              className="grid grid-cols-2 gap-4"
            >
              <div>
                <label className="label">시험 종류 *</label>
                <select name="test_type" className="input" required>
                  {TEST_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="label">시험일 *</label>
                <input name="test_date" className="input" type="date" required defaultValue={new Date().toISOString().split("T")[0]} />
              </div>
              <div>
                <label className="label">설계기준값</label>
                <input name="design_value" className="input" type="number" step="0.1" />
              </div>
              <div>
                <label className="label">측정값 *</label>
                <input name="measured_value" className="input" type="number" step="0.1" required />
              </div>
              <div>
                <label className="label">단위 *</label>
                <input name="unit" className="input" required placeholder="MPa, mm, % ..." defaultValue="MPa" />
              </div>
              <div>
                <label className="label">시험기관</label>
                <input name="lab_name" className="input" placeholder="○○시험연구원" />
              </div>
              <div className="col-span-2">
                <label className="label">위치 상세</label>
                <input name="location_detail" className="input" placeholder="3공구 A구간" />
              </div>
              <div className="col-span-2 flex gap-2 justify-end">
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>취소</button>
                <button type="submit" className="btn-primary" disabled={createMutation.isPending}>저장</button>
              </div>
            </form>
          </div>
        )}

        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>시험일</th><th>종류</th><th>위치</th><th>기준값</th><th>측정값</th><th>단위</th><th>결과</th><th>기관</th></tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={8} className="text-center py-8 text-gray-400">로딩 중...</td></tr>
                ) : tests.length === 0 ? (
                  <tr><td colSpan={8} className="text-center py-8 text-gray-400">시험 기록이 없습니다</td></tr>
                ) : (
                  tests.map((t) => (
                    <tr key={t.id}>
                      <td>{formatDate(t.test_date)}</td>
                      <td className="font-medium">{t.test_type}</td>
                      <td>{t.location_detail || "-"}</td>
                      <td>{t.design_value != null ? t.design_value : "-"}</td>
                      <td className="font-semibold">{t.measured_value}</td>
                      <td>{t.unit}</td>
                      <td>
                        <span className={`badge ${t.result === "pass" ? "badge-green" : "badge-red"}`}>
                          {t.result === "pass" ? "합격" : "불합격"}
                        </span>
                      </td>
                      <td>{t.lab_name || "-"}</td>
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
