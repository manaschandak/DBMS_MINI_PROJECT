import { batteries, readingsFor, alerts as mockAlerts } from "./mockData";

// Flip with VITE_USE_MOCK=false (and optionally VITE_API_URL) when the FastAPI backend is ready.
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const wait = (v, ms = 350) => new Promise((res) => setTimeout(() => res(v), ms));
const json = (r) => {
  if (!r.ok) throw new Error(`Request failed (${r.status})`);
  return r.json();
};
const get = (p) => fetch(BASE + p).then(json);

// Mock alerts live in memory so feedback sticks while you click around.
const alertStore = mockAlerts.map((a) => ({ ...a }));

export const api = {
  getBatteries: () => (USE_MOCK ? wait(batteries) : get("/batteries")),
  getReadings: (id) => (USE_MOCK ? wait(readingsFor(id)) : get(`/batteries/${id}/readings`)),
  getAlerts: () => (USE_MOCK ? wait(alertStore.map((a) => ({ ...a }))) : get("/alerts")),
  sendFeedback: (alertId, verdict) => {
    if (USE_MOCK) {
      const a = alertStore.find((x) => x.id === alertId);
      if (a) a.status = verdict;
      return wait({ ok: true }, 250);
    }
    return fetch(`${BASE}/alerts/${alertId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verdict }),
    }).then(json);
  },
};
