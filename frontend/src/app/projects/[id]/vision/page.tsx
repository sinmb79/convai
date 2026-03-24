"use client";
import { useState, useRef } from "react";
import { useParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { AppLayout } from "@/components/layout/AppLayout";
import api from "@/lib/api";
import type { VisionClassifyResult, VisionSafetyResult, VisionDrawingResult } from "@/lib/types";

type TabId = "classify" | "safety" | "drawing";

const TABS: { id: TabId; label: string; desc: string }[] = [
  { id: "classify", label: "📸 공종 분류", desc: "사진에서 공종 자동 태깅" },
  { id: "safety", label: "⛑ 안전 점검", desc: "안전모·조끼 착용 감지" },
  { id: "drawing", label: "📐 도면 대조", desc: "설계도면 vs 현장사진 비교" },
];

function ImageUploadBox({
  label,
  onChange,
  preview,
}: {
  label: string;
  onChange: (file: File) => void;
  preview: string | null;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <div
      className="border-2 border-dashed border-gray-200 rounded-xl p-4 text-center cursor-pointer hover:border-blue-300 transition-colors"
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && onChange(e.target.files[0])}
      />
      {preview ? (
        <img src={preview} alt="preview" className="max-h-40 mx-auto rounded-lg object-contain" />
      ) : (
        <div className="text-gray-400 py-6">
          <p className="text-2xl mb-1">📁</p>
          <p className="text-sm">{label}</p>
        </div>
      )}
    </div>
  );
}

function RiskBadge({ level }: { level: string }) {
  const map: Record<string, string> = {
    high: "bg-red-100 text-red-700",
    medium: "bg-yellow-100 text-yellow-700",
    low: "bg-green-100 text-green-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${map[level] ?? "bg-gray-100 text-gray-600"}`}>
      {level === "high" ? "🔴 고위험" : level === "medium" ? "🟡 주의" : "🟢 양호"}
    </span>
  );
}

export default function VisionPage() {
  const params = useParams();
  const projectId = params.id as string;

  const [tab, setTab] = useState<TabId>("classify");
  const [classifyFile, setClassifyFile] = useState<File | null>(null);
  const [classifyPreview, setClassifyPreview] = useState<string | null>(null);
  const [safetyFile, setSafetyFile] = useState<File | null>(null);
  const [safetyPreview, setSafetyPreview] = useState<string | null>(null);
  const [drawingFile, setDrawingFile] = useState<File | null>(null);
  const [drawingPreview, setDrawingPreview] = useState<string | null>(null);
  const [fieldFile, setFieldFile] = useState<File | null>(null);
  const [fieldPreview, setFieldPreview] = useState<string | null>(null);

  const handleFileChange = (
    file: File,
    setFile: (f: File) => void,
    setPreview: (s: string) => void
  ) => {
    setFile(file);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const classifyMutation = useMutation<VisionClassifyResult>({
    mutationFn: () => {
      const form = new FormData();
      form.append("file", classifyFile!);
      return api.post(`/projects/${projectId}/vision/classify`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then((r) => r.data);
    },
  });

  const safetyMutation = useMutation<VisionSafetyResult>({
    mutationFn: () => {
      const form = new FormData();
      form.append("file", safetyFile!);
      return api.post(`/projects/${projectId}/vision/safety-check`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then((r) => r.data);
    },
  });

  const drawingMutation = useMutation<VisionDrawingResult>({
    mutationFn: () => {
      const form = new FormData();
      form.append("drawing", drawingFile!);
      form.append("field_photo", fieldFile!);
      return api.post(`/projects/${projectId}/vision/compare-drawing`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      }).then((r) => r.data);
    },
  });

  return (
    <AppLayout>
      <div className="space-y-6">
        <h1 className="text-xl font-bold">Vision AI 사진 분석</h1>

        {/* Tabs */}
        <div className="flex gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                tab === t.id ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab: Classify */}
        {tab === "classify" && (
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <ImageUploadBox
                label="현장 사진을 업로드하세요"
                onChange={(f) => handleFileChange(f, setClassifyFile, setClassifyPreview)}
                preview={classifyPreview}
              />
              <button
                className="btn-primary w-full"
                onClick={() => classifyMutation.mutate()}
                disabled={!classifyFile || classifyMutation.isPending}
              >
                {classifyMutation.isPending ? "분석 중..." : "🔍 공종 분류 실행"}
              </button>
            </div>

            <div>
              {classifyMutation.data && (
                <div className="card p-4 space-y-3">
                  <h3 className="font-semibold">분류 결과</h3>
                  <div>
                    <p className="text-xs text-gray-400">공종</p>
                    <p className="text-lg font-bold text-blue-600">{classifyMutation.data.work_type}</p>
                    <p className="text-xs text-gray-500">신뢰도: {classifyMutation.data.confidence}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">태그</p>
                    <div className="flex flex-wrap gap-1">
                      {classifyMutation.data.tags.map((tag) => (
                        <span key={tag} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">설명</p>
                    <p className="text-sm text-gray-700">{classifyMutation.data.description}</p>
                  </div>
                </div>
              )}
              {!classifyMutation.data && !classifyMutation.isPending && (
                <div className="card p-8 text-center text-gray-400 text-sm">
                  사진을 업로드하고 분석을 실행하세요
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Safety */}
        {tab === "safety" && (
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <ImageUploadBox
                label="근로자 사진을 업로드하세요"
                onChange={(f) => handleFileChange(f, setSafetyFile, setSafetyPreview)}
                preview={safetyPreview}
              />
              <button
                className="btn-primary w-full"
                onClick={() => safetyMutation.mutate()}
                disabled={!safetyFile || safetyMutation.isPending}
              >
                {safetyMutation.isPending ? "분석 중..." : "⛑ 안전 점검 실행"}
              </button>
            </div>

            <div>
              {safetyMutation.data && (
                <div className="card p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">안전 점검 결과</h3>
                    <RiskBadge level={safetyMutation.data.risk_level} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className={`p-3 rounded-lg text-center ${safetyMutation.data.helmet ? "bg-green-50" : "bg-red-50"}`}>
                      <p className="text-2xl">{safetyMutation.data.helmet ? "✅" : "❌"}</p>
                      <p className="text-sm font-medium mt-1">안전모</p>
                    </div>
                    <div className={`p-3 rounded-lg text-center ${safetyMutation.data.vest ? "bg-green-50" : "bg-red-50"}`}>
                      <p className="text-2xl">{safetyMutation.data.vest ? "✅" : "❌"}</p>
                      <p className="text-sm font-medium mt-1">안전조끼</p>
                    </div>
                  </div>
                  {safetyMutation.data.violations.length > 0 && (
                    <div>
                      <p className="text-xs text-red-500 font-semibold mb-1">위반 사항</p>
                      <ul className="text-sm text-gray-700 space-y-0.5">
                        {safetyMutation.data.violations.map((v, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span className="text-red-400">•</span> {v}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-400 mb-1">조치 권고</p>
                    <p className="text-sm text-gray-700">{safetyMutation.data.recommendation}</p>
                  </div>
                </div>
              )}
              {!safetyMutation.data && !safetyMutation.isPending && (
                <div className="card p-8 text-center text-gray-400 text-sm">
                  근로자 사진을 업로드하고 점검을 실행하세요
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab: Drawing Comparison */}
        {tab === "drawing" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">설계 도면</p>
                <ImageUploadBox
                  label="설계 도면 이미지"
                  onChange={(f) => handleFileChange(f, setDrawingFile, setDrawingPreview)}
                  preview={drawingPreview}
                />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-600">현장 사진</p>
                <ImageUploadBox
                  label="현장 시공 사진"
                  onChange={(f) => handleFileChange(f, setFieldFile, setFieldPreview)}
                  preview={fieldPreview}
                />
              </div>
            </div>

            <button
              className="btn-primary w-full"
              onClick={() => drawingMutation.mutate()}
              disabled={!drawingFile || !fieldFile || drawingMutation.isPending}
            >
              {drawingMutation.isPending ? "비교 분석 중..." : "📐 도면 대조 실행"}
            </button>

            {drawingMutation.data && (
              <div className="card p-4 space-y-4">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold">대조 결과</h3>
                  <span className="text-sm font-bold text-blue-600">{drawingMutation.data.overall_match}</span>
                </div>

                {drawingMutation.data.matches.length > 0 && (
                  <div>
                    <p className="text-xs text-green-600 font-semibold mb-1">✅ 일치 항목</p>
                    <ul className="text-sm text-gray-700 space-y-0.5">
                      {drawingMutation.data.matches.map((m, i) => (
                        <li key={i} className="flex items-start gap-1">
                          <span className="text-green-400">•</span> {m}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {drawingMutation.data.discrepancies.length > 0 && (
                  <div>
                    <p className="text-xs text-red-500 font-semibold mb-1">⚠️ 불일치 항목</p>
                    <ul className="text-sm text-gray-700 space-y-0.5">
                      {drawingMutation.data.discrepancies.map((d, i) => (
                        <li key={i} className="flex items-start gap-1">
                          <span className="text-red-400">•</span> {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <p className="text-xs text-gray-400 mb-1">권고 사항</p>
                  <p className="text-sm text-gray-700">{drawingMutation.data.recommendation}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
