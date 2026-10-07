import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getRecommendations()
      .then(setRecommendations)
      .catch(() => setRecommendations([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Recommendations</h1>
          <div className="muted">
            Recommended actions for battery health and safety.
          </div>
        </div>

        <button className="btn" disabled>
          Generate recommendations
        </button>
      </div>

      {loading ? (
        <div className="state">Loading recommendations…</div>
      ) : !recommendations.length ? (
        <div className="state">
          <h2>No recommendations</h2>
          <p className="muted">
            No recommendations are currently available.
          </p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Battery</th>
                <th>Recommendation</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {recommendations.map((r, index) => (
                <tr key={r.recommendation_id ?? index}>
                  <td>{r.serial_number ?? r.battery_id ?? "—"}</td>
                  <td>
                    {r.recommendation ??
                      r.description ??
                      r.message ??
                      "—"}
                  </td>
                  <td>{r.priority ?? "—"}</td>
                  <td>{r.status ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}