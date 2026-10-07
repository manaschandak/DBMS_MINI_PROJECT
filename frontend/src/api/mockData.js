const hoursAgo = (h) => new Date(Date.now() - h * 3600e3).toISOString();

export const batteries = [
  { id: 1, model: "Pack A-100", soh_pct: 92, temperature_c: 31, risk_level: "low", is_anomaly: false },
  { id: 2, model: "Pack A-101", soh_pct: 74, temperature_c: 49, risk_level: "medium", is_anomaly: false },
  { id: 3, model: "Pack B-200", soh_pct: 66, temperature_c: 63, risk_level: "high", is_anomaly: true },
  { id: 4, model: "Pack A-102", soh_pct: 88, temperature_c: 35, risk_level: "low", is_anomaly: false },
  { id: 5, model: "Pack B-201", soh_pct: 81, temperature_c: 38, risk_level: "low", is_anomaly: false },
  { id: 6, model: "Pack B-202", soh_pct: 71, temperature_c: 52, risk_level: "medium", is_anomaly: false },
  { id: 7, model: "Pack C-300", soh_pct: 95, temperature_c: 29, risk_level: "low", is_anomaly: false },
  { id: 8, model: "Pack C-301", soh_pct: 59, temperature_c: 58, risk_level: "high", is_anomaly: true },
  { id: 9, model: "Pack C-302", soh_pct: 84, temperature_c: 41, risk_level: "low", is_anomaly: false },
  { id: 10, model: "Pack A-103", soh_pct: 77, temperature_c: 47, risk_level: "medium", is_anomaly: true },
  { id: 11, model: "Pack B-203", soh_pct: 90, temperature_c: 33, risk_level: "low", is_anomaly: false },
  { id: 12, model: "Pack C-303", soh_pct: 69, temperature_c: 55, risk_level: "medium", is_anomaly: false },
];

export const readingsFor = (id) => {
  const b = batteries.find((x) => x.id === Number(id)) ?? batteries[0];
  const N = 30;
  const start = b.is_anomaly ? b.temperature_c - 16 : b.temperature_c - 3;
  return Array.from({ length: N }, (_, i) => {
    const p = i / (N - 1);
    const rise = (b.temperature_c - start) * Math.pow(p, b.is_anomaly ? 3 : 1);
    const wobble = Math.sin(i / 3 + id) * 1.8 * (1 - p);
    return {
      t: i,
      temperature_c: Math.round((start + rise + wobble) * 10) / 10,
      soh_pct: Math.round((b.soh_pct + (N - 1 - i) * 0.12) * 10) / 10,
    };
  });
};

export const alerts = [
  { id: 1, battery_id: 3, message: "Rapid temperature rise detected", risk_level: "high", status: "open", created_at: hoursAgo(0.4) },
  { id: 2, battery_id: 8, message: "Sustained high temperature with low state of health", risk_level: "high", status: "open", created_at: hoursAgo(2) },
  { id: 3, battery_id: 2, message: "Temperature above 48°C", risk_level: "medium", status: "open", created_at: hoursAgo(5) },
  { id: 4, battery_id: 10, message: "Unusual temperature pattern flagged by anomaly detector", risk_level: "medium", status: "open", created_at: hoursAgo(9) },
  { id: 5, battery_id: 6, message: "Temperature above 48°C", risk_level: "medium", status: "confirmed", created_at: hoursAgo(30) },
  { id: 6, battery_id: 12, message: "Temperature trending upward", risk_level: "medium", status: "false_alarm", created_at: hoursAgo(52) },
];
