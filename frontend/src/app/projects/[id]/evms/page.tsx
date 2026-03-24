"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { EVMSSnapshot, EVMSChart } from "@/lib/types";

function StatCard({ label, value, sub, color = "text-gray-800" }: {
  label: string; value: string | number; sub?: string; color?: string;
}) {
  return (
    <div className="card p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function IndexBadge({ label, value }: { label: string; value: number | null }) {
  if (value == null) return <span className="text-gray-400 text-sm">-</span>;
  const color = value >= 1 ? "text-green-600" : value >= 0.9 ? "text-yellow-600" : "text-red-600";
  const bg = value >= 1 ? "bg-green-50" : value >= 0.9 ? "bg-yellow-50" : "bg-red-50";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${color} ${bg}`}>
      {label} {value.toFixed(2)}
      {value >= 1 ? " ✅" : value >= 0.9 ? " ⚠️" : " 🔴"}
    </span>
  );
}

function MiniBar({ planned, actual }: { planned: number; actual: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2 text-xs">
        <span className="w-10 text-gray-500">계획</span>
        <div className="flex-1 bg-gray-100 rounded-full h-3">
          <div className="bg-blue-400 h-3 rounded-full" style={{ width: `${Math.min(planned, 100)}%` }} />
        </div>
        <span className="w-10 text-right text-gray-600">{planned.toFixed(1)}%</span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className="w-10 text-gray-500">실적</span>
        <div className="flex-1 bg-gray-100 rounded-full h-3">
          <div
            className={`h-3 rounded-full ${actual >= planned ? "bg-green-400" : "bg-red-400"}`}
            style={{ width: `${Math.min(actual, 100)}%` }}
          />
        </div>
        <span className="w-10 text-right text-gray-600">{actual.toFixed(1)}%</span>
      </div>
    </div>
  );
}

export default function EvmsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const qc = useQueryClient();

  const { data: latest, isLoading } = useQuery<EVMSSnapshot>({
    queryKey: ["evms-latest", projectId],
    queryFn: () => api.get(`/projects/${projectId}/evms/latest`).then((r) => r.data),
  });

  const { data: chart } = useQuery<EVMSChart>({
    queryKey: ["evms-chart", projectId],
    queryFn: async () => {
      const r = await api.get(`/portal/progress-chart`, {
        headers: { Authorization: `Bearer __internal__` },
      });
      return r.data;
    },
    retry: false,
  });

  const { data: forecast } = useQuery<{ forecast_days: number; message: string; predicted_end?: string }>({
    queryKey: ["evms-forecast", projectId],
    queryFn: () => api.get(`/projects/${projectId}/evms/delay-forecast`).then((r) => r.data),
    retry: false,
  });

  const { data: claim } = useQuery<{ milestone: string; pct: number; estimated_amount: number; note: string }>({
    queryKey: ["evms-claim", projectId],
    queryFn: () => api.get(`/projects/${projectId}/evms/progress-claim`).then((r) => r.data),
    retry: false,
  });

  const computeMutation = useMutation({
    mutationFn: () => api.post(`/projects/${projectId}/evms/compute`, { save_snapshot: true }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evms-latest", projectId] }),
  });

  const fmt = (n: number | undefined) =>
    n != null ? `${(n / 1e6).toFixed(1)}백만원` : "-";

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold">EVMS 공정/원가 관리</h1>
          <button
            onClick={() => computeMutation.mutate()}
            disabled={computeMutation.isPending}
            className="btn-primary text-sm"
          >
            {computeMutation.isPending ? "계산 중..." : "📊 EVMS 재계산"}
          </button>
        </div>

        {isLoading && <p className="text-gray-400">로딩 중...</p>}

        {!isLoading && !latest && (
          <div className="card p-8 text-center text-gray-400">
            <p className="text-lg mb-2">EVMS 데이터가 없습니다</p>
            <p className="text-sm">EVMS 재계산 버튼을 눌러 스냅샷을 생성하세요.</p>
          </div>
        )}

        {latest && (
          <>
            {/* Index badges */}
            <div className="flex items-center gap-3 flex-wrap">
              <IndexBadge label="SPI" value={latest.spi} />
              <IndexBadge label="CPI" value={latest.cpi} />
              <span className="text-xs text-gray-400">기준일: {latest.snapshot_date}</span>
            </div>

            {/* Progress bars */}
            <div className="card p-4">
              <h2 className="text-sm font-semibold text-gray-600 mb-3">공정률</h2>
              <MiniBar planned={latest.planned_progress} actual={latest.actual_progress} />
            </div>

            {/* EVM stats */}
            <div className="grid grid-cols-3 gap-3">
              <StatCard label="PV (계획가치)" value={fmt(latest.pv)} sub="Planned Value" />
              <StatCard label="EV (획득가치)" value={fmt(latest.ev)} sub="Earned Value" />
              <StatCard
                label="AC (실제원가)"
                value={fmt(latest.ac)}
                sub="Actual Cost"
                color={latest.ac > latest.ev ? "text-red-600" : "text-green-600"}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <StatCard
                label="EAC (완료시점 예산)"
                value={fmt(latest.eac)}
                sub="Estimate at Completion"
                color="text-purple-600"
              />
              <StatCard
                label="ETC (잔여 예산)"
                value={fmt(latest.etc)}
                sub="Estimate to Complete"
              />
            </div>

            {/* Chart (simple ASCII-style bar) */}
            {chart && chart.labels.length > 0 && (
              <div className="card p-4">
                <h2 className="text-sm font-semibold text-gray-600 mb-3">공정률 추이 (최근 {chart.labels.length}일)</h2>
                <div className="overflow-x-auto">
                  <div className="flex items-end gap-1 h-24 min-w-max">
                    {chart.labels.map((label, i) => (
                      <div key={label} className="flex flex-col items-center gap-0.5 w-5">
                        <div className="relative flex gap-0.5 items-end h-20">
                          <div
                            className="w-2 bg-blue-300 rounded-t"
                            style={{ height: `${(chart.planned[i] ?? 0) * 0.8}%` }}
                          />
                          <div
                            className={`w-2 rounded-t ${(chart.actual[i] ?? 0) >= (chart.planned[i] ?? 0) ? "bg-green-400" : "bg-red-400"}`}
                            style={{ height: `${(chart.actual[i] ?? 0) * 0.8}%` }}
                          />
                        </div>
                        <span className="text-[9px] text-gray-400 rotate-45 w-8 text-left ml-1">
                          {label.slice(5)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-300 inline-block rounded" /> 계획</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-400 inline-block rounded" /> 실적</span>
                  </div>
                </div>
              </div>
            )}

            {/* Forecast + Claim */}
            <div className="grid grid-cols-2 gap-4">
              {forecast && (
                <div className="card p-4">
                  <h2 className="text-sm font-semibold mb-2">📅 공기 예측</h2>
                  <p className="text-sm text-gray-700">{forecast.message}</p>
                  {forecast.predicted_end && (
                    <p className="text-xs text-gray-500 mt-1">예상 준공일: {forecast.predicted_end}</p>
                  )}
                </div>
              )}
              {claim && (
                <div className="card p-4">
                  <h2 className="text-sm font-semibold mb-2">💰 기성 청구 예측</h2>
                  <p className="text-sm text-gray-700">{claim.milestone}</p>
                  <p className="text-base font-bold text-purple-600 mt-1">
                    {(claim.estimated_amount / 1e6).toFixed(1)}백만원 ({claim.pct}%)
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{claim.note}</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
