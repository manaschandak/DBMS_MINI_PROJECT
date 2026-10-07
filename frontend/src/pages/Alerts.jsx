import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useFetch } from "../hooks/useFetch";
import RiskBadge from "../components/RiskBadge";
import { ErrorState, EmptyState, Skeleton } from "../components/PageState";
import { timeAgo } from "../lib/thresholds";

const TABS = [["open", "Open"], ["confirmed", "Confirmed"], ["false_alarm", "False alarms"], ["all", "All"]];
const RANK = { high: 0, medium: 1, low: 2 };
const STATUS_TEXT = { confirmed: "Confirmed as real", false_alarm: "Marked as false alarm" };

export default function Alerts() {
  const { data, loading, error, reload, setData } = useFetch(async () => {
    const [alerts, batteries] = await Promise.all([api.getAlerts(), api.getBatteries().catch(() => [])]);
    return { alerts, names: Object.fromEntries(batteries.map((b) => [b.id, b.model])) };
  });
  const [tab, setTab] = useState("open");
  const [busy, setBusy] = useState(null);
  const [failed, setFailed] = useState("");

  if (error) return <ErrorState error={error} onRetry={reload} />;
  const alerts = data?.alerts ?? [];
  const names = data?.names ?? {};
  const countOf = (k) => (k === "all" ? alerts.length : alerts.filter((a) => a.status === k).length);
  const list = alerts
    .filter((a) => tab === "all" || a.status === tab)
    .sort((a, b) => RANK[a.risk_level] - RANK[b.risk_level] || new Date(b.created_at || 0) - new Date(a.created_at || 0));

  const give = async (id, verdict) => {
    setBusy(id);
    setFailed("");
    try {
      await api.sendFeedback(id, verdict);
      setData((d) => ({ ...d, alerts: d.alerts.map((a) => (a.id === id ? { ...a, status: verdict } : a)) }));
    } catch {
      setFailed("Couldn't save your feedback. Please try again.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Alerts</h1>
          <div className="muted">Your answers help the model learn which alerts were real.</div>
        </div>
      </div>

      <div className="seg" role="group" aria-label="Filter alerts" style={{ marginBottom: 18 }}>
        {TABS.map(([k, label]) => (
          <button key={k} className={tab === k ? "on" : ""} aria-pressed={tab === k} onClick={() => setTab(k)}>
            {label}<span className="seg-n">{countOf(k)}</span>
          </button>
        ))}
      </div>

      {failed && <div className="callout err" role="alert">{failed}</div>}

      {loading && !data ? <Skeleton rows={3} /> : list.length === 0 ? (
        <EmptyState
          title={tab === "open" ? "All caught up" : "Nothing here"}
          hint={tab === "open" ? "No open alerts need your review." : "No alerts in this view."}
        />
      ) : (
        list.map((a) => (
          <div key={a.id} className={`alert ${a.risk_level}`}>
            <div className="alert-top">
              <RiskBadge level={a.risk_level} />
              <strong>{a.message}</strong>
              {a.created_at && <span className="muted when">{timeAgo(a.created_at)}</span>}
            </div>
            <div className="muted">
              <Link to={`/battery/${a.battery_id}`}>{names[a.battery_id] || `Battery ${a.battery_id}`}</Link>
            </div>
            <div className="alert-actions">
              {a.status === "open" ? (
                <>
                  <button className="btn primary" disabled={busy === a.id} onClick={() => give(a.id, "confirmed")}>Confirm alert</button>
                  <button className="btn" disabled={busy === a.id} onClick={() => give(a.id, "false_alarm")}>Mark as false alarm</button>
                </>
              ) : (
                <span className={`resolved ${a.status}`}>{STATUS_TEXT[a.status] ?? a.status}</span>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
