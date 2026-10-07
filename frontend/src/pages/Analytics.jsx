import { useEffect, useState } from "react";
import { api } from "../api/client";

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalyticsDashboard()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Analytics</h1>
          <div className="muted">
            Fleet, chemistry and manufacturer analytics.
          </div>
        </div>
      </div>

      {loading ? (
        <div className="state">Loading analytics…</div>
      ) : (
        <div className="state">
          <h2>
            {data ? "Analytics loaded" : "No analytics data"}
          </h2>

          <p className="muted">
            Fleet trends and comparisons will be displayed here.
          </p>
        </div>
      )}
    </div>
  );
}