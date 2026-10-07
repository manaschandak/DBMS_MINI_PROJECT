import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ReferenceLine, ResponsiveContainer } from "recharts";
import { api } from "../api/client";
import { useFetch } from "../hooks/useFetch";
import RiskBadge from "../components/RiskBadge";
import Stat from "../components/Stat";
import { ErrorState, Skeleton } from "../components/PageState";
import { CRIT_C, WARN_C, tempStatus, healthStatus, timeAgo } from "../lib/thresholds";

const RANGES = [["10", "Last 10"], ["20", "Last 20"], ["all", "All"]];

function ChartTip({ active, payload, label, unit, last }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tip">
      <div className="muted">{label === last ? "Latest reading" : `${last - label} readings ago`}</div>
      <b>{payload[0].value}{unit}</b>
    </div>
  );
}

export default function BatteryDetail() {
  const { id } = useParams();
  const [range, setRange] = useState("all");
  const { data, loading, error, reload } = useFetch(
    async () => {
      const [list, readings, alerts] = await Promise.all([api.getBatteries(), api.getReadings(id), api.getAlerts().catch(() => [])]);
      return { battery: list.find((b) => b.id === Number(id)), readings, alerts: alerts.filter((a) => a.battery_id === Number(id)) };
    },
    [id]
  );

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (loading && !data) return <><Link to="/" className="back">← Back to fleet</Link><Skeleton rows={4} /></>;
  const { battery, readings, alerts } = data;
  if (!battery) {
    return (
      <div className="state"><h2>Battery not found</h2><p className="muted">No pack with id {id}.</p><Link to="/" className="btn">Back to fleet</Link></div>
    );
  }

  const shown = range === "all" ? readings : readings.slice(-Number(range));
  const last = readings.length - 1;
  const peak = Math.max(...shown.map((r) => r.temperature_c));
  const ts = tempStatus(battery.temperature_c);
  const open = alerts.filter((a) => a.status === "open");
  const tickFmt = (t) => (t === last ? "now" : `-${last - t}`);

  return (
    <div>
      <Link to="/" className="back">← Back to fleet</Link>
      <div className="head">
        <h1>{battery.model}</h1>
        <RiskBadge level={battery.risk_level} />
        {battery.is_anomaly && <span className="badge anomaly">Anomaly</span>}
      </div>

      {battery.is_anomaly && (
        <div className="callout" role="note">
          The anomaly detector flagged an unusual temperature pattern on this pack. Check the trend below and review its alerts.
        </div>
      )}

      <div className="stats">
        <Stat label="State of health" value={`${battery.soh_pct}%`} tone={healthStatus(battery.soh_pct)} sub={battery.soh_pct >= 80 ? "good" : battery.soh_pct >= 70 ? "degrading" : "poor"} />
        <Stat label="Temperature now" value={`${battery.temperature_c}°C`} tone={ts.key} sub={ts.label} />
        <Stat label="Peak in view" value={`${peak.toFixed(1)}°C`} tone={tempStatus(peak).key} sub={tempStatus(peak).label} />
        <Stat label="Open alerts" value={open.length} tone={open.length ? "high" : undefined} sub={open.length ? "needs review" : "all clear"} />
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Temperature (°C)</h2>
          <div className="seg small" role="group" aria-label="Time range">
            {RANGES.map(([k, label]) => (
              <button key={k} className={range === k ? "on" : ""} aria-pressed={range === k} onClick={() => setRange(k)}>{label}</button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={shown} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="tfill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#14212b" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#14212b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#e6ebee" vertical={false} />
            <XAxis dataKey="t" tickLine={false} tickFormatter={tickFmt} />
            <YAxis domain={[20, 80]} tickLine={false} axisLine={false} />
            <Tooltip content={<ChartTip unit="°C" last={last} />} />
            <ReferenceLine y={WARN_C} stroke="#c98a0b" strokeDasharray="4 4" label={{ value: `Warning ${WARN_C}`, fill: "#8a5d00", fontSize: 12, position: "insideTopLeft" }} />
            <ReferenceLine y={CRIT_C} stroke="#c23b2e" strokeDasharray="4 4" label={{ value: `Critical ${CRIT_C}`, fill: "#9b2a20", fontSize: 12, position: "insideTopLeft" }} />
            <Area type="monotone" dataKey="temperature_c" stroke="#14212b" strokeWidth={2} fill="url(#tfill)" dot={false} activeDot={{ r: 4 }} />
          </AreaChart>
        </ResponsiveContainer>
        <div className="axis-note muted">Readings ago</div>
      </div>

      <div className="panel">
        <h2>State of health (%)</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={shown} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
            <CartesianGrid stroke="#e6ebee" vertical={false} />
            <XAxis dataKey="t" tickLine={false} tickFormatter={tickFmt} />
            <YAxis domain={["auto", "auto"]} tickLine={false} axisLine={false} />
            <Tooltip content={<ChartTip unit="%" last={last} />} />
            <Line type="monotone" dataKey="soh_pct" stroke="#1f8a70" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <div className="panel-head"><h2>Alerts for this pack</h2><Link to="/alerts" className="muted">All alerts →</Link></div>
        {alerts.length === 0 ? <p className="muted">No alerts for this pack.</p> : (
          <ul className="mini-alerts">
            {alerts.map((a) => (
              <li key={a.id}>
                <RiskBadge level={a.risk_level} />
                <span className="grow">{a.message}</span>
                <span className="muted">{a.status === "open" ? timeAgo(a.created_at) || "open" : a.status === "confirmed" ? "Confirmed" : "False alarm"}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
