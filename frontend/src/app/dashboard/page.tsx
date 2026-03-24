"use client";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { Project, WeatherAlert } from "@/lib/types";
import { formatDate, formatCurrency, PROJECT_STATUS_LABELS } from "@/lib/utils";
import Link from "next/link";

export default function DashboardPage() {
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: () => api.get("/projects").then((r) => r.data),
  });

  const activeProjects = projects.filter((p) => p.status === "active");
  const planningProjects = projects.filter((p) => p.status === "planning");

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
          <p className="text-gray-500 text-sm mt-1">현장 현황을 한눈에 확인하세요</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="전체 현장" value={projects.length} icon="🏗" color="blue" />
          <StatCard label="진행중" value={activeProjects.length} icon="🔄" color="green" />
          <StatCard label="계획중" value={planningProjects.length} icon="📋" color="yellow" />
          <StatCard label="완료" value={projects.filter((p) => p.status === "completed").length} icon="✅" color="gray" />
        </div>

        {/* Active Projects */}
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold">진행중인 현장</h2>
            <Link href="/projects" className="btn-secondary text-xs">
              전체 보기
            </Link>
          </div>
          <div className="card-body p-0">
            {activeProjects.length === 0 ? (
              <div className="p-6 text-center text-gray-400 text-sm">
                진행중인 현장이 없습니다.{" "}
                <Link href="/projects" className="text-brand-500 hover:underline">
                  새 현장 등록
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {activeProjects.map((p) => (
                  <Link
                    key={p.id}
                    href={`/projects/${p.id}`}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition-colors"
                  >
                    <div>
                      <p className="font-medium text-gray-900">{p.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {p.code} · {formatDate(p.start_date)} ~ {formatDate(p.end_date)}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="badge badge-green">{PROJECT_STATUS_LABELS[p.status]}</span>
                      <p className="text-xs text-gray-400 mt-1">{formatCurrency(p.contract_amount)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-3 gap-4">
          <QuickAction href="/rag" icon="📚" title="법규 Q&A" desc="KCS·법령 즉시 검색" />
          <QuickAction href="/projects" icon="➕" title="현장 등록" desc="새 공사 현장 추가" />
          <QuickAction href="/settings" icon="⚙️" title="설정" desc="발주처·공종 관리" />
        </div>
      </div>
    </AppLayout>
  );
}

function StatCard({
  label, value, icon, color,
}: {
  label: string; value: number; icon: string; color: "blue" | "green" | "yellow" | "gray";
}) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    yellow: "bg-yellow-50 text-yellow-600",
    gray: "bg-gray-50 text-gray-600",
  };
  return (
    <div className="card p-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg mb-3 ${colors[color]}`}>
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

function QuickAction({
  href, icon, title, desc,
}: {
  href: string; icon: string; title: string; desc: string;
}) {
  return (
    <Link href={href} className="card p-4 hover:shadow-md transition-shadow flex items-start gap-3">
      <span className="text-2xl">{icon}</span>
      <div>
        <p className="font-semibold text-gray-900 text-sm">{title}</p>
        <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
      </div>
    </Link>
  );
}
