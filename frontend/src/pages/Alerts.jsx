import { useEffect, useState } from "react";
import { api } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function Alerts() {
  const [items, setItems] = useState([]);
  useEffect(() => { api.getAlerts().then(setItems); }, []);

  const give = async (id, verdict) => {
    await api.sendFeedback(id, verdict);
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, status: verdict } : a)));
  };

  return (
    <div>
      <h2>Alerts</h2>
      {items.map((a) => (
        <div key={a.id} className={`alert ${a.risk_level}`}>
          <div className="alert-top">
            <RiskBadge level={a.risk_level} />
            <strong>{a.message}</strong>
          </div>
          <div className="muted">
            <Link to={`/battery/${a.battery_id}`}>Battery {a.battery_id}</Link>
          </div>
          <div className="alert-actions">
            {a.status === "open" ? (
              <>
                <button className="btn primary" onClick={() => give(a.id, "confirmed")}>Confirm alert</button>
                <button className="btn" onClick={() => give(a.id, "false_alarm")}>Mark as false alarm</button>
              </>
            ) : (
              <span className="muted">{a.status === "confirmed" ? "Confirmed" : "Marked as false alarm"}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}