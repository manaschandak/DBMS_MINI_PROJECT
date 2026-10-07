import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function ModelPerformance() {
  const [performance, setPerformance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getModelPerformance()
      .then(setPerformance)
      .catch(() => setPerformance([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Model Performance</h1>
          <div className="muted">
            ML model evaluation and performance metrics.
          </div>
        </div>
      </div>

      {loading ? (
        <div className="state">Loading model performance…</div>
      ) : (
        <div className="state">
          <h2>
            {performance.length
              ? "Performance data available"
              : "No performance data"}
          </h2>

          <p className="muted">
            Evaluation metrics will be displayed here.
          </p>
        </div>
      )}
    </div>
  );
}