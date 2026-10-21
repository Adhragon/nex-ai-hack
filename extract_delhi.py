
from pathlib import Path
import pandas as pd

source = Path("data/city_hour.csv")
output = Path("data/delhi_hour.csv")

if not source.exists():
    raise FileNotFoundError(
        f"Dataset not found at {source.resolve()}. "
        "Place city_hour.csv inside the data folder."
    )

df = pd.read_csv(source)
df.columns = df.columns.str.strip()

required = {"City", "Datetime", "AQI", "AQI_Bucket"}
missing = required - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

df["City"] = df["City"].astype("string").str.strip()

cities = sorted(
    df.loc[
        df["City"].str.contains("Delhi", case=False, na=False),
        "City"
    ].dropna().unique()
)

print("Matching city names:", cities)

delhi = df[df["City"].str.casefold() == "delhi"].copy()

if delhi.empty:
    raise ValueError(
        "No exact Delhi records found. Check the city names above."
    )

delhi["Datetime"] = pd.to_datetime(
    delhi["Datetime"], errors="coerce"
)

delhi = delhi.dropna(subset=["Datetime"])
delhi = delhi.sort_values("Datetime")

delhi.to_csv(output, index=False)

print(f"\nSaved to: {output.resolve()}")
print(f"Rows: {len(delhi):,}")
print(f"Date range: {delhi['Datetime'].min()} "
      f"to {delhi['Datetime'].max()}")
print(f"Missing AQI values: {delhi['AQI'].isna().sum():,}")
print(f"Duplicate timestamps: "
      f"{delhi['Datetime'].duplicated().sum():,}")
print("\nFirst five observations:")
print(delhi[["City", "Datetime", "AQI", "AQI_Bucket"]].head())
