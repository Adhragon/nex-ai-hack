
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = BASE_DIR / "data" / "city_hour.csv"
OUTPUT_DIR = BASE_DIR / "data"

CITIES = ["Mumbai", "Bengaluru", "Kolkata", "Chennai"]

def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {SOURCE_FILE}")

    df = pd.read_csv(SOURCE_FILE)

    required = {"City", "Datetime", "AQI"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["City"] = df["City"].astype(str).str.strip()
    df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
    df["AQI"] = pd.to_numeric(df["AQI"], errors="coerce")

    df = df[df["City"].isin(CITIES)].copy()
    df = df.dropna(subset=["Datetime"])
    df.loc[~df["AQI"].between(0, 500), "AQI"] = pd.NA

    for city in CITIES:
        city_df = df[df["City"] == city].copy()

        city_df = city_df.sort_values("Datetime")
        city_df = city_df.drop_duplicates(
            subset=["Datetime"], keep="first"
        )

        output_file = OUTPUT_DIR / f"{city.lower()}_hour.csv"
        city_df.to_csv(output_file, index=False)

        print(f"\n{city}")
        print(f"Rows: {len(city_df)}")
        print(f"Valid AQI readings: {city_df['AQI'].notna().sum()}")
        print(f"Saved to: {output_file}")

    print("\nAll four city datasets created successfully.")

if __name__ == "__main__":
    main()
