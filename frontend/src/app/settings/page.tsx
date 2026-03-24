"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";

type Tab = "client-profiles" | "work-types" | "export-import";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("client-profiles");

  const tabs: { id: Tab; label: string }[] = [
    { id: "client-profiles", label: "🏢 발주처 프로파일" },
    { id: "work-types", label: "⚙️ 공종 라이브러리" },
    { id: "export-import", label: "📦 설정 내보내기/가져오기" },
  ];

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1>설정</h1>
          <p className="text-gray-500 text-sm mt-1">발주처, 공종, 알림 규칙을 관리합니다</p>
        </div>

        <div className="flex gap-1 border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id ? "border-brand-500 text-brand-500" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "client-profiles" && <ClientProfilesTab />}
        {activeTab === "work-types" && <WorkTypesTab />}
        {activeTab === "export-import" && <ExportImportTab />}
      </div>
    </AppLayout>
  );
}

function ClientProfilesTab() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: profiles = [] } = useQuery({
    queryKey: ["client-profiles"],
    queryFn: () => api.get("/settings/client-profiles").then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post("/settings/client-profiles", data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["client-profiles"] }); setShowForm(false); },
  });

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-500">{profiles.length}개 발주처 등록됨</span>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>➕ 발주처 추가</button>
      </div>

      {showForm && (
        <div className="card p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.target as HTMLFormElement);
              createMutation.mutate({ name: fd.get("name"), report_frequency: fd.get("report_frequency") });
            }}
            className="flex gap-3 items-end"
          >
            <div className="flex-1">
              <label className="label">발주처명 *</label>
              <input name="name" className="input" required placeholder="LH공사, ○○시청 등" />
            </div>
            <div>
              <label className="label">보고 주기</label>
              <select name="report_frequency" className="input">
                <option value="weekly">주간</option>
                <option value="biweekly">격주</option>
                <option value="monthly">월간</option>
              </select>
            </div>
            <button type="submit" className="btn-primary">추가</button>
            <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>취소</button>
          </form>
        </div>
      )}

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr><th>발주처명</th><th>보고 주기</th></tr>
            </thead>
            <tbody>
              {profiles.length === 0 ? (
                <tr><td colSpan={2} className="text-center py-6 text-gray-400">등록된 발주처가 없습니다</td></tr>
              ) : (
                profiles.map((p: { id: string; name: string; report_frequency: string }) => (
                  <tr key={p.id}>
                    <td className="font-medium">{p.name}</td>
                    <td>{p.report_frequency === "weekly" ? "주간" : p.report_frequency === "monthly" ? "월간" : "격주"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function WorkTypesTab() {
  const { data: workTypes = [] } = useQuery({
    queryKey: ["work-types"],
    queryFn: () => api.get("/settings/work-types").then((r) => r.data),
  });

  return (
    <div className="card">
      <div className="table-container">
        <table className="table">
          <thead>
            <tr><th>코드</th><th>공종명</th><th>카테고리</th><th>기상 제약</th><th>종류</th></tr>
          </thead>
          <tbody>
            {workTypes.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-6 text-gray-400">공종이 없습니다</td></tr>
            ) : (
              workTypes.map((wt: { id: string; code: string; name: string; category: string; weather_constraints: Record<string, unknown>; is_system: boolean }) => (
                <tr key={wt.id}>
                  <td className="font-mono text-xs">{wt.code}</td>
                  <td className="font-medium">{wt.name}</td>
                  <td>{wt.category}</td>
                  <td className="text-xs text-gray-500">
                    {wt.weather_constraints ? (
                      <span>
                        {wt.weather_constraints.min_temp != null && `최저 ${wt.weather_constraints.min_temp}°C`}
                        {wt.weather_constraints.max_wind != null && ` 최대 ${wt.weather_constraints.max_wind}m/s`}
                        {wt.weather_constraints.no_rain ? " 우천불가" : ""}
                      </span>
                    ) : "-"}
                  </td>
                  <td>{wt.is_system ? <span className="badge badge-blue">기본</span> : <span className="badge badge-gray">사용자</span>}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ExportImportTab() {
  const [importing, setImporting] = useState(false);
  const [importText, setImportText] = useState("");
  const [importResult, setImportResult] = useState<string | null>(null);

  async function handleExport() {
    const resp = await api.get("/settings/export");
    const blob = new Blob([JSON.stringify(resp.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `conai-settings-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleImport(e: React.FormEvent) {
    e.preventDefault();
    setImporting(true);
    try {
      const data = JSON.parse(importText);
      const resp = await api.post("/settings/import", data);
      setImportResult(`가져오기 완료: 발주처 ${resp.data.imported.client_profiles}개, 공종 ${resp.data.imported.work_types}개`);
      setImportText("");
    } catch {
      setImportResult("오류: JSON 형식을 확인해주세요");
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <h3 className="mb-2">설정 내보내기</h3>
        <p className="text-sm text-gray-500 mb-4">현재 설정(발주처, 공종, 알림규칙)을 JSON 파일로 내보냅니다</p>
        <button className="btn-primary" onClick={handleExport}>📥 설정 다운로드</button>
      </div>

      <div className="card p-5">
        <h3 className="mb-2">설정 가져오기</h3>
        <p className="text-sm text-gray-500 mb-4">다른 현장에서 내보낸 설정 JSON을 붙여넣으세요</p>
        <form onSubmit={handleImport} className="space-y-3">
          <textarea
            className="input min-h-[120px] font-mono text-xs"
            value={importText}
            onChange={(e) => setImportText(e.target.value)}
            placeholder={`{"version": "1.0", "client_profiles": [...], ...}`}
          />
          {importResult && (
            <p className={`text-sm px-3 py-2 rounded ${importResult.startsWith("오류") ? "bg-red-50 text-red-600" : "bg-green-50 text-green-600"}`}>
              {importResult}
            </p>
          )}
          <button type="submit" className="btn-primary" disabled={importing || !importText.trim()}>
            {importing ? "가져오는 중..." : "📤 설정 가져오기"}
          </button>
        </form>
      </div>
    </div>
  );
}
