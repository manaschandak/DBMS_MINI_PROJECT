import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function Dashboard() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.getBatteries().then(setRows); }, []);

  return (
    <div>
      <h1>Battery fleet</h1>
      <div className="muted">{rows.length} packs monitored, riskiest first</div>

      <div className="summary">
        <span><i className="dot high" /><b>{count("high")}</b> high risk</span>
        <span><i className="dot medium" /><b>{count("medium")}</b> needs attention</span>
        <span><i className="dot low" /><b>{count("low")}</b> healthy</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Battery</th><th>Health</th><th>Temperature</th><th>Risk</th><th>Anomaly</th></tr>
          </thead>
          <tbody>
            {sorted.map((b) => (
              <tr key={b.id}>
                <td><Link to={`/battery/${b.id}`}>{b.model}</Link></td>
                <td>{b.soh_pct}%</td>
                <td>
                  <div className="temp">
                    <span className="temp-val">{b.temperature_c}°C</span>
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
    </div>
  );
}