"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { WeatherForecastSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

const WEATHER_CODE_ICONS: Record<string, string> = {
  "1": "☀️", "2": "🌤", "3": "⛅", "4": "☁️",
  "5": "🌧", "6": "🌨", "7": "🌨", "8": "❄️",
};

export default function WeatherPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery<WeatherForecastSummary>({
    queryKey: ["weather", id],
    queryFn: () => api.get(`/projects/${id}/weather`).then((r) => r.data),
  });

  const refreshMutation = useMutation({
    mutationFn: () => api.post(`/projects/${id}/weather/refresh`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["weather", id] }),
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) => api.put(`/projects/${id}/weather/alerts/${alertId}/acknowledge`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["weather", id] }),
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            <h1 className="mt-1">날씨 연동 공정 경보</h1>
          </div>
          <button
            className="btn-secondary"
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            {refreshMutation.isPending ? "새로고침 중..." : "🔄 날씨 새로고침"}
          </button>
        </div>

        {/* Active Alerts */}
        {data?.active_alerts && data.active_alerts.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-red-600">⚠️ 활성 경보 ({data.active_alerts.length}건)</h3>
            {data.active_alerts.map((alert) => (
              <div
                key={alert.id}
                className={`card p-4 border-l-4 ${alert.severity === "critical" ? "border-red-500 bg-red-50" : "border-yellow-500 bg-yellow-50"}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-sm">
                      {alert.severity === "critical" ? "🚨" : "⚠️"} {formatDate(alert.alert_date)}
                    </p>
                    <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                  </div>
                  <button
                    className="btn-secondary text-xs"
                    onClick={() => acknowledgeMutation.mutate(alert.id)}
                  >
                    확인
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Forecast */}
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">날씨 예보</h3>
          </div>
          <div className="card-body">
            {isLoading ? (
              <p className="text-gray-400 text-center py-4">로딩 중...</p>
            ) : !data?.forecast || data.forecast.length === 0 ? (
              <p className="text-gray-400 text-center py-4">날씨 데이터가 없습니다. 새로고침 버튼을 눌러주세요.</p>
            ) : (
              <div className="grid grid-cols-4 gap-3">
                {data.forecast.map((f) => (
                  <div key={f.id} className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-500 mb-1">{formatDate(f.forecast_date)}</p>
                    <p className="text-2xl my-1">{WEATHER_CODE_ICONS[f.weather_code || "1"] || "🌤"}</p>
                    <p className="font-semibold text-sm">
                      {f.temperature_high != null ? `${f.temperature_high}°` : "-"}
                      <span className="text-gray-400"> / </span>
                      {f.temperature_low != null ? `${f.temperature_low}°` : "-"}
                    </p>
                    {f.precipitation_mm != null && f.precipitation_mm > 0 && (
                      <p className="text-xs text-blue-500 mt-0.5">💧 {f.precipitation_mm}mm</p>
                    )}
                    {f.wind_speed_ms != null && (
                      <p className="text-xs text-gray-400 mt-0.5">💨 {f.wind_speed_ms}m/s</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
