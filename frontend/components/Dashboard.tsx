"use client";

import type React from "react";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import {
  apiGet,
  apiPost,
} from "@/lib/api";
import type {
  Battery,
  BatteryDetail,
  BatteryHealth,
  CorrectiveActionValidation,
  Diagnostic,
  FailureTree,
  FirmwareIncident,
  FmeaItem,
  Summary
} from "@/lib/api";

type DashboardData = {
  batteries: Battery[];
  summary: Summary;
  firmwareIncidents: FirmwareIncident[];
  batteryHealth: BatteryHealth;
  diagnostics: Diagnostic[];
  fmea: FmeaItem[];
  failureTree: FailureTree;
  correctiveActionValidation: CorrectiveActionValidation;
};

type DiagnosticFilter = "All" | "Thermal" | "SOH" | "Firmware" | "Warning" | "Critical";

const diagnosticFilters: DiagnosticFilter[] = [
  "All",
  "Thermal",
  "SOH",
  "Firmware",
  "Warning",
  "Critical"
];

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedBattery, setSelectedBattery] = useState<string>("");
  const [batteryDetail, setBatteryDetail] = useState<BatteryDetail | null>(null);
  const [diagnosticFilter, setDiagnosticFilter] = useState<DiagnosticFilter>("All");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDashboard() {
    setError(null);
    setLoading(true);
    try {
      const [
        batteries,
        summary,
        firmwareIncidents,
        batteryHealth,
        diagnostics,
        fmea,
        failureTree,
        correctiveActionValidation
      ] =
        await Promise.all([
          apiGet<Battery[]>("/batteries"),
          apiGet<Summary>("/dashboard/summary"),
          apiGet<FirmwareIncident[]>("/dashboard/firmware-incidents"),
          apiGet<BatteryHealth>("/dashboard/battery-health"),
          apiGet<Diagnostic[]>("/diagnostics"),
          apiGet<FmeaItem[]>("/reliability/fmea"),
          apiGet<FailureTree>("/reliability/failure-tree"),
          apiGet<CorrectiveActionValidation>("/reliability/corrective-action-validation")
        ]);
      setData({
        batteries,
        summary,
        firmwareIncidents,
        batteryHealth,
        diagnostics,
        fmea,
        failureTree,
        correctiveActionValidation
      });
      const fallbackBattery =
        summary.affected_batteries[0] ?? batteries[0]?.battery_id ?? "";
      setSelectedBattery((current) => current || fallbackBattery);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "API error");
    } finally {
      setLoading(false);
    }
  }

  async function generateDemoData() {
    setGenerating(true);
    setError(null);
    try {
      await apiPost("/demo/generate");
      setSelectedBattery("");
      setBatteryDetail(null);
      await loadDashboard();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "API error");
    } finally {
      setGenerating(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (!selectedBattery) {
      setBatteryDetail(null);
      return;
    }
    apiGet<BatteryDetail>(`/batteries/${selectedBattery}`)
      .then(setBatteryDetail)
      .catch(() => setBatteryDetail(null));
  }, [selectedBattery]);

  const issueMap = useMemo(() => {
    const map = new Map<string, Diagnostic[]>();
    data?.diagnostics.forEach((diagnostic) => {
      const items = map.get(diagnostic.battery_id) ?? [];
      items.push(diagnostic);
      map.set(diagnostic.battery_id, items);
    });
    return map;
  }, [data]);

  const filteredDiagnostics = useMemo(() => {
    if (!data) {
      return [];
    }
    if (diagnosticFilter === "All") {
      return data.diagnostics;
    }
    return data.diagnostics.filter((diagnostic) => {
      if (diagnosticFilter === "Thermal") {
        return diagnostic.issue_type.toLowerCase().includes("temperature");
      }
      if (diagnosticFilter === "SOH") {
        return diagnostic.issue_type.toLowerCase().includes("soh");
      }
      if (diagnosticFilter === "Firmware") {
        return diagnostic.issue_type.toLowerCase().includes("firmware");
      }
      return diagnostic.severity === diagnosticFilter;
    });
  }, [data, diagnosticFilter]);

  return (
    <main className="min-h-screen bg-slate-100 text-ink">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-line pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">
              Synthetic data
            </p>
            <h1 className="mt-1 text-2xl font-semibold sm:text-3xl">
              Battery Fleet Diagnostic & Reliability Analyzer
            </h1>
            <p className="mt-1 text-sm text-muted">
              Residential Energy Fleet Health Demo
            </p>
          </div>
          <button
            className="h-11 rounded-md bg-accent px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
            onClick={generateDemoData}
            disabled={generating}
          >
            {generating ? "Generating..." : "Generate / Refresh Data"}
          </button>
        </header>

        {error ? (
          <section className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-bad">
            API error: {error}. Confirm the FastAPI backend is running and
            NEXT_PUBLIC_API_URL is set correctly.
          </section>
        ) : null}

        {loading ? (
          <section className="rounded-md border border-line bg-panel p-6 text-sm text-muted">
            Loading fleet telemetry...
          </section>
        ) : null}

        {!loading && data && data.summary.fleet_size === 0 ? (
          <section className="rounded-md border border-line bg-panel p-6 text-sm text-muted">
            No telemetry is loaded yet. Generate synthetic data to populate the demo.
          </section>
        ) : null}

        {data && data.summary.fleet_size > 0 ? (
          <>
            <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <KpiCard label="Total fleet" value={data.summary.fleet_size} />
              <KpiCard label="Healthy batteries" value={data.summary.healthy_battery_count} />
              <KpiCard label="Batteries with issues" value={data.summary.batteries_with_active_issues} />
              <KpiCard label="Incident rate" value={`${Math.round(data.summary.incident_rate * 100)}%`} />
              <KpiCard label="Average SOH" value={`${data.summary.average_state_of_health}%`} />
            </section>

            <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
              <div className="rounded-md border border-line bg-panel p-4">
                <SectionTitle
                  title="Demo scope"
                  tooltip="Synthetic scenarios injected into the demo fleet so the diagnostic workflow has visible examples."
                />
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  <ScopeItem
                    label="Thermal"
                    value="Overtemperature"
                    detail="BAT-004, BAT-007, BAT-009"
                  />
                  <ScopeItem
                    label="Degradation"
                    value="Abnormal SOH drop"
                    detail="BAT-013, BAT-014, BAT-015"
                  />
                  <ScopeItem
                    label="Firmware"
                    value="Incident increase"
                    detail="Firmware 2.1.0 cohort"
                  />
                </div>
              </div>

              <div className="rounded-md border border-line bg-panel p-4">
                <SectionTitle
                  title="Engineering readout"
                  tooltip="Plain-language interpretation of the fleet signal, written the way an engineer might summarize it for a review."
                />
                <p className="mt-3 text-sm leading-6 text-muted">
                  The dashboard separates fleet-level reliability signals from unit-level
                  diagnostics. Root causes are framed as hypotheses and should be validated
                  with service history, environment data, and firmware comparison.
                </p>
              </div>
            </section>

            <section className="grid gap-4 lg:grid-cols-2">
              <ChartPanel title="Incidents by firmware version">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.firmwareIncidents} margin={{ left: 4, right: 16, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="firmware_version" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="incident_battery_count" name="Incident batteries" fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartPanel>

              <ChartPanel title="Battery health distribution">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={data.batteryHealth.distribution} margin={{ left: 4, right: 16, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" name="Batteries" fill="#15803d" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartPanel>

              <ChartPanel title="Temperature comparison">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart
                    data={data.batteryHealth.temperature_by_battery}
                    margin={{ left: 4, right: 16, bottom: 8 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="battery_id" interval={5} tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 60]} />
                    <Tooltip />
                    <ReferenceLine y={45} stroke="#b91c1c" strokeDasharray="4 4" label="45 C limit" />
                    <Bar dataKey="temperature" name="Max temperature C">
                      {data.batteryHealth.temperature_by_battery.map((row) => (
                        <Cell
                          key={row.battery_id}
                          fill={row.temperature > 45 ? "#b91c1c" : "#b45309"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartPanel>

              <ChartPanel title="SOH comparison across batteries">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart
                    data={data.batteryHealth.soh_by_battery}
                    margin={{ left: 4, right: 16, bottom: 8 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="battery_id" interval={5} tick={{ fontSize: 11 }} />
                    <YAxis domain={[80, 100]} />
                    <Tooltip />
                    <ReferenceLine y={92} stroke="#b45309" strokeDasharray="4 4" label="SOH watch" />
                    <Bar dataKey="state_of_health" name="SOH %">
                      {data.batteryHealth.soh_by_battery.map((row) => (
                        <Cell
                          key={row.battery_id}
                          fill={row.state_of_health < 92 ? "#b91c1c" : "#0f766e"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartPanel>
            </section>

            <section className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
              <div className="rounded-md border border-line bg-panel p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <SectionTitle
                      title="Diagnostic table"
                      tooltip="Rule-based findings generated from telemetry. Observed is the value that triggered each finding."
                    />
                    <p className="mt-1 text-sm text-muted">
                      Showing {filteredDiagnostics.length} of {data.diagnostics.length} findings
                    </p>
                  </div>
                  <span className="text-xs text-muted">Root causes are hypotheses</span>
                </div>
                <div className="mb-4 flex flex-wrap gap-2">
                  {diagnosticFilters.map((filter) => (
                    <button
                      key={filter}
                      className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${
                        diagnosticFilter === filter
                          ? "border-accent bg-blue-50 text-accent"
                          : "border-line bg-white text-muted hover:border-accent hover:text-accent"
                      }`}
                      onClick={() => setDiagnosticFilter(filter)}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[900px] border-collapse text-left text-sm">
                    <thead className="border-b border-line text-xs uppercase text-muted">
                      <tr>
                        <th className="py-2 pr-3">Battery ID</th>
                        <th className="py-2 pr-3">Region</th>
                        <th className="py-2 pr-3">Firmware</th>
                        <th className="py-2 pr-3">Issue</th>
                        <th className="py-2 pr-3">Severity</th>
                        <th className="py-2 pr-3">Observed</th>
                        <th className="py-2 pr-3">Likely cause</th>
                        <th className="py-2 pr-3">Recommended action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredDiagnostics.map((diagnostic) => (
                        <tr key={`${diagnostic.battery_id}-${diagnostic.issue_type}`} className="border-b border-slate-100">
                          <td className="py-3 pr-3 font-medium">{diagnostic.battery_id}</td>
                          <td className="py-3 pr-3">{diagnostic.region}</td>
                          <td className="py-3 pr-3">{diagnostic.firmware_version}</td>
                          <td className="py-3 pr-3">{diagnostic.issue_type}</td>
                          <td className="py-3 pr-3">
                            <SeverityBadge severity={diagnostic.severity} />
                          </td>
                          <td className="py-3 pr-3">{diagnostic.observed_value}</td>
                          <td className="py-3 pr-3">{diagnostic.likely_cause}</td>
                          <td className="py-3 pr-3">{diagnostic.recommended_action}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {filteredDiagnostics.length === 0 ? (
                    <p className="py-6 text-sm text-muted">No diagnostics match this filter.</p>
                  ) : null}
                </div>
              </div>

              <aside className="rounded-md border border-line bg-panel p-4">
                <SectionTitle
                  title="Technical insight"
                  tooltip="Fleet-level interpretation that summarizes the dominant trend, affected population, risk level, and next step."
                />
                <dl className="mt-4 space-y-4 text-sm">
                  <Insight label="Main observed trend" value={data.summary.main_observed_trend} />
                  <Insight label="Population affected" value={data.summary.population_affected} />
                  <div>
                    <dt className="text-muted">Risk level</dt>
                    <dd className="mt-1">
                      <SeverityBadge severity={data.summary.risk_level} />
                    </dd>
                  </div>
                  <Insight label="Recommended next step" value={data.summary.recommended_next_step} />
                </dl>
              </aside>
            </section>

            <section className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
              <div className="rounded-md border border-line bg-panel p-4">
                <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <SectionTitle
                      title="FMEA register"
                      tooltip="Failure Mode and Effects Analysis. S, O, and D are scored to calculate RPN and prioritize engineering risk."
                    />
                    <p className="text-sm text-muted">Severity, occurrence, detection, and risk priority</p>
                  </div>
                  <span className="text-xs text-muted">RPN = S x O x D</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[860px] border-collapse text-left text-sm">
                    <thead className="border-b border-line text-xs uppercase text-muted">
                      <tr>
                        <th className="py-2 pr-3">Failure mode</th>
                        <th className="py-2 pr-3">Effect</th>
                        <th className="py-2 pr-3">Detection</th>
                        <th className="py-2 pr-3">
                          <HeaderTooltip label="S" tooltip="Severity: how serious the effect is if the failure occurs." />
                        </th>
                        <th className="py-2 pr-3">
                          <HeaderTooltip label="O" tooltip="Occurrence: how likely or frequent the failure mode is in this demo." />
                        </th>
                        <th className="py-2 pr-3">
                          <HeaderTooltip label="D" tooltip="Detection: how likely the current controls are to detect the issue before impact." />
                        </th>
                        <th className="py-2 pr-3">
                          <HeaderTooltip label="RPN" tooltip="Risk Priority Number. Calculated as Severity x Occurrence x Detection." />
                        </th>
                        <th className="py-2 pr-3">Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.fmea.map((item) => (
                        <tr key={item.failure_mode} className="border-b border-slate-100">
                          <td className="py-3 pr-3 font-medium">{item.failure_mode}</td>
                          <td className="py-3 pr-3">{item.system_effect}</td>
                          <td className="py-3 pr-3">{item.detection_method}</td>
                          <td className="py-3 pr-3">{item.severity}</td>
                          <td className="py-3 pr-3">{item.occurrence}</td>
                          <td className="py-3 pr-3">{item.detection}</td>
                          <td className="py-3 pr-3 font-semibold">{item.rpn}</td>
                          <td className="py-3 pr-3">
                            <PriorityBadge priority={item.priority} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid gap-4">
                <div className="rounded-md border border-line bg-panel p-4">
                  <SectionTitle
                    title="Failure tree"
                    tooltip="Fault-tree style hypothesis map for the critical BAT-009 overtemperature event."
                  />
                  <FailureTreeView tree={data.failureTree} />
                </div>

                <div className="rounded-md border border-line bg-panel p-4">
                  <div className="mb-3">
                    <SectionTitle
                      title="Corrective action validation"
                      tooltip="Before/after comparison used to check whether a corrective action reduced the targeted failure mode."
                    />
                    <p className="text-sm text-muted">{data.correctiveActionValidation.action}</p>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={validationChartData(data.correctiveActionValidation)} margin={{ left: 4, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="phase" />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="count" name={data.correctiveActionValidation.metric} fill="#2563eb" />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <MetricTile
                      label="Reduction"
                      value={`${Math.round(data.correctiveActionValidation.relative_reduction * 100)}%`}
                    />
                    <MetricTile
                      label="Status"
                      value={data.correctiveActionValidation.status}
                    />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted">
                    {data.correctiveActionValidation.interpretation}
                  </p>
                </div>
              </div>
            </section>

            <section className="rounded-md border border-line bg-panel p-4">
              <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <SectionTitle
                    title="Battery detail"
                    tooltip="Unit-level telemetry view for one selected battery, including recent values and detected diagnostics."
                  />
                  <p className="text-sm text-muted">Recent telemetry and detected diagnostics</p>
                </div>
                <select
                  className="h-10 rounded-md border border-line bg-white px-3 text-sm"
                  value={selectedBattery}
                  onChange={(event) => setSelectedBattery(event.target.value)}
                >
                  {data.batteries.map((battery) => (
                    <option key={battery.battery_id} value={battery.battery_id}>
                      {battery.battery_id} {issueMap.has(battery.battery_id) ? "- issue" : "- normal"}
                    </option>
                  ))}
                </select>
              </div>

              {batteryDetail ? (
                <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.5fr]">
                  <div className="space-y-4 text-sm">
                    <div className="grid grid-cols-2 gap-3">
                      <MetricTile label="Battery ID" value={batteryDetail.battery.battery_id} />
                      <MetricTile label="Region" value={batteryDetail.battery.site_region} />
                      <MetricTile label="Firmware" value={batteryDetail.battery.firmware_version ?? "Unknown"} />
                      <MetricTile
                        label="Status"
                        value={batteryDetail.diagnostics.length ? "Issue active" : "Normal"}
                      />
                    </div>
                    <div>
                      <p className="text-muted">Detected diagnostics</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {batteryDetail.diagnostics.length ? (
                          batteryDetail.diagnostics.map((item) => (
                            <span
                              key={item.issue_type}
                              className="rounded-md border border-line bg-slate-50 px-2 py-1 text-xs font-semibold"
                            >
                              {item.issue_type}
                            </span>
                          ))
                        ) : (
                          <SeverityBadge severity="Normal" />
                        )}
                      </div>
                    </div>
                    <div>
                      <p className="text-muted">Recent error codes</p>
                      <p className="mt-1 font-medium">
                        {recentErrorCodes(batteryDetail).length
                          ? recentErrorCodes(batteryDetail).join(", ")
                          : "None"}
                      </p>
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={batteryDetail.recent_telemetry}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tickFormatter={formatHour}
                        interval={5}
                        tick={{ fontSize: 11 }}
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="temperature" name="Temp C" stroke="#b45309" dot={false} />
                      <Line type="monotone" dataKey="voltage" name="Voltage" stroke="#2563eb" dot={false} />
                      <Line type="monotone" dataKey="state_of_charge" name="SOC %" stroke="#15803d" dot={false} />
                      <Line type="monotone" dataKey="state_of_health" name="SOH %" stroke="#0f766e" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="mt-4 text-sm text-muted">Select a battery to view details.</p>
              )}
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}

function KpiCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-panel p-4">
      <p className="text-xs font-semibold uppercase text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function ScopeItem({
  label,
  value,
  detail
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase text-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
      <p className="mt-1 text-xs text-muted">{detail}</p>
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-slate-50 p-3">
      <p className="text-xs font-semibold uppercase text-muted">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

function ChartPanel({
  title,
  children
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-md border border-line bg-panel p-4">
      <h2 className="mb-3 text-base font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function SectionTitle({ title, tooltip }: { title: string; tooltip: string }) {
  return (
    <div className="flex items-center gap-2">
      <h2 className="text-base font-semibold">{title}</h2>
      <InfoTooltip text={tooltip} />
    </div>
  );
}

function HeaderTooltip({ label, tooltip }: { label: string; tooltip: string }) {
  return (
    <span className="inline-flex items-center gap-1">
      {label}
      <InfoTooltip text={tooltip} compact />
    </span>
  );
}

function InfoTooltip({ text, compact = false }: { text: string; compact?: boolean }) {
  const sizeClass = compact ? "h-4 w-4 text-[10px]" : "h-5 w-5 text-xs";

  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-label={text}
        className={`${sizeClass} flex items-center justify-center rounded-full border border-line bg-white font-semibold text-muted transition hover:border-accent hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2`}
      >
        ?
      </button>
      <span className="pointer-events-none absolute left-1/2 top-full z-20 mt-2 w-64 -translate-x-1/2 rounded-md border border-line bg-ink px-3 py-2 text-left text-xs font-medium normal-case leading-5 text-white opacity-0 shadow-lg transition group-hover:opacity-100 group-focus-within:opacity-100">
        {text}
      </span>
    </span>
  );
}

function SeverityBadge({ severity }: { severity: "Normal" | "Warning" | "Critical" }) {
  const classes = {
    Normal: "bg-green-50 text-good border-green-200",
    Warning: "bg-amber-50 text-warn border-amber-200",
    Critical: "bg-red-50 text-bad border-red-200"
  };
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${classes[severity]}`}>
      {severity}
    </span>
  );
}

function PriorityBadge({ priority }: { priority: "Low" | "Medium" | "High" }) {
  const classes = {
    Low: "bg-green-50 text-good border-green-200",
    Medium: "bg-amber-50 text-warn border-amber-200",
    High: "bg-red-50 text-bad border-red-200"
  };
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-semibold ${classes[priority]}`}>
      {priority}
    </span>
  );
}

function FailureTreeView({ tree }: { tree: FailureTree }) {
  return (
    <div className="mt-4 text-sm">
      <div className="rounded-md border border-red-200 bg-red-50 p-3">
        <p className="text-xs font-semibold uppercase text-bad">Top event</p>
        <p className="mt-1 font-semibold">{tree.top_event}</p>
        <p className="mt-1 text-xs text-muted">
          {tree.focus_battery}: {tree.observed_evidence}
        </p>
      </div>
      <div className="mx-auto h-5 w-px bg-line" />
      <div className="mx-auto mb-3 flex h-7 w-7 items-center justify-center rounded-full border border-line bg-white text-xs font-semibold">
        {tree.logic}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {tree.children.map((child) => (
          <div key={child.label} className="rounded-md border border-line bg-slate-50 p-3">
            <p className="font-semibold">{child.label}</p>
            <p className="mt-1 text-xs leading-5 text-muted">{child.evidence}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Insight({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}

function formatHour(timestamp: string) {
  const date = new Date(timestamp);
  return `${date.getHours().toString().padStart(2, "0")}:00`;
}

function recentErrorCodes(detail: BatteryDetail) {
  return Array.from(
    new Set(
      detail.recent_telemetry
        .map((record) => record.error_code)
        .filter((errorCode): errorCode is string => Boolean(errorCode))
    )
  );
}

function validationChartData(validation: CorrectiveActionValidation) {
  return [
    { phase: "Before", count: validation.before_count },
    { phase: "After", count: validation.after_count }
  ];
}
