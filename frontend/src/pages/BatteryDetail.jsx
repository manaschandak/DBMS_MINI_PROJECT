import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";

import { api } from "../api/client";
import { useFetch } from "../hooks/useFetch";
import RiskBadge from "../components/RiskBadge";
import Stat from "../components/Stat";
import { ErrorState, Skeleton } from "../components/PageState";
import {
  CRIT_C,
  WARN_C,
  tempStatus,
  healthStatus,
  timeAgo,
} from "../lib/thresholds";

const RANGES = [
  ["10", "Last 10"],
  ["20", "Last 20"],
  ["all", "All"],
];

function ChartTip({ active, payload, label, unit, last }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="tip">
      <div className="muted">
        {label === last
          ? "Latest reading"
          : `${last - label} readings ago`}
      </div>

      <b>
        {payload[0].value}
        {unit}
      </b>
    </div>
  );
}

export default function BatteryDetail() {
  const { id } = useParams();
  const [range, setRange] = useState("all");

  const { data, loading, error, reload } = useFetch(
    async () => {
      const batteryId = Number(id);

      // -------------------------------------------------------
      // Get battery list
      // -------------------------------------------------------
      const batteries = await api.getBatteries();

      const battery = batteries.find(
        (b) => b.battery_id === batteryId
      );

      if (!battery) {
        return {
          battery: null,
          readings: [],
          alerts: [],
          predictions: [],
          aging: null,
          sensors: [],
        };
      }

      // -------------------------------------------------------
      // Get sensors, aging, predictions and alerts
      // -------------------------------------------------------
      const [
        sensors,
        aging,
        predictions,
        alerts,
      ] = await Promise.all([
        api.getSensors(batteryId).catch(() => []),

        api.getAgingLatest(batteryId).catch(() => null),

        api.getPredictions().catch(() => []),

        api.getAlerts().catch(() => []),
      ]);

      // -------------------------------------------------------
      // Find temperature sensors
      // -------------------------------------------------------
      const temperatureSensors = sensors.filter(
        (sensor) => sensor.sensor_type === "TEMPERATURE"
      );

      // -------------------------------------------------------
      // Get readings from every temperature sensor
      // -------------------------------------------------------
      const sensorReadings = await Promise.all(
        temperatureSensors.map(async (sensor) => {
          try {
            const response = await api.getSensorReadings(
              sensor.sensor_id
            );

            return response?.readings ?? [];
          } catch (error) {
            console.error(
              `Failed to get readings for sensor ${sensor.sensor_id}`,
              error
            );

            return [];
          }
        })
      );

      const allReadings = sensorReadings.flat();

      // -------------------------------------------------------
      // Sort oldest → newest
      // -------------------------------------------------------
      allReadings.sort(
        (a, b) =>
          new Date(a.recorded_at) -
          new Date(b.recorded_at)
      );

      // -------------------------------------------------------
      // Create chart data
      // -------------------------------------------------------
      const readings = allReadings.map((reading, index) => ({
        ...reading,
        t: index,
        soh_pct: aging?.soh_pct ?? null,
      }));

      // -------------------------------------------------------
      // Battery-specific alerts
      // -------------------------------------------------------
      const batteryAlerts = alerts.filter(
        (alert) =>
          Number(alert.battery_id) === batteryId
      );

      // -------------------------------------------------------
      // Battery-specific predictions
      // -------------------------------------------------------
      const batteryPredictions = predictions.filter(
        (prediction) =>
          Number(prediction.battery_id) === batteryId
      );

      return {
        battery,
        readings,
        alerts: batteryAlerts,
        predictions: batteryPredictions,
        aging,
        sensors,
      };
    },
    [id]
  );

  // ---------------------------------------------------------
  // Loading / error
  // ---------------------------------------------------------

  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={reload}
      />
    );
  }

  if (loading && !data) {
    return (
      <>
        <Link to="/" className="back">
          ← Back to fleet
        </Link>

        <Skeleton rows={4} />
      </>
    );
  }

  const {
    battery,
    readings,
    alerts,
    predictions,
    aging,
    sensors,
  } = data;

  // ---------------------------------------------------------
  // Battery not found
  // ---------------------------------------------------------

  if (!battery) {
    return (
      <div className="state">
        <h2>Battery not found</h2>

        <p className="muted">
          No battery with ID {id}.
        </p>

        <Link to="/" className="btn">
          Back to fleet
        </Link>
      </div>
    );
  }

  // ---------------------------------------------------------
  // Current / displayed readings
  // ---------------------------------------------------------

  const shown =
    range === "all"
      ? readings
      : readings.slice(-Number(range));

  const last =
    readings.length > 0
      ? readings.length - 1
      : 0;

  const latestTemperature =
    readings.length > 0
      ? readings[readings.length - 1].temperature_c
      : battery.temperature_c ?? null;

  const temperatureValues = shown
    .map((r) => r.temperature_c)
    .filter((value) => value != null);

  const peak =
    temperatureValues.length > 0
      ? Math.max(...temperatureValues)
      : null;

  // ---------------------------------------------------------
  // Risk
  // ---------------------------------------------------------

  const thermalPrediction = predictions.find(
    (prediction) =>
      prediction.risk_type === "THERMAL"
  );

  const riskLevel =
    thermalPrediction?.final_risk_level?.toLowerCase() ??
    battery.risk_level ??
    "unknown";

  // ---------------------------------------------------------
  // SOH
  // ---------------------------------------------------------

  const soh =
    aging?.soh_pct ??
    battery.soh_pct ??
    null;

  // ---------------------------------------------------------
  // Temperature status
  // ---------------------------------------------------------

  const ts =
    latestTemperature != null
      ? tempStatus(latestTemperature)
      : {
          key: undefined,
          label: "No temperature data",
        };

  // ---------------------------------------------------------
  // Open alerts
  // ---------------------------------------------------------

  const openAlerts = alerts.filter(
    (alert) =>
      alert.status === "open" ||
      alert.status === "OPEN"
  );

  // ---------------------------------------------------------
  // Chart tick formatter
  // ---------------------------------------------------------

  const tickFmt = (t) =>
    t === last
      ? "now"
      : `-${last - t}`;

  return (
    <div>
      {/* --------------------------------------------------- */}
      {/* BACK */}
      {/* --------------------------------------------------- */}

      <Link to="/" className="back">
        ← Back to fleet
      </Link>

      {/* --------------------------------------------------- */}
      {/* HEADER */}
      {/* --------------------------------------------------- */}

      <div className="head">
        <div>
          <h1>
            {battery.serial_number ??
              battery.battery_id}
          </h1>

          <div className="muted">
            {battery.manufacturer_name ?? "—"} ·{" "}
            {battery.chemistry_code ?? "—"} ·{" "}
            {battery.battery_type ?? "—"}
          </div>
        </div>

        <RiskBadge level={riskLevel} />
      </div>

      {/* --------------------------------------------------- */}
      {/* STATS */}
      {/* --------------------------------------------------- */}

      <div className="stats">
        <Stat
          label="State of health"
          value={
            soh != null
              ? `${soh}%`
              : "—"
          }
          tone={
            soh != null
              ? healthStatus(soh)
              : undefined
          }
          sub={
            soh == null
              ? "No aging data"
              : soh >= 80
                ? "good"
                : soh >= 70
                  ? "degrading"
                  : "poor"
          }
        />

        <Stat
          label="Temperature now"
          value={
            latestTemperature != null
              ? `${latestTemperature}°C`
              : "—"
          }
          tone={ts.key}
          sub={ts.label}
        />

        <Stat
          label="Peak in view"
          value={
            peak != null
              ? `${peak.toFixed(1)}°C`
              : "—"
          }
          tone={
            peak != null
              ? tempStatus(peak).key
              : undefined
          }
          sub={
            peak != null
              ? tempStatus(peak).label
              : "No readings"
          }
        />

        <Stat
          label="Open alerts"
          value={openAlerts.length}
          tone={
            openAlerts.length
              ? "high"
              : undefined
          }
          sub={
            openAlerts.length
              ? "needs review"
              : "all clear"
          }
        />
      </div>

      {/* --------------------------------------------------- */}
      {/* BATTERY INFORMATION */}
      {/* --------------------------------------------------- */}

      <div className="panel">
        <h2>Battery information</h2>

        <div className="stats">
          <Stat
            label="Battery ID"
            value={battery.battery_id}
          />

          <Stat
            label="Chemistry"
            value={
              battery.chemistry_code ?? "—"
            }
          />

          <Stat
            label="Capacity"
            value={
              battery.nominal_capacity_ah != null
                ? `${battery.nominal_capacity_ah} Ah`
                : "—"
            }
          />

          <Stat
            label="Status"
            value={
              battery.status ?? "—"
            }
          />
        </div>
      </div>

      {/* --------------------------------------------------- */}
      {/* TEMPERATURE CHART */}
      {/* --------------------------------------------------- */}

      <div className="panel">
        <div className="panel-head">
          <h2>Temperature (°C)</h2>

          <div
            className="seg small"
            role="group"
            aria-label="Time range"
          >
            {RANGES.map(([key, label]) => (
              <button
                key={key}
                className={
                  range === key ? "on" : ""
                }
                aria-pressed={
                  range === key
                }
                onClick={() =>
                  setRange(key)
                }
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {shown.length === 0 ? (
          <div className="state">
            <h2>No temperature readings</h2>

            <p className="muted">
              This battery currently has no
              temperature sensor readings available.
            </p>
          </div>
        ) : (
          <>
            <ResponsiveContainer
              width="100%"
              height={280}
            >
              <AreaChart
                data={shown}
                margin={{
                  top: 10,
                  right: 12,
                  left: -12,
                  bottom: 0,
                }}
              >
                <defs>
                  <linearGradient
                    id="tfill"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#14212b"
                      stopOpacity={0.22}
                    />

                    <stop
                      offset="100%"
                      stopColor="#14212b"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  stroke="#e6ebee"
                  vertical={false}
                />

                <XAxis
                  dataKey="t"
                  tickLine={false}
                  tickFormatter={tickFmt}
                />

                <YAxis
                  domain={[20, 80]}
                  tickLine={false}
                  axisLine={false}
                />

                <Tooltip
                  content={
                    <ChartTip
                      unit="°C"
                      last={last}
                    />
                  }
                />

                <ReferenceLine
                  y={WARN_C}
                  stroke="#c98a0b"
                  strokeDasharray="4 4"
                  label={{
                    value: `Warning ${WARN_C}`,
                    fill: "#8a5d00",
                    fontSize: 12,
                    position:
                      "insideTopLeft",
                  }}
                />

                <ReferenceLine
                  y={CRIT_C}
                  stroke="#c23b2e"
                  strokeDasharray="4 4"
                  label={{
                    value: `Critical ${CRIT_C}`,
                    fill: "#9b2a20",
                    fontSize: 12,
                    position:
                      "insideTopLeft",
                  }}
                />

                <Area
                  type="monotone"
                  dataKey="temperature_c"
                  stroke="#14212b"
                  strokeWidth={2}
                  fill="url(#tfill)"
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </AreaChart>
            </ResponsiveContainer>

            <div className="axis-note muted">
              Readings ago
            </div>
          </>
        )}
      </div>

      {/* --------------------------------------------------- */}
      {/* SOH */}
      {/* --------------------------------------------------- */}

      <div className="panel">
        <h2>State of health (%)</h2>

        {soh == null ? (
          <p className="muted">
            No aging data is available for this battery.
          </p>
        ) : (
          <ResponsiveContainer
            width="100%"
            height={220}
          >
            <LineChart
              data={shown}
              margin={{
                top: 10,
                right: 12,
                left: -12,
                bottom: 0,
              }}
            >
              <CartesianGrid
                stroke="#e6ebee"
                vertical={false}
              />

              <XAxis
                dataKey="t"
                tickLine={false}
                tickFormatter={tickFmt}
              />

              <YAxis
                domain={["auto", "auto"]}
                tickLine={false}
                axisLine={false}
              />

              <Tooltip
                content={
                  <ChartTip
                    unit="%"
                    last={last}
                  />
                }
              />

              <Line
                type="monotone"
                dataKey="soh_pct"
                stroke="#1f8a70"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* --------------------------------------------------- */}
      {/* AGING INFORMATION */}
      {/* --------------------------------------------------- */}

      {aging && (
        <div className="panel">
          <h2>Aging information</h2>

          <div className="stats">
            <Stat
              label="Cycle count"
              value={
                aging.cycle_count ?? "—"
              }
            />

            <Stat
              label="Calendar age"
              value={
                aging.calendar_age_days != null
                  ? `${aging.calendar_age_days} days`
                  : "—"
              }
            />

            <Stat
              label="Capacity"
              value={
                aging.capacity_ah != null
                  ? `${aging.capacity_ah} Ah`
                  : "—"
              }
            />

            <Stat
              label="Internal resistance"
              value={
                aging.internal_resistance_mohm != null
                  ? `${aging.internal_resistance_mohm} mΩ`
                  : "—"
              }
            />
          </div>
        </div>
      )}

      {/* --------------------------------------------------- */}
      {/* SENSORS */}
      {/* --------------------------------------------------- */}

      <div className="panel">
        <h2>Sensors</h2>

        {sensors.length === 0 ? (
          <p className="muted">
            No sensors are registered for this battery.
          </p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Sensor</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {sensors.map((sensor) => (
                  <tr
                    key={sensor.sensor_id}
                  >
                    <td>
                      #{sensor.sensor_id}
                    </td>

                    <td>
                      {sensor.sensor_type ??
                        "—"}
                    </td>

                    <td>
                      {sensor.location ??
                        "—"}
                    </td>

                    <td>
                      {sensor.is_active
                        ? "Active"
                        : "Inactive"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* --------------------------------------------------- */}
      {/* ALERTS */}
      {/* --------------------------------------------------- */}

      <div className="panel">
        <div className="panel-head">
          <h2>Alerts for this pack</h2>

          <Link
            to="/alerts"
            className="muted"
          >
            All alerts →
          </Link>
        </div>

        {alerts.length === 0 ? (
          <p className="muted">
            No alerts for this pack.
          </p>
        ) : (
          <ul className="mini-alerts">
            {alerts.map((alert, index) => (
              <li
                key={
                  alert.alert_id ??
                  alert.id ??
                  index
                }
              >
                <RiskBadge
                  level={
                    alert.risk_level ??
                    alert.severity ??
                    "unknown"
                  }
                />

                <span className="grow">
                  {alert.message ??
                    alert.description ??
                    "Battery alert"}
                </span>

                <span className="muted">
                  {alert.status === "open"
                    ? timeAgo(
                        alert.created_at
                      ) || "open"
                    : alert.status ===
                        "confirmed"
                      ? "Confirmed"
                      : alert.status ===
                          "false_alarm"
                        ? "False alarm"
                        : alert.status ??
                          "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}