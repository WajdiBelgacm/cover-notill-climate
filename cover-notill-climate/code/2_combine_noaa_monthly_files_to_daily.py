import os
import glob
import pandas as pd
import numpy as np

# ============================================================
# STEP 2: COMBINE NOAA MONTHLY COUNTY FILES INTO DAILY DATA
# Input: 912 monthly NOAA files from Step 1
# Output: one daily county-level CSV, 2000–2018
# ============================================================

IN_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC\nclimgrid_county_raw_2000_2018"

OUT_FILE = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC\county_nclimgrid_daily_2000_2018.csv"

VARIABLES = ["prcp", "tmin", "tmax", "tavg"]

MISSING_VALUE = -999.99


# ============================================================
# FUNCTION: READ ONE NOAA MONTHLY COUNTY FILE
# ============================================================

def read_one_file(fp):
    """
    NOAA file structure:
    col 1 = region type
    col 2 = NCEI county code
    col 3 = county name
    col 4 = year
    col 5 = month
    col 6 = variable
    col 7-37 = daily values day 1 to day 31
    """

    df = pd.read_csv(fp, header=None)

    id_cols = [
        "region_type",
        "ncei_county_code",
        "county_name",
        "year",
        "month",
        "variable"
    ]

    day_cols = [f"day_{d}" for d in range(1, 32)]

    df.columns = id_cols + day_cols

    # Wide to long
    long = df.melt(
        id_vars=id_cols,
        value_vars=day_cols,
        var_name="day",
        value_name="value"
    )

    # Convert day_1, day_2, ... to 1, 2, ...
    long["day"] = long["day"].str.replace("day_", "", regex=False).astype(int)

    # Replace NOAA missing/impossible day value
    long["value"] = long["value"].replace(MISSING_VALUE, np.nan)

    # Create real date
    long["date"] = pd.to_datetime(
        dict(
            year=long["year"].astype(int),
            month=long["month"].astype(int),
            day=long["day"].astype(int)
        ),
        errors="coerce"
    )

    # Drop impossible dates, like February 30 and February 31
    long = long.dropna(subset=["date"])

    # Make variable lowercase
    long["variable"] = long["variable"].str.lower()

    return long


# ============================================================
# FIND FILES
# ============================================================

files = sorted(glob.glob(os.path.join(IN_DIR, "*", "*-cty-scaled.csv")))

print("=" * 60)
print("STEP 2: COMBINE NOAA MONTHLY FILES TO DAILY COUNTY DATA")
print("=" * 60)
print(f"Input folder: {IN_DIR}")
print(f"Files found: {len(files)}")

if len(files) == 0:
    raise SystemExit("No NOAA files found. Check IN_DIR path.")

expected_files = 19 * 12 * 4
if len(files) != expected_files:
    print(f"WARNING: expected {expected_files} files, but found {len(files)} files.")


# ============================================================
# READ AND STACK ALL FILES
# ============================================================

all_long = []

for i, fp in enumerate(files, 1):
    fname = os.path.basename(fp)

    if i % 25 == 0 or i == 1:
        print(f"Reading file {i}/{len(files)}: {fname}")

    temp = read_one_file(fp)
    all_long.append(temp)

combined_long = pd.concat(all_long, ignore_index=True)

print("\nFinished reading all monthly files.")
print("Long stacked shape:", combined_long.shape)


# ============================================================
# RESHAPE VARIABLES INTO COLUMNS
# ============================================================

print("\nReshaping variables into columns...")

daily = combined_long.pivot_table(
    index=[
        "region_type",
        "ncei_county_code",
        "county_name",
        "year",
        "month",
        "day",
        "date"
    ],
    columns="variable",
    values="value",
    aggfunc="first"
).reset_index()

daily.columns.name = None

# Sort
daily = daily.sort_values(["ncei_county_code", "date"]).reset_index(drop=True)


# ============================================================
# BASIC CHECKS
# ============================================================

print("\nDaily file shape:")
print(daily.shape)

print("\nColumns:")
print(daily.columns.tolist())

print("\nDate range:")
print(daily["date"].min(), "to", daily["date"].max())

print("\nVariables missing count:")
for v in VARIABLES:
    if v in daily.columns:
        print(f"{v}: {daily[v].isna().sum()}")
    else:
        print(f"{v}: COLUMN MISSING")

print("\nSample rows:")
print(daily.head(10))

print("\nBrookings check:")
brookings = daily[daily["county_name"].str.contains("Brookings", case=False, na=False)]
print(brookings.head(10))


# ============================================================
# SAVE
# ============================================================

print("\nSaving combined daily file...")
daily.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)