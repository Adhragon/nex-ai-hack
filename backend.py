from datetime import datetime
import math
from numbers import Integral, Real

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from planner import (
    plan,
    SCHOOL_START,
    SCHOOL_END,
    CITY_FILES,
    get_data_path,
)

app = FastAPI(
    title="School AirSafe API",
    description="Historical AQI planning, calendar, and city comparison API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class PlanRequest(BaseModel):
    date: str
    city: str = "Delhi"
    duration_minutes: int = Field(gt=0, le=720)
    available_from: int = Field(
        ge=SCHOOL_START * 60,
        lt=SCHOOL_END * 60,
    )
    available_until: int = Field(
        gt=SCHOOL_START * 60,
        le=SCHOOL_END * 60,
    )
    health_considerations: bool = False


def validate_city(city):
    if city not in CITY_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported city. Choose from: {', '.join(CITY_FILES)}",
        )


def make_json_safe(value):
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, (np.integer, Integral)):
        return int(value)

    if isinstance(value, (np.floating, Real)):
        number = float(value)
        return number if math.isfinite(number) else None

    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    return value


def load_city_data(city):
    validate_city(city)
    path = get_data_path(city)

    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Dataset for {city} not found: {path}",
        )

    df = pd.read_csv(path)

    if "Datetime" not in df.columns or "AQI" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail=f"The {city} dataset must contain Datetime and AQI columns.",
        )

    df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
    df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")
    df = df.dropna(subset=["Datetime"])
    df.loc[~df["AQI"].between(0, 500), "AQI"] = np.nan

    return df.sort_values("Datetime").reset_index(drop=True)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "School AirSafe API",
        "cities": list(CITY_FILES),
    }


@app.get("/api/calendar")
def get_calendar(
    year: int = Query(ge=2000, le=2100),
    city: str = Query(default="Delhi"),
):
    try:
        df = load_city_data(city)
        df = df[df["Datetime"].dt.year == year].copy()
        df["date"] = df["Datetime"].dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["AQI"])

        daily = (
            df.groupby("date")
            .agg(
                aqi=("AQI", "max"),
                average_aqi=("AQI", "mean"),
                readings=("AQI", "count"),
            )
            .reset_index()
        )

        if not daily.empty:
            daily["aqi"] = daily["aqi"].round().astype(int)
            daily["average_aqi"] = daily["average_aqi"].round(1)

        return {
            "year": year,
            "city": city,
            "metric": "daily_maximum_aqi",
            "days": daily.to_dict(orient="records"),
        }

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load calendar data: {error}",
        )


@app.post("/api/plan")
def create_plan(request: PlanRequest):
    validate_city(request.city)

    try:
        datetime.strptime(request.date, "%Y-%m-%d")

        if request.available_from >= request.available_until:
            raise HTTPException(
                status_code=422,
                detail="The end time must be later than the start time.",
            )

        result = plan(
            request.date,
            request.duration_minutes,
            request.available_from,
            request.available_until,
            request.health_considerations,
            city=request.city,
        )

        result["city"] = request.city
        return make_json_safe(result)

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=(
                "The planner could not process this request. "
                "Check the backend terminal for errors."
            ),
        )


@app.get("/api/compare")
def compare_cities(
    city_a: str = Query(...),
    city_b: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
):
    validate_city(city_a)
    validate_city(city_b)

    if city_a == city_b:
        raise HTTPException(
            status_code=422,
            detail="Choose two different cities.",
        )

    try:
        start = pd.to_datetime(start_date, errors="raise").normalize()
        end = pd.to_datetime(end_date, errors="raise").normalize()
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail="Dates must use YYYY-MM-DD format.",
        )

    if start > end:
        raise HTTPException(
            status_code=422,
            detail="Start date must be before or equal to end date.",
        )

    if (end - start).days > 366:
        raise HTTPException(
            status_code=422,
            detail="Choose a date range no longer than 367 calendar days.",
        )

    def summarize(city):
        df = load_city_data(city)

        selected = df[
            (df["Datetime"] >= start)
            & (df["Datetime"] < end + pd.Timedelta(days=1))
        ].copy()

        valid = selected.dropna(subset=["AQI"])

        daily = (
            valid.assign(
                date=valid["Datetime"].dt.strftime("%Y-%m-%d")
            )
            .groupby("date")["AQI"]
            .mean()
            .round(1)
        )

        return {
            "city": city,
            "average_aqi": (
                round(float(valid["AQI"].mean()), 1)
                if not valid.empty else None
            ),
            "worst_aqi": (
                round(float(valid["AQI"].max()), 1)
                if not valid.empty else None
            ),
            "valid_readings": int(len(valid)),
            "total_rows": int(len(selected)),
            "coverage_percent": (
                round(len(valid) / len(selected) * 100, 1)
                if len(selected) else 0
            ),
            "daily": [
                {"date": date, "aqi": float(aqi)}
                for date, aqi in daily.items()
            ],
        }

    return {
        "start_date": start_date,
        "end_date": end_date,
        "city_a": summarize(city_a),
        "city_b": summarize(city_b),
    }