// Core types matching backend Pydantic schemas

export type UserRole = "admin" | "site_manager" | "supervisor" | "worker";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  phone?: string;
  kakao_user_key?: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type ProjectStatus = "planning" | "active" | "suspended" | "completed";
export type ConstructionType = "road" | "sewer" | "water" | "bridge" | "site_work" | "other";

export interface Project {
  id: string;
  name: string;
  code: string;
  client_profile_id?: string;
  construction_type: ConstructionType;
  contract_amount?: number;
  start_date?: string;
  end_date?: string;
  location_address?: string;
  location_lat?: number;
  location_lng?: number;
  status: ProjectStatus;
  owner_id: string;
  created_at: string;
}

export interface WBSItem {
  id: string;
  project_id: string;
  parent_id?: string;
  code: string;
  name: string;
  level: number;
  unit?: string;
  design_qty?: number;
  unit_price?: number;
  sort_order: number;
  children: WBSItem[];
}

export interface Task {
  id: string;
  project_id: string;
  wbs_item_id?: string;
  name: string;
  planned_start?: string;
  planned_end?: string;
  actual_start?: string;
  actual_end?: string;
  progress_pct: number;
  is_milestone: boolean;
  is_critical: boolean;
  early_start?: string;
  early_finish?: string;
  late_start?: string;
  late_finish?: string;
  total_float?: number;
  sort_order: number;
  created_at: string;
}

export interface GanttData {
  tasks: Task[];
  critical_path: string[];
  project_duration_days?: number;
}

export type DailyReportStatus = "draft" | "confirmed" | "submitted";
export type InputSource = "kakao" | "web" | "api";

export interface DailyReport {
  id: string;
  project_id: string;
  report_date: string;
  weather_summary?: string;
  temperature_high?: number;
  temperature_low?: number;
  workers_count?: Record<string, number>;
  equipment_list?: Array<{ type: string; count: number; hours?: number }>;
  work_content?: string;
  issues?: string;
  input_source: InputSource;
  ai_generated: boolean;
  status: DailyReportStatus;
  confirmed_by?: string;
  confirmed_at?: string;
  pdf_s3_key?: string;
  photos: Array<{ id: string; s3_key: string; caption?: string; sort_order: number }>;
  created_at: string;
}

export type InspectionResult = "pass" | "fail" | "conditional_pass";
export type InspectionStatus = "draft" | "sent" | "completed";

export interface InspectionRequest {
  id: string;
  project_id: string;
  wbs_item_id?: string;
  inspection_type: string;
  requested_date: string;
  location_detail?: string;
  checklist_items?: Array<{
    item: string;
    standard: string;
    timing: string;
    passed: boolean | null;
  }>;
  result?: InspectionResult;
  inspector_name?: string;
  notes?: string;
  ai_generated: boolean;
  status: InspectionStatus;
  pdf_s3_key?: string;
  created_at: string;
}

export type AlertSeverity = "warning" | "critical";

export interface WeatherAlert {
  id: string;
  project_id: string;
  task_id?: string;
  alert_date: string;
  alert_type: string;
  severity: AlertSeverity;
  message: string;
  is_acknowledged: boolean;
  created_at: string;
}

export interface WeatherData {
  id: string;
  forecast_date: string;
  forecast_type: string;
  temperature_high?: number;
  temperature_low?: number;
  precipitation_mm?: number;
  wind_speed_ms?: number;
  weather_code?: string;
}

export interface WeatherForecastSummary {
  forecast: WeatherData[];
  active_alerts: WeatherAlert[];
}

export type PermitStatus = "not_started" | "submitted" | "in_review" | "approved" | "rejected";

export interface PermitItem {
  id: string;
  project_id: string;
  permit_type: string;
  authority?: string;
  required: boolean;
  deadline?: string;
  status: PermitStatus;
  submitted_date?: string;
  approved_date?: string;
  notes?: string;
  sort_order: number;
  created_at: string;
}

export interface RagSource {
  id: string;
  title: string;
  source_type: string;
  chunk_content: string;
  relevance_score: number;
}

export interface RagAnswer {
  question: string;
  answer: string;
  sources: RagSource[];
  disclaimer: string;
}
