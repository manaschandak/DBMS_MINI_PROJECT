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
        <div key={a.id} style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, marginBottom: 10 }}>
          <RiskBadge level={a.risk_level} /> Battery {a.battery_id}: {a.message}
          <div style={{ marginTop: 8 }}>
            {a.status === "open" ? (
              <>
                <button onClick={() => give(a.id, "confirmed")}>Confirm</button>{" "}
                <button onClick={() => give(a.id, "false_alarm")}>False alarm</button>
              </>
            ) : (
              <em>Marked: {a.status}</em>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}