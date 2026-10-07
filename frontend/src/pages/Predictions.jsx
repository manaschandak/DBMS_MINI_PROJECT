import { useEffect, useState } from "react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function Predictions() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPredictions()
      .then(setPredictions)
      .catch(() => setPredictions([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Risk & Predictions</h1>
          <div className="muted">
            Thermal and health risk predictions.
          </div>
        </div>
      </div>

      {loading ? (
        <div className="state">Loading predictions…</div>
      ) : !predictions.length ? (
        <div className="state">
          <h2>No predictions</h2>
          <p className="muted">
            No prediction records are currently available.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Battery</th>
                <th>Type</th>
                <th>Risk</th>
                <th>Confidence</th>
                <th>Model</th>
              </tr>
            </thead>

            <tbody>
              {predictions.map((p) => (
                <tr key={p.prediction_id}>
                  <td>{p.serial_number}</td>
                  <td>{p.risk_type}</td>
                  <td>
                    <RiskBadge
                      level={p.final_risk_level?.toLowerCase()}
                    />
                  </td>
                  <td>
                    {p.confidence != null
                      ? `${Math.round(p.confidence * 100)}%`
                      : "—"}
                  </td>
                  <td>{p.model_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}