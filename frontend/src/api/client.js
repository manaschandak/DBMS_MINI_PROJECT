import { batteries, readingsFor, alerts } from "./mockData";

const USE_MOCK = true;
const BASE = "http://localhost:8000";
const get = (p) => fetch(BASE + p).then((r) => r.json());

export const api = {
  getBatteries: () => (USE_MOCK ? Promise.resolve(batteries) : get("/batteries")),
  getReadings: (id) => (USE_MOCK ? Promise.resolve(readingsFor(id)) : get(`/batteries/${id}/readings`)),
  getAlerts: () => (USE_MOCK ? Promise.resolve(alerts) : get("/alerts")),
  sendFeedback: (alertId, verdict) =>
    USE_MOCK
      ? Promise.resolve({ ok: true })
      : fetch(`${BASE}/alerts/${alertId}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ verdict }),
        }).then((r) => r.json()),
};