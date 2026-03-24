import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

export function formatCurrency(amount: number | undefined): string {
  if (!amount) return "-";
  return new Intl.NumberFormat("ko-KR", { style: "currency", currency: "KRW" }).format(amount);
}

export function formatProgress(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

export const PROJECT_STATUS_LABELS: Record<string, string> = {
  planning: "계획",
  active: "진행중",
  suspended: "중단",
  completed: "완료",
};

export const CONSTRUCTION_TYPE_LABELS: Record<string, string> = {
  road: "도로공사",
  sewer: "하수도공사",
  water: "상수도공사",
  bridge: "교량공사",
  site_work: "부지조성",
  other: "기타",
};

export const PERMIT_STATUS_LABELS: Record<string, string> = {
  not_started: "미착수",
  submitted: "제출완료",
  in_review: "검토중",
  approved: "승인",
  rejected: "반려",
};

export const PERMIT_STATUS_COLORS: Record<string, string> = {
  not_started: "bg-gray-100 text-gray-700",
  submitted: "bg-blue-100 text-blue-700",
  in_review: "bg-yellow-100 text-yellow-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export const DAILY_REPORT_STATUS_LABELS: Record<string, string> = {
  draft: "초안",
  confirmed: "확인완료",
  submitted: "제출완료",
};
