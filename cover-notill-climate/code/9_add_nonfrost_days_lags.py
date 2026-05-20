import os
import pandas as pd

# ============================================================
# STEP 9: CREATE ANNUAL NON-FROST DAYS AND MERGE LAGS
#
# Definition:
#   nonfrost_days = number of days in a year with Tmin > 0°C
#
# Input 1:
#   county_nclimgrid_daily_2000_2018_fips.csv
#
# Input 2:
#   cover_notill_with_climate_and_spei_lags_2005_2018.csv
#
# Output 1:
#   county_year_nonfrost_days_458counties_2000_2018.csv
#
# Output 2:
#   cover_notill_with_climate_spei_nonfrost_lags_2005_2018.csv
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"

DAILY_CLIMATE_FILE = os.path.join(
    BASE_DIR,
    "county_nclimgrid_daily_2000_2018_fips.csv"
)

MAIN_FILE = os.path.join(
    BASE_DIR,
    "cover_notill_with_climate_and_spei_lags_2005_2018.csv"
)

OUT_ANNUAL_NONFROST = os.path.join(
    BASE_DIR,
    "county_year_nonfrost_days_458counties_2000_2018.csv"
)

OUT_FINAL = os.path.join(
    BASE_DIR,
    "cover_notill_with_climate_spei_nonfrost_lags_2005_2018.csv"
)

print("=" * 80)
print("STEP 9: ADD ANNUAL NON-FROST DAYS")
print("=" * 80)

# ============================================================
# CHECK INPUT FILES
# ============================================================

if not os.path.exists(DAILY_CLIMATE_FILE):
    raise SystemExit(f"Missing daily climate file:\n{DAILY_CLIMATE_FILE}")

if not os.path.exists(MAIN_FILE):
    raise SystemExit(f"Missing main modeling file:\n{MAIN_FILE}")

print("\nDaily climate file found:")
print(DAILY_CLIMATE_FILE)

print("\nMain modeling file found:")
print(MAIN_FILE)

# ============================================================
# LOAD MAIN MODELING FILE
# ============================================================

print("\nLoading main modeling file...")
main = pd.read_csv(MAIN_FILE)

print("Main shape:", main.shape)
print("Main columns:")
print(main.columns.tolist())

# Main file uses County_FIPS and Year, not fips/year
main["fips"] = (
    main["County_FIPS"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

main["year"] = main["Year"].astype(int)

target_fips = sorted(main["fips"].dropna().unique())

print("\nTarget counties:", len(target_fips))
print("Main file year range:", main["year"].min(), "to", main["year"].max())
print("First 10 FIPS:", target_fips[:10])

# ============================================================
# LOAD DAILY CLIMATE FILE
# ============================================================

print("\nLoading daily climate file...")
clim = pd.read_csv(DAILY_CLIMATE_FILE)

print("Daily climate shape before filtering:", clim.shape)
print("Daily climate columns:")
print(clim.columns.tolist())

clim["fips"] = (
    clim["fips"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

clim["year"] = clim["year"].astype(int)
clim["tmin"] = pd.to_numeric(clim["tmin"], errors="coerce")

# Keep only target counties and years needed for lag construction
clim = clim[
    (clim["fips"].isin(target_fips)) &
    (clim["year"] >= 2000) &
    (clim["year"] <= 2018)
].copy()

print("\nDaily climate shape after filtering:", clim.shape)
print("Number of counties after filtering:", clim["fips"].nunique())
print("Year range after filtering:", clim["year"].min(), "to", clim["year"].max())

# ============================================================
# CREATE DAILY NON-FROST INDICATOR
# ============================================================

# Professor's definition:
# non-frost day = daily minimum temperature greater than 0°C
clim["nonfrost_day"] = (clim["tmin"] > 0).astype(int)

# ============================================================
# AGGREGATE TO COUNTY-YEAR
# ============================================================

print("\nCreating annual non-frost days...")

nonfrost = (
    clim.groupby(
        ["fips", "county_name", "state_abbr", "state_name", "year"],
        as_index=False
    )
    .agg(
        nonfrost_days=("nonfrost_day", "sum"),
        n_days=("tmin", "count")
    )
)

nonfrost = nonfrost.sort_values(["fips", "year"]).reset_index(drop=True)

# ============================================================
# CHECK ANNUAL NON-FROST DATA
# ============================================================

print("\nAnnual non-frost shape:")
print(nonfrost.shape)

print("\nYear range:")
print(nonfrost["year"].min(), "to", nonfrost["year"].max())

print("\nNumber of counties:")
print(nonfrost["fips"].nunique())

print("\nNon-frost days summary:")
print(nonfrost["nonfrost_days"].describe())

print("\nDays per county-year:")
print(nonfrost["n_days"].describe())

print("\nFirst rows:")
print(nonfrost.head())

print("\nBrookings annual non-frost check:")
print(nonfrost[nonfrost["fips"] == "46011"].head(20))

expected_rows = len(target_fips) * 19
actual_rows = len(nonfrost)

print("\nExpected annual non-frost rows:", expected_rows)
print("Actual annual non-frost rows:", actual_rows)

if expected_rows == actual_rows:
    print("GOOD: annual non-frost panel has expected rows.")
else:
    print("WARNING: annual non-frost panel row count is not expected.")

print("\nMissing values in annual non-frost file:")
print(nonfrost.isna().sum())

# Save annual non-frost file
print("\nSaving annual non-frost file...")
nonfrost.to_csv(OUT_ANNUAL_NONFROST, index=False)

print("Saved:")
print(OUT_ANNUAL_NONFROST)

# ============================================================
# CREATE LAGS AND MERGE WITH MAIN MODELING FILE
# ============================================================

print("\nCreating non-frost lag variables and merging...")

merged = main.copy()

for lag in [0, 1, 2, 3]:

    temp = nonfrost[["fips", "year", "nonfrost_days"]].copy()

    # For outcome year t:
    # lag0 = non-frost days in year t
    # lag1 = non-frost days in year t-1
    # lag2 = non-frost days in year t-2
    # lag3 = non-frost days in year t-3
    temp["year"] = temp["year"] + lag

    temp = temp.rename(
        columns={
            "nonfrost_days": f"nonfrost_days_lag{lag}"
        }
    )

    print(f"\nMerging non-frost lag {lag}...")
    print("Temp year range after shifting:", temp["year"].min(), "to", temp["year"].max())

    merged = merged.merge(
        temp,
        on=["fips", "year"],
        how="left"
    )

# ============================================================
# FINAL CHECKS
# ============================================================

print("\nMerged final shape:")
print(merged.shape)

print("\nRows before merge:", len(main))
print("Rows after merge:", len(merged))

if len(main) == len(merged):
    print("GOOD: merge did not change number of rows.")
else:
    print("WARNING: merge changed number of rows.")

nonfrost_lag_cols = [
    "nonfrost_days_lag0",
    "nonfrost_days_lag1",
    "nonfrost_days_lag2",
    "nonfrost_days_lag3"
]

print("\nMissing values in non-frost lag columns:")
print(merged[nonfrost_lag_cols].isna().sum())

print("\nRows with any missing non-frost lag:")
print(merged[nonfrost_lag_cols].isna().any(axis=1).sum())

print("\nSummary of non-frost lag variables:")
print(merged[nonfrost_lag_cols].describe())

print("\nBrookings final check:")
brookings = merged[
    merged["County_Name"].astype(str).str.contains("Brookings", case=False, na=False)
]

print(
    brookings[
        ["County_FIPS", "County_Name", "State_Name", "Year"] + nonfrost_lag_cols
    ].head(15)
)

# ============================================================
# SAVE FINAL FILE
# ============================================================

merged.to_csv(OUT_FINAL, index=False)

print("\nDONE.")
print("Saved final file:")
print(OUT_FINAL)