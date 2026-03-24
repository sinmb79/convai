"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { Project, ConstructionType } from "@/lib/types";
import { formatDate, formatCurrency, PROJECT_STATUS_LABELS, CONSTRUCTION_TYPE_LABELS } from "@/lib/utils";
import Link from "next/link";

export default function ProjectsPage() {
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post("/projects", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      setShowForm(false);
    },
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1>프로젝트 목록</h1>
            <p className="text-gray-500 text-sm mt-1">등록된 공사 현장을 관리합니다</p>
          </div>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            ➕ 새 현장
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <div className="card p-5">
            <h3 className="mb-4">새 현장 등록</h3>
            <CreateProjectForm
              onSubmit={(data) => createMutation.mutate(data)}
              onCancel={() => setShowForm(false)}
              loading={createMutation.isPending}
            />
          </div>
        )}

        {/* Projects table */}
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>현장명</th>
                  <th>코드</th>
                  <th>공종</th>
                  <th>착공일</th>
                  <th>준공일</th>
                  <th>계약금액</th>
                  <th>상태</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="text-center text-gray-400 py-8">
                      로딩 중...
                    </td>
                  </tr>
                ) : projects.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center text-gray-400 py-8">
                      등록된 현장이 없습니다
                    </td>
                  </tr>
                ) : (
                  projects.map((p) => (
                    <tr key={p.id}>
                      <td className="font-medium">{p.name}</td>
                      <td className="text-gray-500 font-mono text-xs">{p.code}</td>
                      <td>{CONSTRUCTION_TYPE_LABELS[p.construction_type]}</td>
                      <td>{formatDate(p.start_date)}</td>
                      <td>{formatDate(p.end_date)}</td>
                      <td>{formatCurrency(p.contract_amount)}</td>
                      <td>
                        <StatusBadge status={p.status} />
                      </td>
                      <td>
                        <Link href={`/projects/${p.id}`} className="btn-secondary text-xs py-1 px-2">
                          상세 →
                        </Link>
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

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "active" ? "badge-green" :
    status === "planning" ? "badge-blue" :
    status === "suspended" ? "badge-yellow" :
    "badge-gray";
  return <span className={`badge ${cls}`}>{PROJECT_STATUS_LABELS[status]}</span>;
}

function CreateProjectForm({
  onSubmit,
  onCancel,
  loading,
}: {
  onSubmit: (data: Record<string, unknown>) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [form, setForm] = useState({
    name: "",
    code: "",
    construction_type: "other" as ConstructionType,
    start_date: "",
    end_date: "",
    contract_amount: "",
    location_address: "",
  });

  const set = (field: string, val: string) => setForm((f) => ({ ...f, [field]: val }));

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      contract_amount: form.contract_amount ? Number(form.contract_amount) : undefined,
      start_date: form.start_date || undefined,
      end_date: form.end_date || undefined,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
      <div>
        <label className="label">공사명 *</label>
        <input className="input" value={form.name} onChange={(e) => set("name", e.target.value)} required />
      </div>
      <div>
        <label className="label">현장코드 *</label>
        <input className="input" value={form.code} onChange={(e) => set("code", e.target.value)} required placeholder="PROJ-2026-001" />
      </div>
      <div>
        <label className="label">공종</label>
        <select className="input" value={form.construction_type} onChange={(e) => set("construction_type", e.target.value)}>
          {Object.entries(CONSTRUCTION_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="label">도급금액 (원)</label>
        <input className="input" type="number" value={form.contract_amount} onChange={(e) => set("contract_amount", e.target.value)} />
      </div>
      <div>
        <label className="label">착공일</label>
        <input className="input" type="date" value={form.start_date} onChange={(e) => set("start_date", e.target.value)} />
      </div>
      <div>
        <label className="label">준공예정일</label>
        <input className="input" type="date" value={form.end_date} onChange={(e) => set("end_date", e.target.value)} />
      </div>
      <div className="col-span-2">
        <label className="label">공사 위치</label>
        <input className="input" value={form.location_address} onChange={(e) => set("location_address", e.target.value)} placeholder="시/군/구 위치" />
      </div>
      <div className="col-span-2 flex gap-2 justify-end pt-2">
        <button type="button" className="btn-secondary" onClick={onCancel}>취소</button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "저장 중..." : "현장 등록"}
        </button>
      </div>
    </form>
  );
}
