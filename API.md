# API contract

Base URL: http://localhost:8000 (CORS allowed for http://localhost:5173)

GET  /batteries
  -> [{ id, model, soh_pct, temperature_c, risk_level, is_anomaly }]

GET  /batteries/{id}/readings
  -> [{ t, temperature_c, soh_pct }]

GET  /alerts
  -> [{ id, battery_id, message, risk_level, status }]

POST /alerts/{id}/feedback
  body: { "verdict": "confirmed" | "false_alarm" }

POST /readings
  body: { battery_id, cycle_count, temperature_c, voltage_v, current_a,
          soh_pct, internal_resistance_mohm, temp_rise_rate }
  -> { risk_level, risk_score, is_anomaly, anomaly_score }

Backend calls `predict(reading)` from ml/predict.py.
risk_level is "low" | "medium" | "high". Alert status is "open" | "confirmed" | "false_alarm".