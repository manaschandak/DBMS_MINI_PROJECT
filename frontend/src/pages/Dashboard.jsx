import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useFetch } from "../hooks/useFetch";
import RiskBadge from "../components/RiskBadge";
import Stat from "../components/Stat";
import { ErrorState, EmptyState, Skeleton } from "../components/PageState";
import { gaugePos, healthStatus, tempStatus } from "../lib/thresholds";

const RANK = { high: 0, medium: 1, low: 2 };
const sorters = {
  model: (a, b) => a.model.localeCompare(b.model, undefined, { numeric: true }),
  soh_pct: (a, b) => a.soh_pct - b.soh_pct,
  temperature_c: (a, b) => a.temperature_c - b.temperature_c,
  risk_level: (a, b) => RANK[a.risk_level] - RANK[b.risk_level],
  is_anomaly: (a, b) => Number(b.is_anomaly) - Number(a.is_anomaly),
};
const DEFAULT_DIR = { temperature_c: "desc" };
const FILTERS = [["all", "All"], ["high", "High"], ["medium", "Medium"], ["low", "Low"]];

const columns = [
  ["model", "Battery"], ["soh_pct", "Health"], ["temperature_c", "Temperature"],
  ["risk_level", "Risk"], ["is_anomaly", "Anomaly"],
];

function exportCsv(rows) {
  const head = "id,model,soh_pct,temperature_c,risk_level,is_anomaly";
  const body = rows.map((b) => [b.id, b.model, b.soh_pct, b.temperature_c, b.risk_level, b.is_anomaly].join(","));
  const url = URL.createObjectURL(new Blob([[head, ...body].join("\n")], { type: "text/csv" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: "battery-fleet.csv" });
  a.click();
  URL.revokeObjectURL(url);
}

export default function Dashboard() {
  const { data: rows, loading, error, reload } = useFetch(api.getBatteries);
  const { data: alerts } = useFetch(() => api.getAlerts().catch(() => []));
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState({ key: "risk_level", dir: "asc" });

  const all = rows ?? [];
  const count = (l) => all.filter((b) => b.risk_level === l).length;
  const avgHealth = all.length ? Math.round(all.reduce((s, b) => s + b.soh_pct, 0) / all.length) : 0;
  const openAlerts = (alerts ?? []).filter((a) => a.status === "open").length;

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = all.filter((b) => (filter === "all" || b.risk_level === filter) && (!q || b.model.toLowerCase().includes(q)));
    const f = sorters[sort.key];
    const m = sort.dir === "asc" ? 1 : -1;
    return list.sort((a, b) => m * f(a, b) || RANK[a.risk_level] - RANK[b.risk_level] || sorters.model(a, b));
  }, [all, query, filter, sort]);

  const toggleSort = (key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: DEFAULT_DIR[key] || "asc" }));

  if (error) return <ErrorState error={error} onRetry={reload} />;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Battery fleet</h1>
          <div className="muted">{loading ? "Loading packs…" : `${all.length} packs monitored`}</div>
        </div>
        <button className="btn" onClick={reload} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
      </div>

      <div className="stats">
        <Stat label="High risk" value={count("high")} tone="high" sub="act now" />
        <Stat label="Needs attention" value={count("medium")} tone="medium" sub="monitor closely" />
        <Stat label="Healthy" value={count("low")} tone="low" sub="no action" />
        <Stat label="Avg. health" value={`${avgHealth}%`} sub="state of health" />
        <Link to="/alerts" className="stat-link">
          <Stat label="Open alerts" value={openAlerts} sub="review and give feedback →" tone={openAlerts ? "high" : undefined} />
        </Link>
      </div>

      <div className="toolbar">
        <input
          className="search" type="search" placeholder="Search packs, e.g. B-200" aria-label="Search packs"
          value={query} onChange={(e) => setQuery(e.target.value)}
        />
        <div className="seg" role="group" aria-label="Filter by risk">
          {FILTERS.map(([k, label]) => (
            <button key={k} className={filter === k ? "on" : ""} aria-pressed={filter === k} onClick={() => setFilter(k)}>
              {label}<span className="seg-n">{k === "all" ? all.length : count(k)}</span>
            </button>
          ))}
        </div>
        <button className="btn" onClick={() => exportCsv(visible)} disabled={!visible.length}>Export CSV</button>
      </div>

      {loading && !rows ? <Skeleton rows={6} /> : !visible.length ? (
        <EmptyState
          title="No packs match"
          hint="Try a different search or risk filter."
          action={<button className="btn" onClick={() => { setQuery(""); setFilter("all"); }}>Clear filters</button>}
        />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map(([key, label]) => (
                  <th key={key} aria-sort={sort.key === key ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}>
                    <button className="th-btn" onClick={() => toggleSort(key)}>
                      {label}<span className="arrow">{sort.key === key ? (sort.dir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((b) => (
                <tr key={b.id}>
                  <td><Link to={`/battery/${b.id}`} className="pack">{b.model}</Link></td>
                  <td>
                    <div className="soh">
                      <span className="num">{b.soh_pct}%</span>
                      <div className="bar-track"><i className={healthStatus(b.soh_pct)} style={{ width: `${b.soh_pct}%` }} /></div>
                    </div>
                  </td>
                  <td>
                    <div className="temp">
                      <span className={`temp-val ${tempStatus(b.temperature_c).key}`}>{b.temperature_c}°C</span>
                      <div className="gauge"><i style={{ left: `${gaugePos(b.temperature_c)}%` }} /></div>
                    </div>
                  </td>
                  <td><RiskBadge level={b.risk_level} /></td>
                  <td>{b.is_anomaly ? <span className="flag">Detected</span> : <span className="muted">None</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!loading && visible.length > 0 && <div className="muted foot">Showing {visible.length} of {all.length} packs</div>}
    </div>
  );
}
