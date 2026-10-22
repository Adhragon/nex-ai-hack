
import math
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DATA_PATH = Path("data/delhi_hour.csv")

SCHOOL_START = 6
SCHOOL_END = 18
STUCK_HOURS = 6
MAX_AQI = 200


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
    df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")
    df = df.dropna(subset=["Datetime"])
    return df.sort_values("Datetime").reset_index(drop=True)


def category(aqi):
    if pd.isna(aqi):
        return "Missing"
    if aqi < 0:
        return "Invalid"
    if aqi > 500:
        return "Out of range"
    if aqi <= 50:
        return "Good"
    if aqi <= 100:
        return "Satisfactory"
    if aqi <= 200:
        return "Moderate"
    if aqi <= 300:
        return "Poor"
    if aqi <= 400:
        return "Very Poor"
    return "Severe"


def get_time_limits():
    value = input(
        "Available from / preferred range "
        "(HH:MM or HH:MM-HH:MM, blank for full day): "
    ).strip()

    if not value:
        return SCHOOL_START * 60, SCHOOL_END * 60

    try:
        if "-" in value:
            start_text, end_text = value.split("-", 1)
            start_time = datetime.strptime(start_text.strip(), "%H:%M")
            end_time = datetime.strptime(end_text.strip(), "%H:%M")

            start = start_time.hour * 60 + start_time.minute
            end = end_time.hour * 60 + end_time.minute

            if start < SCHOOL_START * 60 or end > SCHOOL_END * 60:
                raise ValueError
            if start >= end:
                raise ValueError

            return start, end

        start_time = datetime.strptime(value, "%H:%M")
        start = start_time.hour * 60 + start_time.minute

        if start < SCHOOL_START * 60 or start >= SCHOOL_END * 60:
            raise ValueError

        return start, SCHOOL_END * 60

    except ValueError:
        print("Invalid time. Use HH:MM or HH:MM-HH:MM within 06:00-18:00.")
        return get_time_limits()


def get_readings(day, available_from, available_until):
    readings = []

    for hour in range(SCHOOL_START, SCHOOL_END):
        slot_start = hour * 60
        slot_end = (hour + 1) * 60

        if slot_start < available_from or slot_end > available_until:
            continue

        hourly = day[day["Datetime"].dt.hour == hour]

        if hourly.empty:
            readings.append({
                "time": f"{hour:02d}:00",
                "aqi": None,
                "category": "Missing",
                "status": "No reading"
            })
        elif len(hourly) > 1:
            readings.append({
                "time": f"{hour:02d}:00",
                "aqi": None,
                "category": "Invalid",
                "status": "Duplicate timestamps"
            })
        else:
            aqi = hourly.iloc[0]["AQI"]
            readings.append({
                "time": f"{hour:02d}:00",
                "aqi": aqi,
                "category": category(aqi),
                "status": "Observed" if pd.notna(aqi) else "Missing AQI"
            })

    return readings


def find_stuck_timestamps(day):
    valid = day.sort_values("Datetime").reset_index(drop=True)
    stuck_times = set()
    run_start = 0

    for i in range(1, len(valid) + 1):
        same_as_previous = False

        if i < len(valid):
            previous = valid.iloc[i - 1]
            current = valid.iloc[i]

            same_as_previous = (
                pd.notna(previous["AQI"])
                and pd.notna(current["AQI"])
                and current["AQI"] == previous["AQI"]
                and current["Datetime"] - previous["Datetime"]
                == pd.Timedelta(hours=1)
            )

        if not same_as_previous:
            run = valid.iloc[run_start:i]

            if (
                len(run) >= STUCK_HOURS
                and run["AQI"].notna().all()
                and run["AQI"].nunique() == 1
            ):
                stuck_times.update(run["Datetime"].tolist())

            run_start = i

    return stuck_times


def evaluate_windows(
    day,
    duration_minutes,
    available_from,
    available_until
):
    if duration_minutes <= 0:
        return []

    windows = []
    stuck_times = find_stuck_timestamps(day)
    duration_hours = math.ceil(duration_minutes / 60)

    for start in range(SCHOOL_START, SCHOOL_END):
        start_minutes = start * 60
        end_minutes = start_minutes + duration_minutes

        if start_minutes < available_from or end_minutes > available_until:
            continue

        hours = list(range(start, start + duration_hours))

        if not hours or hours[-1] >= SCHOOL_END:
            continue

        window = day[day["Datetime"].dt.hour.isin(hours)].copy()

        if len(window) != duration_hours:
            continue
        if window["Datetime"].dt.hour.nunique() != duration_hours:
            continue
        if window["Datetime"].dt.date.nunique() != 1:
            continue
        if window["AQI"].isna().any():
            continue
        if (window["AQI"] < 0).any() or (window["AQI"] > 500).any():
            continue
        if window["Datetime"].dt.minute.ne(0).any():
            continue
        if any(timestamp in stuck_times for timestamp in window["Datetime"]):
            continue

        worst_aqi = float(window["AQI"].max())
        average_aqi = float(window["AQI"].mean())

        end_time = datetime(2000, 1, 1, start, 0) + timedelta(
            minutes=duration_minutes
        )

        windows.append({
            "start": f"{start:02d}:00",
            "end": end_time.strftime("%H:%M"),
            "duration_minutes": duration_minutes,
            "worst_aqi": worst_aqi,
            "average_aqi": round(average_aqi, 2),
            "category": category(worst_aqi),
            "policy_passed": worst_aqi <= MAX_AQI
        })

    windows.sort(
        key=lambda w: (
            w["worst_aqi"],
            w["average_aqi"],
            w["start"]
        )
    )

    return windows


def plan(date_string, duration_minutes, available_from, available_until):
    try:
        selected_date = datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        return {
            "status": "INVALID INPUT",
            "reason": "Enter the date in YYYY-MM-DD format.",
            "readings": [],
            "recommended": None,
            "alternatives": [],
            "best_available": None
        }

    if duration_minutes <= 0:
        return {
            "status": "INVALID INPUT",
            "reason": "Duration must be a positive number of minutes.",
            "readings": [],
            "recommended": None,
            "alternatives": [],
            "best_available": None
        }

    df = load_data()
    day = df[df["Datetime"].dt.date == selected_date].copy()

    if day.empty:
        return {
            "status": "NO ADVICE",
            "reason": "No historical data is available for this date.",
            "readings": [],
            "recommended": None,
            "alternatives": [],
            "best_available": None
        }

    school_day = day[
        (day["Datetime"].dt.hour >= SCHOOL_START)
        & (day["Datetime"].dt.hour < SCHOOL_END)
    ].copy()

    readings = get_readings(
        school_day,
        available_from,
        available_until
    )

    candidates = evaluate_windows(
        school_day,
        duration_minutes,
        available_from,
        available_until
    )

    best_available = candidates[0] if candidates else None
    approved = [w for w in candidates if w["policy_passed"]]

    if not approved:
        return {
            "status": "NO ADVICE",
            "reason": (
                "No window passed the configured AQI policy and "
                "data-quality checks."
                if best_available
                else "No window passed the time and data-quality checks."
            ),
            "readings": readings,
            "recommended": None,
            "alternatives": [],
            "best_available": best_available
        }

    return {
        "status": "CANDIDATE FOUND",
        "reason": "Best eligible window under the configured policy.",
        "readings": readings,
        "recommended": approved[0],
        "alternatives": approved[1:4],
        "best_available": best_available
    }


def display(result):
    print("\n--- HOURLY AQI READINGS ---")

    if not result["readings"]:
        print("No readings available for the selected time range.")

    for item in result["readings"]:
        aqi = item["aqi"]
        aqi_text = "N/A" if aqi is None or pd.isna(aqi) else str(aqi)

        print(
            f'{item["time"]} | AQI {aqi_text:>6} | '
            f'{item["category"]:<12} | {item["status"]}'
        )

    print("\n--- PLANNING RESULT ---")
    print("Status:", result["status"])
    print("Reason:", result["reason"])

    if result["recommended"]:
        print("\n--- APPROVED RECOMMENDATION ---")
        print(result["recommended"])

        if result["alternatives"]:
            print("\n--- ALTERNATIVES ---")
            for alternative in result["alternatives"]:
                print(alternative)

    best = result.get("best_available")

    if best and result["recommended"] is None:
        print("\n--- BEST AVAILABLE WINDOW (NOT APPROVED) ---")
        print(f'Time: {best["start"]} - {best["end"]}')
        print(f'Worst AQI: {best["worst_aqi"]}')
        print(f'Average AQI: {best["average_aqi"]}')
        print(f'Category: {best["category"]}')
        print("Warning: This window fails the configured AQI policy.")
        print("It is not an approved recommendation.")


def main():
    date_string = input("Enter date (YYYY-MM-DD): ").strip()

    try:
        duration_minutes = int(
            input("Activity duration in minutes (e.g. 45, 75, 135): ").strip()
        )
    except ValueError:
        print("Invalid duration. Enter a whole number of minutes.")
        return

    if duration_minutes <= 0:
        print("Duration must be greater than zero.")
        return

    available_from, available_until = get_time_limits()

    try:
        result = plan(
            date_string,
            duration_minutes,
            available_from,
            available_until
        )
        display(result)
    except FileNotFoundError as error:
        print(error)


if __name__ == "__main__":
    main()
