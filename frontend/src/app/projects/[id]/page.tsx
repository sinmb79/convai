"use client";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { Project } from "@/lib/types";
import { formatDate, formatCurrency, PROJECT_STATUS_LABELS, CONSTRUCTION_TYPE_LABELS } from "@/lib/utils";
import Link from "next/link";

const TABS = [
  { id: "gantt", label: "📅 공정표", href: (id: string) => `/projects/${id}/gantt` },
  { id: "reports", label: "📋 일보/보고서", href: (id: string) => `/projects/${id}/reports` },
  { id: "inspections", label: "🔬 검측", href: (id: string) => `/projects/${id}/inspections` },
  { id: "quality", label: "✅ 품질시험", href: (id: string) => `/projects/${id}/quality` },
  { id: "weather", label: "🌤 날씨", href: (id: string) => `/projects/${id}/weather` },
  { id: "permits", label: "🏛 인허가", href: (id: string) => `/projects/${id}/permits` },
  { id: "agents", label: "🤖 AI 에이전트", href: (id: string) => `/projects/${id}/agents` },
  { id: "evms", label: "📊 EVMS", href: (id: string) => `/projects/${id}/evms` },
  { id: "vision", label: "👁 Vision AI", href: (id: string) => `/projects/${id}/vision` },
  { id: "completion", label: "📦 준공도서", href: (id: string) => `/projects/${id}/completion` },
];

export default function ProjectDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: ["project", id],
    queryFn: () => api.get(`/projects/${id}`).then((r) => r.data),
  });

  if (isLoading) return <AppLayout><div className="text-gray-400">로딩 중...</div></AppLayout>;
  if (!project) return <AppLayout><div className="text-red-500">현장을 찾을 수 없습니다</div></AppLayout>;

  const statusColors: Record<string, string> = {
    active: "badge-green", planning: "badge-blue",
    suspended: "badge-yellow", completed: "badge-gray",
  };

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="card p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Link href="/projects" className="text-gray-400 hover:text-gray-600 text-sm">← 목록</Link>
                <span className={`badge ${statusColors[project.status]}`}>{PROJECT_STATUS_LABELS[project.status]}</span>
              </div>
              <h1 className="text-xl font-bold">{project.name}</h1>
              <p className="text-gray-500 text-sm mt-0.5">
                {project.code} · {CONSTRUCTION_TYPE_LABELS[project.construction_type]}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-100">
            <InfoItem label="착공일" value={formatDate(project.start_date)} />
            <InfoItem label="준공예정일" value={formatDate(project.end_date)} />
            <InfoItem label="계약금액" value={formatCurrency(project.contract_amount)} />
            <InfoItem label="공사위치" value={project.location_address || "-"} />
          </div>
        </div>

        {/* Module Tabs */}
        <div className="grid grid-cols-4 gap-3">
          {TABS.map((tab) => (
            <Link
              key={tab.id}
              href={tab.href(id)}
              className="card p-4 hover:shadow-md transition-shadow flex items-center gap-3"
            >
              <span className="text-2xl">{tab.label.split(" ")[0]}</span>
              <span className="font-medium text-sm">{tab.label.split(" ").slice(1).join(" ")}</span>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="font-medium text-sm mt-0.5">{value}</p>
    </div>
  );
}
