import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function Dashboard() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.getBatteries().then(setRows); }, []);

  return (
    <div>
      <h2>Battery Fleet</h2>
      <table width="100%" cellPadding={8}>
        <thead><tr><th>ID</th><th>Model</th><th>SoH %</th><th>Temp °C</th><th>Risk</th><th>Anomaly</th></tr></thead>
        <tbody>
          {rows.map((b) => (
            <tr key={b.id}>
              <td><Link to={`/battery/${b.id}`}>{b.id}</Link></td>
              <td>{b.model}</td>
              <td>{b.soh_pct}</td>
              <td>{b.temperature_c}</td>
              <td><RiskBadge level={b.risk_level} /></td>
              <td>{b.is_anomaly ? "⚠️" : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}