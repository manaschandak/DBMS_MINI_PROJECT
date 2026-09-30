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
      <h2>Battery {id}</h2>
      <h4>Temperature (°C)</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="t" /><YAxis /><Tooltip />
          <Line type="monotone" dataKey="temperature_c" stroke="#d32f2f" dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <h4>State of Health (%)</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="t" /><YAxis domain={["auto", "auto"]} /><Tooltip />
          <Line type="monotone" dataKey="soh_pct" stroke="#1976d2" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}