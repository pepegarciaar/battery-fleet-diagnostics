export type Summary = {
  fleet_size: number;
  healthy_battery_count: number;
  batteries_with_active_issues: number;
  incident_rate: number;
  average_temperature: number;
  average_state_of_health: number;
  affected_batteries: string[];
  main_observed_trend: string;
  population_affected: string;
  risk_level: "Normal" | "Warning" | "Critical";
  recommended_next_step: string;
  synthetic_data: boolean;
};

export type FirmwareIncident = {
  firmware_version: string;
  battery_count: number;
  incident_battery_count: number;
  incident_rate: number;
};

export type BatteryHealth = {
  distribution: Array<{ range: string; count: number }>;
  soh_by_battery: Array<{ battery_id: string; state_of_health: number }>;
  temperature_by_battery: Array<{ battery_id: string; temperature: number }>;
};

export type Diagnostic = {
  battery_id: string;
  region: string;
  firmware_version: string;
  issue_type: string;
  severity: "Normal" | "Warning" | "Critical";
  observed_value: number;
  expected_range: string;
  likely_cause: string;
  recommended_action: string;
};

export type FmeaItem = {
  failure_mode: string;
  system_effect: string;
  potential_cause: string;
  detection_method: string;
  severity: number;
  occurrence: number;
  detection: number;
  rpn: number;
  priority: "Low" | "Medium" | "High";
  recommended_action: string;
};

export type FailureTree = {
  top_event: string;
  focus_battery: string;
  observed_evidence: string;
  logic: string;
  children: Array<{
    label: string;
    evidence: string;
  }>;
};

export type CorrectiveActionValidation = {
  action: string;
  target_failure_mode: string;
  metric: string;
  before_count: number;
  after_count: number;
  before_rate: number;
  after_rate: number;
  relative_reduction: number;
  status: string;
  interpretation: string;
};

export type Battery = {
  battery_id: string;
  site_region: string;
  firmware_version: string | null;
  status: string;
  model: string | null;
};

export type BatteryDetail = {
  battery: Battery;
  recent_telemetry: Array<{
    timestamp: string;
    voltage: number;
    current: number;
    temperature: number;
    state_of_charge: number;
    state_of_health: number;
    error_code: string | null;
    operating_mode: string;
  }>;
  diagnostics: Diagnostic[];
  synthetic_data: boolean;
};

function apiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    return "/api";
  }
  return "http://127.0.0.1:8000";
}

const API_URL = apiBaseUrl();

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
