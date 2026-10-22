
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CalendarDays,
  Clock3,
  HeartPulse,
  RefreshCw,
  ShieldCheck,
  Wind,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  LayoutGrid,
  ChevronLeft,
  ChevronRight,
  CalendarClock,
  MapPin,
  Route,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const MIN_TIME = 360;
const MAX_TIME = 1080;

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function formatTime(value) {
  if (typeof value === "number") {
    return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
  }
  return String(value ?? "—");
}

function aqiColor(value) {
  const aqi = Number(value);

  if (value == null || !Number.isFinite(aqi)) return "#e8edf2";
  if (aqi <= 50) return "#22a447";
  if (aqi <= 100) return "#86b817";
  if (aqi <= 200) return "#e9c52c";
  if (aqi <= 300) return "#f18b36";
  if (aqi <= 400) return "#e44848";

  return "#8f1728";
}

function aqiCategory(value) {
  if (value == null || !Number.isFinite(Number(value))) return "No data";

  const aqi = Number(value);

  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";

  return "Severe";
}

function displayAQI(value) {
  return value == null || !Number.isFinite(Number(value))
    ? "—"
    : Math.round(Number(value));
}

function formatWindow(item) {
  if (!item) return "—";

  const start =
    item.start_time ??
    item.start ??
    item.start_datetime;

  const end =
    item.end_time ??
    item.end ??
    item.end_datetime;

  if (typeof start === "number" && typeof end === "number") {
    return `${formatTime(start)} – ${formatTime(end)}`;
  }

  if (start != null && end != null) {
    return `${start} – ${end}`;
  }

  return item.time ?? "Window details unavailable";
}

function worstAQI(item) {
  return (
    item?.worst_aqi ??
    item?.max_aqi ??
    item?.worst ??
    item?.maximum_aqi ??
    null
  );
}

function averageAQI(item) {
  return (
    item?.average_aqi ??
    item?.avg_aqi ??
    item?.mean_aqi ??
    item?.average ??
    null
  );
}

function Metric({ label, value, subtitle, icon: Icon }) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span>{label}</span>
        <Icon size={19} />
      </div>

      <div className="metric-value">{value}</div>
      <div className="metric-subtitle">{subtitle}</div>
    </div>
  );
}

/* Hourly AQI strip */

function HourlyAQIStrip({ readings }) {
  const hours = useMemo(() => {
    const byHour = new Map();

    readings.forEach((reading) => {
      const rawTime =
        reading.time ??
        reading.timestamp ??
        reading.datetime ??
        "";

      const match = String(rawTime).match(
        /(?:T|\s)?(\d{1,2}):\d{2}/
      );

      const hour = match ? Number(match[1]) : null;

      if (hour != null && hour >= 0 && hour <= 23) {
        byHour.set(hour, reading);
      }
    });

    return Array.from({ length: 24 }, (_, hour) => ({
      hour,
      reading: byHour.get(hour) ?? null,
    }));
  }, [readings]);

  return (
    <section className="panel hourly-panel">
      <div className="panel-heading">
        <div className="section-icon">
          <Clock3 size={19} />
        </div>

        <div>
          <h2>Hourly AQI</h2>
          <p>Each block represents one hour for the selected day.</p>
        </div>
      </div>

      {readings.length === 0 ? (
        <div className="hourly-empty">
          Submit a planning request to see this day's hourly AQI.
        </div>
      ) : (
        <>
          <div className="hour-strip">
            {hours.map(({ hour, reading }) => {
              const value = reading?.aqi;

              const available =
                value != null &&
                Number.isFinite(Number(value));

              return (
                <div
                  className="hour-cell"
                  key={hour}
                  title={`${String(hour).padStart(2, "0")}:00 · ${
                    available
                      ? `AQI ${displayAQI(value)} · ${aqiCategory(value)}`
                      : "No data"
                  }`}
                >
                  <div
                    className={`hour-color ${
                      available ? "" : "hour-missing"
                    }`}
                    style={{
                      backgroundColor: available
                        ? aqiColor(value)
                        : undefined,
                    }}
                  />

                  <span className="hour-label">
                    {String(hour).padStart(2, "0")}
                  </span>

                  <strong>
                    {available ? displayAQI(value) : "—"}
                  </strong>
                </div>
              );
            })}
          </div>

          <div className="aqi-legend">
            {[
              ["#22a447", "Good 0–50"],
              ["#86b817", "Satisfactory 51–100"],
              ["#e9c52c", "Moderate 101–200"],
              ["#f18b36", "Poor 201–300"],
              ["#e44848", "Very poor 301–400"],
              ["#8f1728", "Severe 401–500"],
              ["#e8edf2", "No data"],
            ].map(([color, label]) => (
              <span className="legend-item" key={label}>
                <i style={{ backgroundColor: color }} />
                {label}
              </span>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

/* AQI calendar */

function AQICalendar({ selectedDate, onSelectDate, city }) {
  const selectedYear = Number(selectedDate.slice(0, 4));
  const selectedMonth = Number(selectedDate.slice(5, 7)) - 1;

  const [year, setYear] = useState(selectedYear);
  const [month, setMonth] = useState(selectedMonth);
  const [view, setView] = useState("year");
  const [calendarData, setCalendarData] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCalendar() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          `${API_URL}/api/calendar?year=${year}&city=${encodeURIComponent(city)}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Could not load calendar data."
          );
        }

        const next = {};

        (data.days ?? []).forEach((day) => {
          next[day.date] = day;
        });

        if (!cancelled) {
          setCalendarData(next);
        }
      } catch (err) {
        if (!cancelled) {
          setCalendarData({});
          setError(
            err.message || "Could not load the AQI calendar."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadCalendar();

    return () => {
      cancelled = true;
    };
  }, [year, city]);

  function changeYear(nextYear) {
    setYear(nextYear);

    onSelectDate(
      `${nextYear}-${String(month + 1).padStart(2, "0")}-01`
    );
  }

  function dateString(y, m, d) {
    return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  }

  function renderDay(date, compact = false) {
    const info = calendarData[date];
    const value = info?.aqi ?? null;
    const dayNumber = Number(date.slice(8, 10));
    const isSelected = selectedDate === date;

    return (
      <button
        key={date}
        type="button"
        className={`calendar-day ${
          compact ? "calendar-day-compact" : ""
        } ${
          isSelected ? "calendar-day-selected" : ""
        } ${
          info ? "" : "calendar-day-no-data"
        }`}
        style={{ "--day-color": aqiColor(value) }}
        title={`${date}: ${
          info
            ? `Daily maximum AQI ${info.aqi}, ${aqiCategory(info.aqi)}, ${info.readings} readings`
            : "No valid AQI data"
        }`}
        onClick={() => onSelectDate(date)}
        aria-label={`${date}, ${
          info ? `AQI ${info.aqi}` : "no data"
        }`}
      >
        <span>{dayNumber}</span>
        {!compact && info && <small>{info.aqi}</small>}
      </button>
    );
  }

  function renderMonthGrid(y, m, compact = false) {
    const firstDay = new Date(y, m, 1).getDay();
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const cells = [];

    for (let i = 0; i < firstDay; i++) {
      cells.push(
        <div
          className="calendar-blank"
          key={`blank-${y}-${m}-${i}`}
        />
      );
    }

    for (let day = 1; day <= daysInMonth; day++) {
      cells.push(
        renderDay(dateString(y, m, day), compact)
      );
    }

    return (
      <div
        className={`month-grid ${
          compact ? "month-grid-compact" : ""
        }`}
      >
        {["S", "M", "T", "W", "T", "F", "S"].map(
          (day, index) => (
            <span
              className="weekday-label"
              key={`${day}-${index}`}
            >
              {day}
            </span>
          )
        )}

        {cells}
      </div>
    );
  }

  function monthStats(m) {
    const prefix =
      `${year}-${String(m + 1).padStart(2, "0")}-`;

    const values = Object.entries(calendarData)
      .filter(([date]) => date.startsWith(prefix))
      .map(([, info]) => Number(info.aqi))
      .filter(Number.isFinite);

    return values.length
      ? { days: values.length, worst: Math.max(...values) }
      : { days: 0, worst: null };
  }

  return (
    <section className="panel calendar-panel" id="workspace">
      <div className="panel-heading calendar-heading">
        <div className="section-icon">
          <LayoutGrid size={19} />
        </div>

        <div>
          <h2>Workspace · AQI calendar</h2>
          <p>Explore daily pollution patterns across the year.</p>
        </div>
      </div>

      <div className="calendar-controls">
        <div className="calendar-year-controls">
          <button
            className="icon-button"
            aria-label="Previous year"
            onClick={() => changeYear(year - 1)}
          >
            <ChevronLeft size={17} />
          </button>

          <strong>{year}</strong>

          <button
            className="icon-button"
            aria-label="Next year"
            onClick={() => changeYear(year + 1)}
          >
            <ChevronRight size={17} />
          </button>
        </div>

        <div className="calendar-view-switch">
          <button
            className={view === "year" ? "selected" : ""}
            onClick={() => setView("year")}
          >
            Year
          </button>

          <button
            className={view === "month" ? "selected" : ""}
            onClick={() => setView("month")}
          >
            Month
          </button>
        </div>
      </div>

      {view === "month" && (
        <div className="month-picker">
          <label htmlFor="calendar-month">Month</label>

          <select
            id="calendar-month"
            value={month}
            onChange={(event) =>
              setMonth(Number(event.target.value))
            }
          >
            {MONTHS.map((name, index) => (
              <option value={index} key={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      )}

      {loading && (
        <div className="calendar-loading">
          <RefreshCw size={17} className="spin" />
          Loading daily AQI data…
        </div>
      )}

      {error && (
        <div className="error-message">
          <AlertTriangle size={17} />
          {error}
        </div>
      )}

      {!loading && !error && view === "year" && (
        <div className="year-grid">
          {MONTHS.map((name, index) => {
            const stats = monthStats(index);

            return (
              <div className="year-month" key={name}>
                <button
                  className="year-month-title"
                  onClick={() => {
                    setMonth(index);
                    setView("month");
                  }}
                >
                  <strong>{name}</strong>
                  <span>
                    {stats.days
                      ? `Peak ${stats.worst}`
                      : "Explore month"}
                  </span>
                </button>

                {renderMonthGrid(year, index, true)}
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && view === "month" && (
        <div className="single-month">
          <div className="single-month-title">
            <h3>{MONTHS[month]} {year}</h3>
            <span>{monthStats(month).days} days with data</span>
          </div>

          {renderMonthGrid(year, month)}
        </div>
      )}

      <div className="calendar-footer">
        <div className="calendar-legend">
          <span>Cleaner</span>

          {[
            "#22a447", "#86b817", "#e9c52c",
            "#f18b36", "#e44848", "#8f1728",
            "#e8edf2",
          ].map((color) => (
            <i
              key={color}
              style={{ backgroundColor: color }}
            />
          ))}

          <span>Worse / no data</span>
        </div>

        <p>
          Each day is colored by its daily maximum AQI.
          Grey means no valid reading.
        </p>
      </div>
    </section>
  );
}

/* Activity recommendations — table removed */

function ActivityRecommendations({ result, loading }) {
  const recommended = result?.recommended ?? null;

  const alternatives = Array.isArray(result?.alternatives)
    ? result.alternatives
    : [];

  const bestAvailable = result?.best_available ?? null;

  return (
    <section className="panel recommendations-panel">
      <div className="panel-heading recommendations-heading">
        <div className="section-icon">
          <ShieldCheck size={19} />
        </div>

        <div>
          <h2>Activity recommendations</h2>
          <p>Recommendations calculated by your Python planner.</p>
        </div>
      </div>

      {!result && !loading && (
        <div className="empty-state">
          <CalendarDays size={28} />
          <strong>No plan generated yet</strong>
          <span>
            Choose your requirements and check an activity window.
          </span>
        </div>
      )}

      {loading && (
        <div className="empty-state">
          <RefreshCw size={25} className="spin" />
          <strong>Evaluating available windows</strong>
          <span>Waiting for the historical AQI planner.</span>
        </div>
      )}

      {result && (
        <>
          <div
            className={`recommendation-card ${
              recommended ? "approved" : "not-approved"
            }`}
          >
            <div className="recommendation-status-icon">
              {recommended
                ? <CheckCircle2 size={23} />
                : <XCircle size={23} />}
            </div>

            <div className="recommendation-main">
              <span className="recommendation-label">
                {recommended
                  ? "RECOMMENDED WINDOW"
                  : "NO APPROVED WINDOW"}
              </span>

              <h3>
                {recommended
                  ? formatWindow(recommended)
                  : "No window meets the selected threshold"}
              </h3>

              <p>
                {recommended
                  ? `Worst AQI: ${displayAQI(worstAQI(recommended))} · Average AQI: ${displayAQI(averageAQI(recommended))}`
                  : result.reason ||
                    "Review the available readings and planner result below."}
              </p>
            </div>

            {recommended && (
              <span
                className="aqi-pill"
                style={{
                  color: aqiColor(worstAQI(recommended)),
                  backgroundColor: `${aqiColor(worstAQI(recommended))}18`,
                }}
              >
                AQI {displayAQI(worstAQI(recommended))}
              </span>
            )}
          </div>

          {!recommended && bestAvailable && (
            <div className="best-available">
              <strong>Best available alternative</strong>
              <span>{formatWindow(bestAvailable)}</span>
              <span>
                Worst AQI: {displayAQI(worstAQI(bestAvailable))}
              </span>
              <small>
                This window did not meet the selected threshold
                and is not approved by the planner.
              </small>
            </div>
          )}

          {alternatives.length > 0 && (
            <div className="alternatives-section">
              <h3>Other suitable windows</h3>

              <div className="alternatives-list">
                {alternatives.map((item, index) => (
                  <div className="alternative-row" key={index}>
                    <div className="alternative-number">
                      {index + 1}
                    </div>

                    <div className="alternative-info">
                      <strong>{formatWindow(item)}</strong>
                      <span>
                        Average AQI: {displayAQI(averageAQI(item))}
                      </span>
                    </div>

                    <span
                      className="aqi-pill"
                      style={{
                        color: aqiColor(worstAQI(item)),
                        backgroundColor: `${aqiColor(worstAQI(item))}18`,
                      }}
                    >
                      Worst {displayAQI(worstAQI(item))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}

/* AQI overview */

function AQIOverview({
  result,
  date,
  readings,
  healthConsiderations,
}) {
  const chartData = readings.map((reading) => ({
    time:
      reading.time ??
      reading.timestamp ??
      reading.datetime ??
      "",
    aqi: reading.aqi == null ? null : Number(reading.aqi),
  }));

  const validAQI = readings
    .map((reading) => Number(reading.aqi))
    .filter(Number.isFinite);

  const average = validAQI.length
    ? Math.round(
        validAQI.reduce((sum, value) => sum + value, 0) /
          validAQI.length
      )
    : null;

  const worst = validAQI.length
    ? Math.max(...validAQI)
    : null;

  return (
    <section className="panel overview-panel">
      <div className="panel-heading">
        <div className="section-icon">
          <Wind size={19} />
        </div>

        <div>
          <h2>AQI overview</h2>
          <p>
            {result
              ? `Historical readings for ${date}`
              : "Submit a plan to load historical readings."}
          </p>
        </div>
      </div>

      <div className="metrics-grid">
        <Metric
          label="Average AQI"
          value={displayAQI(average)}
          subtitle={average == null ? "No readings" : aqiCategory(average)}
          icon={Activity}
        />

        <Metric
          label="Highest AQI"
          value={displayAQI(worst)}
          subtitle={worst == null ? "No readings" : aqiCategory(worst)}
          icon={Wind}
        />

        <Metric
          label="Readings"
          value={readings.length}
          subtitle="Returned by planner"
          icon={Clock3}
        />

        <Metric
          label="AQI threshold"
          value={result?.max_aqi ?? "—"}
          subtitle={
            healthConsiderations
              ? "Stricter setting selected"
              : "General setting selected"
          }
          icon={ShieldCheck}
        />
      </div>

      <div className="chart-heading">
        <div>
          <h3>Hourly AQI trend</h3>
          <p>Historical hourly readings returned by the API</p>
        </div>

        {validAQI.length > 0 && (
          <span className="chart-legend">
            <span className="legend-dot" /> AQI
          </span>
        )}
      </div>

      <div className="chart-container">
        {chartData.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 12, right: 12, left: -18, bottom: 4 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#e2e8f0"
              />
              <XAxis
                dataKey="time"
                tick={{ fill: "#64748b", fontSize: 11 }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#64748b", fontSize: 11 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: 10,
                  border: "1px solid #e2e8f0",
                }}
              />
              <Line
                type="monotone"
                dataKey="aqi"
                name="AQI"
                stroke="#526b88"
                strokeWidth={2.5}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="empty-chart">
            <Activity size={27} />
            <span>Your hourly AQI trend will appear here.</span>
          </div>
        )}
      </div>

      {result && (
        <p className="data-note">
          Status: {result.status ?? "Completed"}.
          {result.reason ? ` ${result.reason}` : ""}
        </p>
      )}
    </section>
  );
}

import CityComparison from "./CityComparison.jsx";

const CITIES = ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai"];

function formatAQI(value) {
  return value == null || !Number.isFinite(Number(value)) ? "—" : Math.round(Number(value));
}

function Workspace({ defaultCity = "Delhi" }) {
  const [origin, setOrigin] = useState(defaultCity);
  const [destination, setDestination] = useState(defaultCity === "Delhi" ? "Mumbai" : "Delhi");
  const [startDate, setStartDate] = useState("2019-07-15");
  const [endDate, setEndDate] = useState("2019-07-17");
  const [duration, setDuration] = useState("60");
  const [tripResult, setTripResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function planTrip(event) {
    event.preventDefault();
    setError("");
    setTripResult(null);

    if (origin === destination) {
      setError("Choose two different cities for your trip.");
      return;
    }
    if (startDate > endDate) {
      setError("The return date must be on or after the departure date.");
      return;
    }

    const dates = [];
    const current = new Date(`${startDate}T12:00:00`);
    const last = new Date(`${endDate}T12:00:00`);
    while (current <= last && dates.length < 31) {
      dates.push(current.toISOString().slice(0, 10));
      current.setDate(current.getDate() + 1);
    }
    if (!dates.length || startDate > endDate) {
      setError("Choose a valid trip date range.");
      return;
    }
    if (dates.length >= 31 && dates[dates.length - 1] !== endDate) {
      setError("Please choose a trip of 31 days or fewer.");
      return;
    }

    setLoading(true);
    try {
      const comparisons = await Promise.all(
        dates.map(async (date) => {
          const response = await fetch(`${API_URL}/api/compare?${new URLSearchParams({
            city_a: origin,
            city_b: destination,
            start_date: date,
            end_date: date,
          })}`);
          const data = await response.json();
          if (!response.ok) throw new Error(data.detail || `Could not load AQI for ${date}.`);
          return { date, origin: data.city_a, destination: data.city_b };
        })
      );
      setTripResult(comparisons);
    } catch (err) {
      setError(err.message || "Could not plan this trip. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  const originReadings = (tripResult ?? []).map((day) => day.origin.average_aqi).filter((value) => value != null);
  const destinationReadings = (tripResult ?? []).map((day) => day.destination.average_aqi).filter((value) => value != null);
  const originAverage = originReadings.length ? originReadings.reduce((sum, value) => sum + value, 0) / originReadings.length : null;
  const destinationAverage = destinationReadings.length ? destinationReadings.reduce((sum, value) => sum + value, 0) / destinationReadings.length : null;

  return (
    <div className="workspace-content">
      <section className="panel trip-scheduler-panel">
        <div className="panel-heading">
          <div className="section-icon"><CalendarClock size={19} /></div>
          <div>
            <h2>Trip scheduler</h2>
            <p>Choose your route and dates to review historical air quality at both destinations.</p>
          </div>
        </div>

        <form className="trip-form" onSubmit={planTrip}>
          <label>
            <span><MapPin size={14} /> Departure city</span>
            <select value={origin} onChange={(event) => setOrigin(event.target.value)}>
              {CITIES.map((city) => <option key={city} value={city}>{city}</option>)}
            </select>
          </label>
          <label>
            <span><Route size={14} /> Destination city</span>
            <select value={destination} onChange={(event) => setDestination(event.target.value)}>
              {CITIES.map((city) => <option key={city} value={city}>{city}</option>)}
            </select>
          </label>
          <label>
            <span><CalendarClock size={14} /> Departure date</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required />
          </label>
          <label>
            <span><CalendarClock size={14} /> Return date</span>
            <input type="date" value={endDate} min={startDate} onChange={(event) => setEndDate(event.target.value)} required />
          </label>
          <label>
            <span><Clock3 size={14} /> Planned outdoor activity</span>
            <select value={duration} onChange={(event) => setDuration(event.target.value)}>
              <option value="30">30 minutes</option>
              <option value="60">1 hour</option>
              <option value="90">1 hour 30 minutes</option>
              <option value="120">2 hours</option>
              <option value="180">3 hours</option>
            </select>
          </label>
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Checking trip dates…" : "Check trip AQI"}
          </button>
        </form>

        <p className="trip-note">The scheduler compares historical AQI averages for each selected date. It does not book travel or forecast future AQI.</p>

        {error && <div className="error-message" role="alert"><AlertTriangle size={17} />{error}</div>}

        {tripResult && (
          <div className="trip-results">
            <div className="trip-summary-grid">
              <div className="trip-summary-card">
                <span>{origin} · Mean of available daily averages</span>
                <strong>{formatAQI(originAverage)}</strong>
                <small>{originReadings.length} day(s) with AQI data</small>
              </div>
              <div className="trip-summary-card">
                <span>{destination} · Mean of available daily averages</span>
                <strong>{formatAQI(destinationAverage)}</strong>
                <small>{destinationReadings.length} day(s) with AQI data</small>
              </div>
            </div>
            <div className="trip-day-list">
              <h3>Daily trip overview</h3>
              {tripResult.map((day) => (
                <div className="trip-day-row" key={day.date}>
                  <strong>{day.date}</strong>
                  <span>{origin}: <b>{formatAQI(day.origin.average_aqi)}</b></span>
                  <span>{destination}: <b>{formatAQI(day.destination.average_aqi)}</b></span>
                  <span className="trip-duration"><Clock3 size={13} /> {duration} min activity</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <CityComparison />
    </div>
  );
}


/* Main application */

function App() {
  const [activeView, setActiveView] = useState("planner");
  const [selectedCity, setSelectedCity] = useState("Delhi");
  const cities = ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai"];
  const [date, setDate] = useState("2019-07-15");
  const [duration, setDuration] = useState(60);
  const [timeRange, setTimeRange] = useState([
    MIN_TIME,
    MAX_TIME,
  ]);
  const [healthConsiderations, setHealthConsiderations] =
    useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const readings = Array.isArray(result?.readings)
    ? result.readings
    : [];

  async function checkPlan(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/api/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          date,
          city: selectedCity,
          duration_minutes: Number(duration),
          available_from: Number(timeRange[0]),
          available_until: Number(timeRange[1]),
          health_considerations: healthConsiderations,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail ?? data)
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message?.includes("fetch")
          ? "Cannot connect to the backend. Make sure FastAPI is running at http://127.0.0.1:8000."
          : err.message || "Could not create the plan."
      );
    } finally {
      setLoading(false);
    }
  }

  function updateRange(index, value) {
    const next = [...timeRange];
    next[index] = Number(value);

    if (next[0] >= next[1]) {
      if (index === 0) next[0] = next[1] - 5;
      else next[1] = next[0] + 5;
    }

    setTimeRange(next);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Wind size={23} /></div>
          <div>
            <div className="brand-name">School AirSafe</div>
            <div className="brand-subtitle">AIR QUALITY PLANNER</div>
          </div>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <button
          type="button"
          className={`nav-item nav-button ${activeView === "planner" ? "active" : ""}`}
          onClick={() => {setActiveView("planner");

            setTimeout(() => {
              document.querySelector("main")?.scrollTo({
                top: 0,
                behavior: "smooth",
              });

              window.scrollTo({
                top: 0,
                behavior: "smooth",
              });
            }, 50);
          }}
        >
          <Activity size={18} /> Activity planner
        </button>

        <button
          type="button"
          className="nav-item nav-button"
          onClick={() => {
            setActiveView("planner");
            setTimeout(() => document.getElementById("workspace")?.scrollIntoView({ behavior: "smooth" }), 0);
          }}
        >
          <LayoutGrid size={18} /> AQI calendar
        </button>

        <button
          type="button"
          className={`nav-item nav-button ${activeView === "workspace" ? "active" : ""}`}
          onClick={() => setActiveView("workspace")}
        >
          <CalendarDays size={18} /> Trip scheduler
        </button>

        <div className="sidebar-note">
          <ShieldCheck size={19} />
          <div>
            <strong>Safer school activities</strong>
            <p>
              Use historical AQI readings to compare available
              activity windows.
            </p>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="status-dot" />
          Historical data planner
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <div className="eyebrow">SCHOOL OPERATIONS</div>
            <h1>{activeView === "planner" ? "Activity planner" : "Workspace"}</h1>
            <p className="page-description">
              {activeView === "planner"
                ? "Find a suitable time window for outdoor school activities."
                : "Schedule trips and compare historical air quality across cities."}
            </p>
          </div>

          <div className="header-actions">
            <label className="city-selector">
              <span>City</span>
              <select
                value={selectedCity}
                onChange={(event) => {
                  setSelectedCity(event.target.value);
                  setResult(null);
                  setError("");
                }}
                aria-label="Select dashboard city"
              >
                {cities.map((city) => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
            </label>
            <div className="header-status">
              <span className="status-dot" />
              Historical AQI planning
            </div>
          </div>
        </header>

        {activeView === "planner" && <>
        <div className="dashboard-grid" id="planner">
          <section className="panel planner-panel">
            <div className="panel-heading">
              <div className="section-icon">
                <CalendarDays size={19} />
              </div>
              <div>
                <h2>Plan an activity</h2>
                <p>Set your school's scheduling requirements.</p>
              </div>
            </div>

            <form onSubmit={checkPlan}>
              <div className="form-field">
                <label htmlFor="date">Planning date</label>
                <input
                  id="date"
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <div className="field-heading">
                  <label htmlFor="duration">Activity duration</label>
                  <span className="field-value">
                    {duration >= 60
                      ? `${Math.floor(duration / 60)} hr${duration >= 120 ? "s" : ""}${duration % 60 ? ` ${duration % 60} min` : ""}`
                      : `${duration} min`}
                  </span>
                </div>

                <input
                  id="duration"
                  type="range"
                  min="30"
                  max="240"
                  step="5"
                  value={duration}
                  onChange={(event) =>
                    setDuration(Number(event.target.value))
                  }
                />

                <div className="range-labels">
                  <span>30 minutes</span>
                  <span>4 hours</span>
                </div>
              </div>

              <div className="form-field">
                <div className="field-heading">
                  <label>Available time window</label>
                  <span className="field-value">
                    {formatTime(timeRange[0])} – {formatTime(timeRange[1])}
                  </span>
                </div>

                <div className="dual-range">
                  <input
                    aria-label="Available start time"
                    type="range"
                    min={MIN_TIME}
                    max={MAX_TIME}
                    step="5"
                    value={timeRange[0]}
                    onChange={(event) =>
                      updateRange(0, event.target.value)
                    }
                  />

                  <input
                    aria-label="Available end time"
                    type="range"
                    min={MIN_TIME}
                    max={MAX_TIME}
                    step="5"
                    value={timeRange[1]}
                    onChange={(event) =>
                      updateRange(1, event.target.value)
                    }
                  />
                </div>

                <div className="range-labels">
                  <span>06:00</span>
                  <span>18:00</span>
                </div>
              </div>

              <label className="health-option">
                <input
                  type="checkbox"
                  checked={healthConsiderations}
                  onChange={(event) =>
                    setHealthConsiderations(event.target.checked)
                  }
                />

                <span className="health-icon">
                  <HeartPulse size={19} />
                </span>

                <span className="health-copy">
                  <strong>Consider respiratory health needs</strong>
                  <small>
                    Apply the planner's stricter AQI threshold.
                  </small>
                </span>
              </label>

              <button
                className="primary-button"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <RefreshCw size={17} className="spin" />
                    Checking historical data…
                  </>
                ) : (
                  <>
                    <Activity size={17} />
                    Check activity window
                  </>
                )}
              </button>
            </form>

            {error && (
              <div className="error-message" role="alert">
                <AlertTriangle size={18} />
                {error}
              </div>
            )}
          </section>

          <div className="dashboard-results">
            <ActivityRecommendations
              result={result}
              loading={loading}
            />

            <HourlyAQIStrip readings={readings} />

            <AQIOverview
              result={result}
              date={date}
              readings={readings}
              healthConsiderations={healthConsiderations}
            />
          </div>
        </div>

        <AQICalendar
          selectedDate={date}
          onSelectDate={setDate}
          city={selectedCity}
        />

        </>}

        {activeView === "workspace" && <Workspace defaultCity={selectedCity} />}

        <footer className="disclaimer">
          <AlertTriangle size={16} />
          <span>
            School AirSafe is a historical-data planning aid, not
            a real-time air-quality monitor or medical clearance.
            Follow local guidance and school health policies.
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
