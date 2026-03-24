"use client";
import { useState } from "react";
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardData {
  project: { name: string; start_date: string | null; end_date: string | null; status: string };
  progress: { planned: number | null; actual: number | null; spi: number | null; snapshot_date: string | null };
  quality: { total_tests: number; pass_rate: number | null };
  recent_reports: Array<{ date: string; weather: string; work: string }>;
  active_alerts: Array<{ type: string; message: string }>;
  generated_at: string;
}

function StatBox({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-xl font-bold text-gray-800">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function ProgressBar({ planned, actual }: { planned: number | null; actual: number | null }) {
  const p = planned ?? 0;
  const a = actual ?? 0;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-sm">
        <span className="w-12 text-gray-500">계획</span>
        <div className="flex-1 bg-gray-100 rounded-full h-4">
          <div className="bg-blue-400 h-4 rounded-full" style={{ width: `${Math.min(p, 100)}%` }} />
        </div>
        <span className="w-12 text-right font-medium">{p.toFixed(1)}%</span>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <span className="w-12 text-gray-500">실적</span>
        <div className="flex-1 bg-gray-100 rounded-full h-4">
          <div
            className={`h-4 rounded-full ${a >= p ? "bg-green-400" : "bg-red-400"}`}
            style={{ width: `${Math.min(a, 100)}%` }}
          />
        </div>
        <span className="w-12 text-right font-medium">{a.toFixed(1)}%</span>
      </div>
    </div>
  );
}

export default function PortalPage() {
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);

  const handleLogin = async () => {
    if (!token.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_URL}/api/v1/portal/dashboard`, {
        headers: { Authorization: `Bearer ${token.trim()}` },
      });
      setData(res.data);
    } catch {
      setError("유효하지 않은 토큰이거나 만료되었습니다.");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const statusLabels: Record<string, string> = {
    active: "공사 중", planning: "착공 준비", suspended: "공사 중단", completed: "준공 완료",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
        <div>
          <span className="text-xl font-bold">CONAI</span>
          <span className="ml-3 text-sm text-gray-400">발주처 공사 현황 포털</span>
        </div>
        <span className="text-xs text-gray-500">읽기 전용 · 실시간 현황</span>
      </header>

      <main className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Token Input */}
        {!data && (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 space-y-4">
            <div className="text-center mb-2">
              <p className="text-2xl mb-1">🏗</p>
              <h1 className="text-xl font-bold text-gray-800">발주처 포털</h1>
              <p className="text-sm text-gray-500 mt-1">현장 관리자로부터 받은 접근 토큰을 입력하세요</p>
            </div>
            <input
              className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="포털 접근 토큰 입력..."
              value={token}
              onChange={(e) => setToken(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              onClick={handleLogin}
              disabled={loading || !token.trim()}
              className="w-full bg-blue-500 text-white py-3 rounded-lg font-medium hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {loading ? "확인 중..." : "현황 확인"}
            </button>
          </div>
        )}

        {/* Dashboard */}
        {data && (
          <>
            {/* Project header */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">{data.project.name}</h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {data.project.start_date} ~ {data.project.end_date ?? "미정"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                    {statusLabels[data.project.status] ?? data.project.status}
                  </span>
                  <button
                    onClick={() => setData(null)}
                    className="text-xs text-gray-400 hover:text-gray-600"
                  >
                    로그아웃
                  </button>
                </div>
              </div>
            </div>

            {/* Active alerts */}
            {data.active_alerts.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-2">
                <p className="text-sm font-semibold text-red-700">🚨 기상 경보</p>
                {data.active_alerts.map((a, i) => (
                  <p key={i} className="text-sm text-red-600">{a.type}: {a.message}</p>
                ))}
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <StatBox
                label="SPI (공정 성과 지수)"
                value={data.progress.spi != null ? data.progress.spi.toFixed(2) : "-"}
                sub={data.progress.spi != null
                  ? data.progress.spi >= 1 ? "✅ 정상" : "⚠️ 지연"
                  : undefined}
              />
              <StatBox
                label="품질시험 합격률"
                value={data.quality.pass_rate != null ? `${data.quality.pass_rate}%` : "-"}
                sub={`총 ${data.quality.total_tests}건`}
              />
              <StatBox
                label="기준일"
                value={data.progress.snapshot_date ?? "-"}
                sub="EVMS 스냅샷"
              />
            </div>

            {/* Progress */}
            <div className="bg-white rounded-2xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-600 mb-4">공정률 현황</h3>
              <ProgressBar planned={data.progress.planned} actual={data.progress.actual} />
            </div>

            {/* Recent reports */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 bg-gray-50 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-600">최근 작업일보</h3>
              </div>
              {data.recent_reports.length === 0 ? (
                <p className="text-sm text-gray-400 p-5">작업일보가 없습니다</p>
              ) : (
                <div className="divide-y divide-gray-50">
                  {data.recent_reports.map((r, i) => (
                    <div key={i} className="px-5 py-4">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-sm font-medium text-gray-700">{r.date}</span>
                        <span className="text-xs text-gray-400">{r.weather}</span>
                      </div>
                      <p className="text-sm text-gray-600">{r.work || "-"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <p className="text-xs text-gray-400 text-right">생성: {data.generated_at.slice(0, 19).replace("T", " ")}</p>
          </>
        )}
      </main>
    </div>
  );
}
