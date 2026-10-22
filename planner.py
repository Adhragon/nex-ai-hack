import math
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CITY_FILES = {
    "Delhi": "delhi_hour.csv",
    "Mumbai": "mumbai_hour.csv",
    "Bengaluru": "bengaluru_hour.csv",
    "Kolkata": "kolkata_hour.csv",
    "Chennai": "chennai_hour.csv",
}

DATA_PATH = DATA_DIR / CITY_FILES["Delhi"]

SCHOOL_START = 6
SCHOOL_END = 18
STUCK_HOURS = 6

GENERAL_MAX_AQI = 200
ASTHMA_MAX_AQI = 100


def get_data_path(city="Delhi"):
    if city not in CITY_FILES:
        raise ValueError(
            f"Unsupported city: {city}. Choose from {', '.join(CITY_FILES)}."
        )
    return DATA_DIR / CITY_FILES[city]


def load_data(city="Delhi"):
    path = get_data_path(city)
    if not path.exists():
        raise FileNotFoundError(f"Dataset for {city} not found: {path}")

    df = pd.read_csv(path)

    if "Datetime" not in df.columns or "AQI" not in df.columns:
        raise ValueError(
            f"The {city} dataset must contain Datetime and AQI columns."
        )

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


def ask_asthma_status():
    while True:
        answer = input(
            "Does the activity involve a child with asthma? (yes/no): "
        ).strip().lower()

        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False

        print("Please enter yes or no.")


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

            if (
                start < SCHOOL_START * 60
                or end > SCHOOL_END * 60
                or start >= end
            ):
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
                "status": "No reading",
            })
        elif len(hourly) > 1:
            readings.append({
                "time": f"{hour:02d}:00",
                "aqi": None,
                "category": "Invalid",
                "status": "Duplicate timestamps",
            })
        else:
            aqi = hourly.iloc[0]["AQI"]
            readings.append({
                "time": f"{hour:02d}:00",
                "aqi": aqi,
                "category": category(aqi),
                "status": "Observed" if pd.notna(aqi) else "Missing AQI",
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
    available_until,
    max_aqi,
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
            "policy_limit": max_aqi,
            "policy_passed": worst_aqi <= max_aqi,
        })

    windows.sort(
        key=lambda window: (
            window["worst_aqi"],
            window["average_aqi"],
            window["start"],
        )
    )

    return windows


def empty_result(status, reason):
    return {
        "status": status,
        "reason": reason,
        "readings": [],
        "recommended": None,
        "alternatives": [],
        "best_available": None,
        "max_aqi": None,
        "asthma": None,
        "city": "Delhi",
    }


def plan(
    date_string,
    duration_minutes,
    available_from,
    available_until,
    asthma,
    city="Delhi",
):
    try:
        selected_date = datetime.strptime(
            date_string, "%Y-%m-%d"
        ).date()
    except ValueError:
        return empty_result(
            "INVALID INPUT",
            "Enter the date in YYYY-MM-DD format.",
        )

    if duration_minutes <= 0:
        return empty_result(
            "INVALID INPUT",
            "Duration must be a positive number of minutes.",
        )

    max_aqi = ASTHMA_MAX_AQI if asthma else GENERAL_MAX_AQI

    df = load_data(city)
    day = df[df["Datetime"].dt.date == selected_date].copy()

    if day.empty:
        result = empty_result(
            "NO ADVICE",
            "No historical data is available for this date.",
        )
        result["max_aqi"] = max_aqi
        result["asthma"] = asthma
        result["city"] = city
        return result

    school_day = day[
        (day["Datetime"].dt.hour >= SCHOOL_START)
        & (day["Datetime"].dt.hour < SCHOOL_END)
    ].copy()

    readings = get_readings(
        school_day,
        available_from,
        available_until,
    )

    candidates = evaluate_windows(
        school_day,
        duration_minutes,
        available_from,
        available_until,
        max_aqi,
    )

    best_available = candidates[0] if candidates else None
    approved = [
        window for window in candidates if window["policy_passed"]
    ]

    if not approved:
        return {
            "status": "NO ADVICE",
            "reason": (
                "No window passed the configured AQI policy."
                if best_available
                else (
                    "No window passed the time and data-quality checks. "
                    "A reliable best available window cannot be calculated."
                )
            ),
            "readings": readings,
            "recommended": None,
            "alternatives": [],
            "best_available": best_available,
            "max_aqi": max_aqi,
            "asthma": asthma,
            "city": city,
        }

    return {
        "status": "CANDIDATE FOUND",
        "reason": "Best eligible window under the configured policy.",
        "readings": readings,
        "recommended": approved[0],
        "alternatives": approved[1:4],
        "best_available": best_available,
        "max_aqi": max_aqi,
        "asthma": asthma,
        "city": city,
    }


def display(result):
    print(f"\nCity: {result.get('city', 'Delhi')}")
    print(f"Status: {result['status']}")
    print(f"Reason: {result['reason']}")

    if result.get("max_aqi") is not None:
        print(f"Configured AQI limit: {result['max_aqi']}")

    if result.get("readings"):
        print("\nHourly readings:")
        for reading in result["readings"]:
            print(
                f"{reading['time']} | AQI: {reading['aqi']} | "
                f"{reading['category']} | {reading['status']}"
            )

    recommended = result.get("recommended")
    if recommended:
        print("\nRecommended window:")
        print(
            f"{recommended['start']}–{recommended['end']} | "
            f"Average AQI: {recommended['average_aqi']} | "
            f"Worst AQI: {recommended['worst_aqi']}"
        )

        alternatives = result.get("alternatives", [])
        if alternatives:
            print("\nAlternative windows:")
            for window in alternatives:
                print(
                    f"{window['start']}–{window['end']} | "
                    f"Average AQI: {window['average_aqi']} | "
                    f"Worst AQI: {window['worst_aqi']}"
                )
    elif result.get("best_available"):
        window = result["best_available"]
        print("\nBest available window (does not pass policy):")
        print(
            f"{window['start']}–{window['end']} | "
            f"Average AQI: {window['average_aqi']} | "
            f"Worst AQI: {window['worst_aqi']}"
        )


def main():
    print("School AirSafe — Historical AQI Planner")
    print("Available cities:", ", ".join(CITY_FILES))

    city = input("Choose city [Delhi]: ").strip().title() or "Delhi"
    if city not in CITY_FILES:
        print(f"Unsupported city. Choose from: {', '.join(CITY_FILES)}")
        return

    date_string = input("Enter date (YYYY-MM-DD): ").strip()

    try:
        duration = int(input("Activity duration in minutes: ").strip())
    except ValueError:
        print("Duration must be a number.")
        return

    available_from, available_until = get_time_limits()
    asthma = ask_asthma_status()

    try:
        result = plan(
            date_string,
            duration,
            available_from,
            available_until,
            asthma,
            city=city,
        )
        display(result)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()