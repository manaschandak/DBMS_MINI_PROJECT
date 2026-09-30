import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { api } from "../api/client";

export default function BatteryDetail() {
  const { id } = useParams();
  const [data, setData] = useState([]);
  useEffect(() => { api.getReadings(id).then(setData); }, [id]);

  return (
    <div>
      <Link to="/" className="back">Back to fleet</Link>
      <div className="head">
        <h1>{battery ? battery.model : `Battery ${id}`}</h1>
        {battery && <RiskBadge level={battery.risk_level} />}
      </div>
      {battery && (
        <div className="muted">
          Health {battery.soh_pct}%, currently {battery.temperature_c}°C
          {battery.is_anomaly ? ", anomaly detected" : ""}
        </div>
      )}

      <div className="panel">
        <h2>Temperature (°C)</h2>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data}>
            <CartesianGrid stroke="#e6ebee" vertical={false} />
            <XAxis dataKey="t" tickLine={false} />
            <YAxis domain={[20, 80]} tickLine={false} axisLine={false} />
            <Tooltip />
            <ReferenceLine y={48} stroke="#c98a0b" strokeDasharray="4 4" label={{ value: "Warning 48", fill: "#8a5d00", fontSize: 12, position: "insideTopLeft" }} />
            <ReferenceLine y={60} stroke="#c23b2e" strokeDasharray="4 4" label={{ value: "Critical 60", fill: "#9b2a20", fontSize: 12, position: "insideTopLeft" }} />
            <Line type="monotone" dataKey="temperature_c" stroke="#14212b" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h2>State of health (%)</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <CartesianGrid stroke="#e6ebee" vertical={false} />
            <XAxis dataKey="t" tickLine={false} />
            <YAxis domain={["auto", "auto"]} tickLine={false} axisLine={false} />
            <Tooltip />
            <Line type="monotone" dataKey="soh_pct" stroke="#1f8a70" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}