export const batteries = [
  { id: 1, model: "Pack A-100", soh_pct: 92, temperature_c: 31, risk_level: "low", is_anomaly: false },
  { id: 2, model: "Pack A-101", soh_pct: 74, temperature_c: 49, risk_level: "medium", is_anomaly: false },
  { id: 3, model: "Pack B-200", soh_pct: 66, temperature_c: 63, risk_level: "high", is_anomaly: true },
];

export const readingsFor = (id) =>
  Array.from({ length: 30 }, (_, i) => ({
    t: i,
    temperature_c: 28 + id * 3 + Math.sin(i / 3) * 3 + (id === 3 && i > 22 ? (i - 22) * 4 : 0),
    soh_pct: 95 - id * 4 - i * 0.05,
  }));

export const alerts = [
  { id: 1, battery_id: 3, message: "Rapid temperature rise detected", risk_level: "high", status: "open" },
  { id: 2, battery_id: 2, message: "Temperature above 48°C", risk_level: "medium", status: "open" },
];