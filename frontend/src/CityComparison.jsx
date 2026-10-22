import { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { GitCompareArrows } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";
const CITIES = ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Chennai"];

function getCategory(aqi) {
  if (aqi == null) return "No data";
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Satisfactory";
  if (aqi <= 200) return "Moderate";
  if (aqi <= 300) return "Poor";
  if (aqi <= 400) return "Very Poor";
  return "Severe";
}

function CityMetrics({ data }) {
  return (
    <div className="comparison-city">
      <h3>{data.city}</h3>

      <div className="comparison-metric">
        <span>Average AQI</span>
        <strong>{data.average_aqi ?? "—"}</strong>
        <small>{getCategory(data.average_aqi)}</small>
      </div>

      <div className="comparison-metric">
        <span>Worst AQI</span>
        <strong>{data.worst_aqi ?? "—"}</strong>
        <small>{getCategory(data.worst_aqi)}</small>
      </div>

      <div className="comparison-metric">
        <span>Valid readings</span>
        <strong>{data.valid_readings}</strong>
      </div>

      <div className="comparison-metric">
        <span>AQI data coverage</span>
        <strong>{data.coverage_percent}%</strong>
      </div>
    </div>
  );
}

export default function CityComparison() {
  const [cityA, setCityA] = useState("Delhi");
  const [cityB, setCityB] = useState("Mumbai");
  const [startDate, setStartDate] = useState("2019-01-01");
  const [endDate, setEndDate] = useState("2019-01-31");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function compare() {
    if (cityA === cityB) {
      setError("Select two different cities.");
      return;
    }

    if (!startDate || !endDate || startDate > endDate) {
      setError("Choose a valid date range.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const params = new URLSearchParams({
        city_a: cityA,
        city_b: cityB,
        start_date: startDate,
        end_date: endDate,
      });

      const response = await fetch(
        `${API_URL}/api/compare?${params.toString()}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Comparison failed.");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  const a = result?.city_a;
  const b = result?.city_b;

  const allDates = [
    ...new Set([
      ...(a?.daily ?? []).map((item) => item.date),
      ...(b?.daily ?? []).map((item) => item.date),
    ]),
  ].sort();

  const dailyA = new Map(
    (a?.daily ?? []).map((item) => [item.date, item.aqi])
  );

  const dailyB = new Map(
    (b?.daily ?? []).map((item) => [item.date, item.aqi])
  );

  const chartData = allDates.map((date) => ({
    date,
    [cityA]: dailyA.get(date) ?? null,
    [cityB]: dailyB.get(date) ?? null,
  }));

  let conclusion = "Not enough data to compare these cities.";

  if (a && b && a.average_aqi != null && b.average_aqi != null) {
    if (a.average_aqi === b.average_aqi) {
      conclusion = "Both cities have the same average AQI for this period.";
    } else {
      const cleaner = a.average_aqi < b.average_aqi ? a.city : b.city;
      conclusion = `${cleaner} had the lower average AQI during this period.`;
    }
  }

  return (
    <section className="panel city-comparison-panel" id="city-comparison">
      <div className="panel-heading">
        <div className="section-icon">
          <GitCompareArrows size={19} />
        </div>

        <div>
          <h2>City comparison</h2>
          <p>Compare historical air quality across two cities.</p>
        </div>
      </div>

      <div className="comparison-controls">
        <label>
          First city
          <select
            value={cityA}
            onChange={(event) => setCityA(event.target.value)}
          >
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </label>

        <label>
          Second city
          <select
            value={cityB}
            onChange={(event) => setCityB(event.target.value)}
          >
            {CITIES.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
        </label>

        <label>
          From
          <input
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />
        </label>

        <label>
          To
          <input
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />
        </label>

        <button
          type="button"
          className="primary-button"
          onClick={compare}
          disabled={loading}
        >
          {loading ? "Comparing..." : "Compare cities"}
        </button>
      </div>

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      {result && (
        <>
          <div className="comparison-conclusion">
            <strong>{conclusion}</strong>
            <span>
              Lower AQI indicates cleaner air in this historical comparison.
            </span>
          </div>

          <div className="comparison-metrics">
            <CityMetrics data={a} />
            <CityMetrics data={b} />
          </div>

          <div className="chart-heading">
            <div>
              <h3>Daily average AQI</h3>
              <p>Historical readings for the selected period</p>
            </div>
          </div>

          {chartData.length > 0 ? (
            <div className="comparison-chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#e2e8f0"
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10 }}
                    minTickGap={25}
                  />
                  <YAxis />
                  <Tooltip />
                  <Legend />

                  <Line
                    dataKey={cityA}
                    type="monotone"
                    stroke="#526b88"
                    dot={false}
                    connectNulls={false}
                  />

                  <Line
                    dataKey={cityB}
                    type="monotone"
                    stroke="#d97745"
                    dot={false}
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p>No valid AQI readings are available for these dates.</p>
          )}
        </>
      )}
    </section>
  );
}