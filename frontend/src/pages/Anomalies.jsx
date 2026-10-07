import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnomalies()
      .then(setAnomalies)
      .catch(() => setAnomalies([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Anomalies</h1>
          <div className="muted">
            Detected abnormal battery behavior.
          </div>
        </div>

        <button className="btn" disabled>
          Detect anomalies
        </button>
      </div>

      {loading ? (
        <div className="state">Loading anomalies…</div>
      ) : !anomalies.length ? (
        <div className="state">
          <h2>No anomalies</h2>
          <p className="muted">
            No anomaly records are currently available.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Battery</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Detected</th>
              </tr>
            </thead>

            <tbody>
              {anomalies.map((a, index) => (
                <tr key={a.anomaly_id ?? index}>
                  <td>{a.serial_number ?? a.battery_id ?? "—"}</td>
                  <td>{a.anomaly_type ?? "—"}</td>
                  <td>{a.severity ?? "—"}</td>
                  <td>{a.detected_at ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}