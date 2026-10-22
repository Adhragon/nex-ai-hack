
from datetime import datetime
from pathlib import Path
import math
from numbers import Integral, Real

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from planner import plan, SCHOOL_START, SCHOOL_END, DATA_PATH

app = FastAPI(
    title="School AirSafe API",
    description="Historical AQI planning and calendar API",
    version="1.1.0",
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


def load_calendar_data():
    path = Path(DATA_PATH)

    if not path.exists():
        raise FileNotFoundError(
            f"AQI dataset not found: {path.resolve()}"
        )

    df = pd.read_csv(path)

    if "Datetime" not in df.columns or "AQI" not in df.columns:
        raise ValueError(
            "Dataset must contain Datetime and AQI columns."
        )

    df["Datetime"] = pd.to_datetime(
        df["Datetime"], errors="coerce"
    )
    df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")

    df = df.dropna(subset=["Datetime"])
    df = df[
        df["AQI"].notna()
        & df["AQI"].between(0, 500)
    ].copy()

    df["date"] = df["Datetime"].dt.strftime("%Y-%m-%d")

    daily = (
        df.groupby("date")
        .agg(
            aqi=("AQI", "max"),
            average_aqi=("AQI", "mean"),
            readings=("AQI", "count"),
        )
        .reset_index()
    )

    daily["aqi"] = daily["aqi"].round().astype(int)
    daily["average_aqi"] = daily["average_aqi"].round(1)

    return daily


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "School AirSafe API",
    }


@app.get("/api/calendar")
def get_calendar(year: int = Query(ge=2000, le=2100)):
    try:
        daily = load_calendar_data()
        daily = daily[
            daily["date"].str.startswith(f"{year}-")
        ]

        return {
            "year": year,
            "metric": "daily_maximum_aqi",
            "days": daily.to_dict(orient="records"),
        }

    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load calendar data: {error}",
        )


@app.post("/api/plan")
def create_plan(request: PlanRequest):
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
        )

        return make_json_safe(result)

    except HTTPException:
        raise

    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid date or planner input.",
        )

    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="The planner could not process this request. Check the backend terminal for errors.",
        )
