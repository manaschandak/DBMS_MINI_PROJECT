import {
  batteries,
  readingsFor,
  alerts as mockAlerts,
} from "./mockData";

// ============================================================
// CONFIGURATION
// ============================================================

// Set VITE_USE_MOCK=false in .env to use the FastAPI backend.
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

const BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

// ============================================================
// HELPERS
// ============================================================

const wait = (value, ms = 350) =>
  new Promise((resolve) =>
    setTimeout(() => resolve(value), ms)
  );

const json = (response) => {
  if (!response.ok) {
    throw new Error(
      `Request failed (${response.status})`
    );
  }

  return response.json();
};

// GET request with JWT authentication
const get = (path) => {
  const token = localStorage.getItem("access_token");

  return fetch(BASE + path, {
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  }).then(json);
};

// POST request with JWT authentication
const post = (path, body) => {
  const token = localStorage.getItem("access_token");

  return fetch(BASE + path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",

      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
    body: JSON.stringify(body),
  }).then(json);
};

// PUT request with JWT authentication
const put = (path, body) => {
  const token = localStorage.getItem("access_token");

  return fetch(BASE + path, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",

      ...(token
        ? {
            Authorization: `Bearer ${token}`,
          }
        : {}),
    },
    body: JSON.stringify(body),
  }).then(json);
};

// DELETE request with JWT authentication
const del = (path) => {
  const token = localStorage.getItem("access_token");

  return fetch(BASE + path, {
    method: "DELETE",
    headers: token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {},
  }).then(json);
};

// ============================================================
// MOCK ALERT STORE
// ============================================================

const alertStore = mockAlerts.map((alert) => ({
  ...alert,
}));

// ============================================================
// API
// ============================================================

export const api = {
  // ==========================================================
  // BATTERIES
  // ==========================================================

  getBatteries: async () => {
    if (USE_MOCK) {
      return wait(batteries);
    }

    const batteryList = await get("/batteries");

    const predictions = await get("/predictions");

    const result = await Promise.all(
      batteryList.map(async (battery) => {
        let soh_pct = null;
        let temperature_c = null;

        // ----------------------------------------------------
        // Latest SOH
        // ----------------------------------------------------

        try {
          const aging = await get(
            `/batteries/${battery.battery_id}/aging/latest`
          );

          soh_pct = aging?.soh_pct ?? null;
        } catch (error) {
          console.error(
            `SOH failed for battery ${battery.battery_id}:`,
            error
          );
        }

        // ----------------------------------------------------
        // Latest temperature
        // ----------------------------------------------------

        try {
          const sensors = await get(
            `/batteries/${battery.battery_id}/sensors`
          );

          const temperatureSensors = sensors.filter(
            (sensor) =>
              sensor.sensor_type === "TEMPERATURE"
          );

          if (temperatureSensors.length > 0) {
            const sensorReadings =
              await Promise.all(
                temperatureSensors.map(
                  async (sensor) => {
                    try {
                      const response = await get(
                        `/sensors/${sensor.sensor_id}/readings`
                      );

                      return (
                        response?.readings ?? []
                      );
                    } catch (error) {
                      console.error(
                        `Readings failed for sensor ${sensor.sensor_id}:`,
                        error
                      );

                      return [];
                    }
                  }
                )
              );

            const allReadings =
              sensorReadings.flat();

            if (allReadings.length > 0) {
              allReadings.sort(
                (a, b) =>
                  new Date(b.recorded_at) -
                  new Date(a.recorded_at)
              );

              temperature_c =
                allReadings[0]
                  ?.temperature_c ?? null;
            }
          }
        } catch (error) {
          console.error(
            `Temperature failed for battery ${battery.battery_id}:`,
            error
          );
        }

        // ----------------------------------------------------
        // Thermal prediction
        // ----------------------------------------------------

        const batteryPredictions =
          predictions.filter(
            (prediction) =>
              prediction.battery_id ===
              battery.battery_id
          );

        const thermalPrediction =
          batteryPredictions.find(
            (prediction) =>
              prediction.risk_type === "THERMAL"
          );

        const risk_level =
          thermalPrediction?.final_risk_level
            ?.toLowerCase() ?? "unknown";

        return {
          ...battery,
          soh_pct,
          temperature_c,
          risk_level,
        };
      })
    );

    console.log(
      "Dashboard battery data:",
      result
    );

    return result;
  },

  // ==========================================================
  // BATTERY SENSORS
  // ==========================================================

  getSensors: (batteryId) =>
    get(`/batteries/${batteryId}/sensors`),

  // ==========================================================
  // SENSOR READINGS
  // ==========================================================

  getSensorReadings: (sensorId) =>
    get(`/sensors/${sensorId}/readings`),

  // ==========================================================
  // BATTERY AGING
  // ==========================================================

  getAgingLatest: (batteryId) =>
    get(
      `/batteries/${batteryId}/aging/latest`
    ),

  // ==========================================================
  // OLD READINGS METHOD
  // Kept for compatibility with older components.
  // BatteryDetail no longer depends on this.
  // ==========================================================

  getReadings: (id) =>
    USE_MOCK
      ? wait(readingsFor(id))
      : get(`/batteries/${id}/readings`),

  // ==========================================================
  // PREDICTIONS
  // ==========================================================

  getPredictions: () =>
    USE_MOCK
      ? wait([])
      : get("/predictions"),

  // ==========================================================
  // ANOMALIES
  // ==========================================================

  getAnomalies: () =>
    USE_MOCK
      ? wait([])
      : get("/anomalies"),

  // ==========================================================
  // RECOMMENDATIONS
  // ==========================================================

  getRecommendations: () =>
    USE_MOCK
      ? wait([])
      : get("/recommendations"),

  // ==========================================================
  // ALERTS
  // ==========================================================

  getAlerts: () =>
    USE_MOCK
      ? wait(
          alertStore.map((alert) => ({
            ...alert,
          }))
        )
      : get("/alerts"),

  // ==========================================================
  // MODEL PERFORMANCE
  // ==========================================================

  getModelPerformance: () =>
    USE_MOCK
      ? wait([])
      : get("/model-performance"),

  // ==========================================================
  // ANALYTICS
  // ==========================================================

  getAnalyticsDashboard: () =>
    USE_MOCK
      ? wait(null)
      : get("/analytics/dashboard"),

  getAnalyticsBatteries: () =>
    USE_MOCK
      ? wait([])
      : get("/analytics/batteries"),

  getAnalyticsOpenAlerts: () =>
    USE_MOCK
      ? wait([])
      : get("/analytics/open-alerts"),

  getChemistryComparison: () =>
    USE_MOCK
      ? wait([])
      : get("/analytics/chemistry-comparison"),

  getManufacturerComparison: () =>
    USE_MOCK
      ? wait([])
      : get("/analytics/manufacturer-comparison"),

  getModelAccuracy: () =>
    USE_MOCK
      ? wait([])
      : get("/analytics/model-accuracy"),

  // ==========================================================
  // ADMIN
  // ==========================================================

  adminCheck: () =>
    USE_MOCK
      ? wait({ ok: true })
      : get("/auth/admin-check"),

  // ==========================================================
  // FEEDBACK
  // ==========================================================

  sendFeedback: (alertId, verdict) => {
    if (USE_MOCK) {
      const alert = alertStore.find(
        (item) => item.id === alertId
      );

      if (alert) {
        alert.status = verdict;
      }

      return wait(
        { ok: true },
        250
      );
    }

    const token =
      localStorage.getItem("access_token");

    return fetch(
      `${BASE}/alerts/${alertId}/feedback`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          ...(token
            ? {
                Authorization: `Bearer ${token}`,
              }
            : {}),
        },

        body: JSON.stringify({
          verdict,
        }),
      }
    ).then(json);
  },

  // ==========================================================
  // GENERATE RECOMMENDATIONS
  // ==========================================================

  generateRecommendations: (batteryId) =>
    post("/recommendations/generate", {
      battery_id: batteryId,
    }),

  // ==========================================================
  // DETECT ANOMALIES
  // ==========================================================

  detectAnomalies: (batteryId) =>
    post("/anomalies/detect", {
      battery_id: batteryId,
    }),

  // ==========================================================
  // CREATE SENSOR READING
  // ==========================================================

  addReading: (data) =>
    post("/readings", data),

  // ==========================================================
  // CREATE AGING RECORD
  // ==========================================================

  addAging: (batteryId, data) =>
    post(
      `/batteries/${batteryId}/aging`,
      data
    ),

  // ==========================================================
  // CREATE SENSOR
  // ==========================================================

  addSensor: (batteryId, data) =>
    post(
      `/batteries/${batteryId}/sensors`,
      data
    ),

  // ==========================================================
  // CREATE BATTERY
  // ==========================================================

  addBattery: (data) =>
    post("/batteries", data),

  // ==========================================================
  // UPDATE BATTERY
  // ==========================================================

  updateBattery: (batteryId, data) =>
    put(
      `/batteries/${batteryId}`,
      data
    ),

  // ==========================================================
  // DELETE BATTERY
  // ==========================================================

  deleteBattery: (batteryId) =>
    del(`/batteries/${batteryId}`),
};