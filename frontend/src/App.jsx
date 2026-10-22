
import { useState } from "react";
import {
  Wind,
  LayoutDashboard,
  ChartNoAxesCombined,
  CalendarDays,
  Activity,
  AlertTriangle,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import "./App.css";

const sampleData = [
  { time: "06:00", aqi: 82 },
  { time: "07:00", aqi: 96 },
  { time: "08:00", aqi: 121 },
  { time: "09:00", aqi: 148 },
  { time: "10:00", aqi: 137 },
  { time: "11:00", aqi: 114 },
  { time: "12:00", aqi: 91 },
  { time: "13:00", aqi: 105 },
  { time: "14:00", aqi: 126 },
  { time: "15:00", aqi: 110 },
  { time: "16:00", aqi: 88 },
  { time: "17:00", aqi: 76 },
];

const MIN_TIME = 6 * 60;
const MAX_TIME = 18 * 60;
const TIME_STEP = 5;

function formatTime(minutes) {
  const hour = Math.floor(minutes / 60);
  const minute = minutes % 60;
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function getCategory(aqi) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  if (aqi <= 500) return "Severe";
  return "Invalid";
}

export default function App() {
  const [date, setDate] = useState("2019-07-15");
  const [duration, setDuration] = useState(60);
  const [timeRange, setTimeRange] = useState([360, 1080]);
  const [healthConsiderations, setHealthConsiderations] = useState(false);
  const [notice, setNotice] = useState("");

  const averageAQI = Math.round(
    sampleData.reduce((sum, item) => sum + item.aqi, 0) /
      sampleData.length
  );

  const startPercent =
    ((timeRange[0] - MIN_TIME) / (MAX_TIME - MIN_TIME)) * 100;
  const endPercent =
    ((timeRange[1] - MIN_TIME) / (MAX_TIME - MIN_TIME)) * 100;

  function updateTimeRange(index, value) {
    const nextValue = Number(value);

    setTimeRange((previous) => {
      const next = [...previous];

      if (index === 0) {
        next[0] = Math.min(nextValue, previous[1] - TIME_STEP);
      } else {
        next[1] = Math.max(nextValue, previous[0] + TIME_STEP);
      }

      return next;
    });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Wind size={22} strokeWidth={1.8} />
          <div>
            <strong>School AirSafe</strong>
            <span>AIR QUALITY PLANNER</span>
          </div>
        </div>

        <p className="nav-heading">WORKSPACE</p>

        <button className="nav-item active">
          <LayoutDashboard size={17} />
          Dashboard
        </button>

        <button
          className="nav-item"
          onClick={() =>
            document
              .getElementById("aqi-trends")
              ?.scrollIntoView({ behavior: "smooth" })
          }
        >
          <ChartNoAxesCombined size={17} />
          AQI trends
        </button>

        <div className="sidebar-footer">
          School air quality planning
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <p className="breadcrumb">WORKSPACE / DASHBOARD</p>
            <h1>School Activity Planner</h1>
            <p className="subtitle">
              Review historical air quality and plan outdoor activities.
            </p>
          </div>

          <div className="location-label">
            <span className="location-dot" />
            Delhi, India
          </div>
        </header>

        <section className="panel planner-panel">
          <div className="section-title">
            <CalendarDays size={18} />
            <div>
              <h2>Activity planning</h2>
              <p>Specify the schedule and group requirements.</p>
            </div>
          </div>

          <div className="form-grid">
            <div className="field">
              <label htmlFor="date">Planning date</label>
              <input
                id="date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>

            <div className="field duration-field">
              <div className="label-row">
                <label htmlFor="duration">Activity duration</label>
                <output>{duration} minutes</output>
              </div>

              <input
                className="range-input"
                id="duration"
                type="range"
                min="30"
                max="240"
                step="5"
                value={duration}
                style={{
                  "--range-progress": `${((duration - 30) / 210) * 100}%`,
                }}
                onChange={(e) => setDuration(Number(e.target.value))}
              />

              <div className="range-labels">
                <span>30 min</span>
                <span>4 hours</span>
              </div>
            </div>
          </div>

          <div className="time-section">
            <div className="label-row time-heading">
              <div>
                <label>Available time window</label>
                <p className="field-description">
                  Drag the handles to select school hours.
                </p>
              </div>

              <strong className="time-value">
                {formatTime(timeRange[0])} – {formatTime(timeRange[1])}
              </strong>
            </div>

            <div className="dual-range">
              <div className="range-track" />

              <div
                className="range-selected"
                style={{
                  left: `${startPercent}%`,
                  width: `${endPercent - startPercent}%`,
                }}
              />

              <input
                aria-label="Available start time"
                className="range-handle"
                type="range"
                min={MIN_TIME}
                max={MAX_TIME}
                step={TIME_STEP}
                value={timeRange[0]}
                onChange={(e) => updateTimeRange(0, e.target.value)}
                style={{ zIndex: 3 }}
              />

              <input
                aria-label="Available end time"
                className="range-handle"
                type="range"
                min={MIN_TIME}
                max={MAX_TIME}
                step={TIME_STEP}
                value={timeRange[1]}
                onChange={(e) => updateTimeRange(1, e.target.value)}
                style={{ zIndex: 4 }}
              />
            </div>

            <div className="time-labels">
              <span>06:00</span>
              <span>09:00</span>
              <span>12:00</span>
              <span>15:00</span>
              <span>18:00</span>
            </div>
          </div>

          <div className="health-section">
            <label className="checkbox-row" htmlFor="health">
              <input
                id="health"
                type="checkbox"
                checked={healthConsiderations}
                onChange={(e) =>
                  setHealthConsiderations(e.target.checked)
                }
              />

              <span className="custom-checkbox" />

              <span className="checkbox-copy">
                <strong>Health considerations</strong>
                <small>
                  Apply the project's stricter AQI threshold for children
                  with asthma or other respiratory sensitivities.
                </small>
              </span>
            </label>
          </div>

          <div className="form-actions">
            <button
              className="primary-button"
              onClick={() =>
                setNotice(
                  "The interface is ready, but AQI recommendations have not been calculated because the backend is not connected."
                )
              }
            >
              <Activity size={16} />
              Check activity window
            </button>

            <span className="form-note">
              {formatTime(timeRange[0])}–{formatTime(timeRange[1])}
              {" · "}{duration} min
              {healthConsiderations ? " · Health-aware" : ""}
            </span>
          </div>

          {notice && (
            <div className="inline-notice" role="status">
              <AlertTriangle size={17} />
              <span>{notice}</span>
            </div>
          )}
        </section>

        <section className="overview-section">
          <div className="section-heading">
            <h2>Air quality overview</h2>
            <span>Illustrative data</span>
          </div>

          <div className="metrics-grid">
            <div className="panel metric-card">
              <p>Average AQI</p>
              <div className="metric-number">{averageAQI}</div>
              <span>Sample readings</span>
            </div>

            <div className="panel metric-card">
              <p>AQI category</p>
              <div className="metric-category">
                {getCategory(averageAQI)}
              </div>
              <span>Based on average AQI</span>
            </div>

            <div className="panel metric-card">
              <p>Planning date</p>
              <div className="metric-date">{date}</div>
              <span>Selected date</span>
            </div>
          </div>
        </section>

        <section className="panel chart-panel" id="aqi-trends">
          <div className="chart-header">
            <div>
              <h2>Hourly AQI trend</h2>
              <p>Hourly air quality readings throughout the day.</p>
            </div>
            <span className="chart-unit">AQI</span>
          </div>

          <div className="chart-container">
            <ResponsiveContainer width="100%" height={270}>
              <AreaChart
                data={sampleData}
                margin={{ top: 12, right: 12, left: -18, bottom: 0 }}
              >
                <CartesianGrid
                  stroke="#e8ebef"
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11, fill: "#667085" }}
                  axisLine={{ stroke: "#dfe3e8" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#667085" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="aqi"
                  name="AQI"
                  stroke="#64748b"
                  strokeWidth={2}
                  fill="#cbd5e1"
                  fillOpacity={0.28}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <p className="chart-disclaimer">
            Demonstration values only. Real historical readings will be
            shown after data integration.
          </p>
        </section>

        <footer className="page-footer">
          School AirSafe · Educational planning tool
        </footer>
      </main>
    </div>
  );
}
