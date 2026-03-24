"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { GanttData, Task } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { useState } from "react";
import Link from "next/link";

export default function GanttPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const { data: gantt, isLoading } = useQuery<GanttData>({
    queryKey: ["gantt", id],
    queryFn: () => api.get(`/projects/${id}/tasks/gantt`).then((r) => r.data),
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post(`/projects/${id}/tasks`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["gantt", id] }); setShowCreateForm(false); },
  });

  const updateProgressMutation = useMutation({
    mutationFn: ({ taskId, progress }: { taskId: string; progress: number }) =>
      api.put(`/projects/${id}/tasks/${taskId}`, { progress_pct: progress }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["gantt", id] }),
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 text-sm">← 현장</Link>
            <h1 className="mt-1">공정표 (Gantt)</h1>
            {gantt?.project_duration_days && (
              <p className="text-sm text-gray-500 mt-0.5">총 공기: {gantt.project_duration_days}일 | 주공정선: {gantt.critical_path.length}개 태스크</p>
            )}
          </div>
          <button className="btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
            ➕ 태스크 추가
          </button>
        </div>

        {showCreateForm && (
          <div className="card p-5">
            <h3 className="mb-4">새 태스크</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.target as HTMLFormElement);
                createTaskMutation.mutate({
                  name: fd.get("name"),
                  planned_start: fd.get("planned_start") || undefined,
                  planned_end: fd.get("planned_end") || undefined,
                });
              }}
              className="grid grid-cols-3 gap-4"
            >
              <div className="col-span-3 md:col-span-1">
                <label className="label">태스크명 *</label>
                <input name="name" className="input" required placeholder="콘크리트 타설" />
              </div>
              <div>
                <label className="label">계획 시작일</label>
                <input name="planned_start" className="input" type="date" />
              </div>
              <div>
                <label className="label">계획 완료일</label>
                <input name="planned_end" className="input" type="date" />
              </div>
              <div className="col-span-3 flex gap-2 justify-end">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateForm(false)}>취소</button>
                <button type="submit" className="btn-primary" disabled={createTaskMutation.isPending}>추가</button>
              </div>
            </form>
          </div>
        )}

        {/* Task List with Gantt-like bars */}
        <div className="card">
          <div className="card-header">
            <span className="font-semibold">태스크 목록</span>
            <span className="text-gray-400 text-sm">{gantt?.tasks.length || 0}개 태스크</span>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>태스크명</th>
                  <th>계획 시작</th>
                  <th>계획 완료</th>
                  <th>진행률</th>
                  <th>주공정선</th>
                  <th>여유일수</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={6} className="text-center py-8 text-gray-400">CPM 계산 중...</td></tr>
                ) : !gantt?.tasks.length ? (
                  <tr><td colSpan={6} className="text-center py-8 text-gray-400">태스크가 없습니다</td></tr>
                ) : (
                  gantt.tasks.map((task) => (
                    <tr key={task.id} className={task.is_critical ? "bg-red-50" : ""}>
                      <td className="font-medium">
                        {task.is_critical && <span className="text-red-500 mr-1">●</span>}
                        {task.name}
                      </td>
                      <td>{formatDate(task.planned_start)}</td>
                      <td>{formatDate(task.planned_end)}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-1.5 min-w-[60px]">
                            <div
                              className={`h-1.5 rounded-full ${task.progress_pct >= 100 ? "bg-green-500" : "bg-brand-500"}`}
                              style={{ width: `${task.progress_pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 w-8">{task.progress_pct}%</span>
                        </div>
                      </td>
                      <td>
                        {task.is_critical ? (
                          <span className="badge badge-red">주공정</span>
                        ) : (
                          <span className="badge badge-gray">여유</span>
                        )}
                      </td>
                      <td>{task.total_float != null ? `${task.total_float}일` : "-"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-400 inline-block"></span> 주공정선 (Critical Path)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-gray-300 inline-block"></span> 여유 공정</span>
        </div>
      </div>
    </AppLayout>
  );
}
