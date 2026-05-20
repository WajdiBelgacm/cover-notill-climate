import os
import pandas as pd

# ============================================================
# STEP 5: MERGE COVER/NO-TILL DATA WITH ANNUAL CLIMATE LAGS
#
# Input 1: Counry_Cover_Notill.csv
# Input 2: county_year_annual_climate_458counties_2000_2018.csv
#
# Output:
#   cover_notill_with_annual_climate_lags_2005_2018.csv
#
# Lags:
#   lag0 = climate in same year t
#   lag1 = climate in year t-1
#   lag2 = climate in year t-2
#   lag3 = climate in year t-3
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"

DV_FILE = os.path.join(BASE_DIR, "Counry_Cover_Notill.csv")

CLIMATE_FILE = os.path.join(
    BASE_DIR,
    "county_year_annual_climate_458counties_2000_2018.csv"
)

OUT_FILE = os.path.join(
    BASE_DIR,
    "cover_notill_with_annual_climate_lags_2005_2018.csv"
)

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("STEP 5: MERGE COVER/NO-TILL WITH ANNUAL CLIMATE LAGS")
print("=" * 70)

print("\nLoading dependent-variable file...")
dv = pd.read_csv(DV_FILE)

print("DV shape:", dv.shape)
print("DV columns:")
print(dv.columns.tolist())

print("\nLoading annual climate file...")
clim = pd.read_csv(CLIMATE_FILE)

print("Climate shape:", clim.shape)
print("Climate columns:")
print(clim.columns.tolist())

# ============================================================
# CLEAN IDS
# ============================================================

dv["fips"] = (
    dv["County_FIPS"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

dv["year"] = dv["Year"].astype(int)

clim["fips"] = (
    clim["fips"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

clim["year"] = clim["year"].astype(int)

# Keep climate variables only
climate_vars = [
    "annual_prcp",
    "annual_tavg",
    "annual_tmin",
    "annual_tmax"
]

# ============================================================
# CREATE LAGGED CLIMATE DATASETS AND MERGE
# ============================================================

merged = dv.copy()

for lag in [0, 1, 2, 3]:

    temp = clim[["fips", "year"] + climate_vars].copy()

    # For outcome year t, lag k uses climate year t-k.
    # So shift climate year forward by k to match outcome year.
    temp["year"] = temp["year"] + lag

    rename_dict = {
        var: f"{var}_lag{lag}"
        for var in climate_vars
    }

    temp = temp.rename(columns=rename_dict)

    print(f"\nMerging lag {lag} climate variables...")
    print("Temp year range after shifting:", temp["year"].min(), "to", temp["year"].max())

    merged = merged.merge(
        temp,
        on=["fips", "year"],
        how="left"
    )

# ============================================================
# CHECKS
# ============================================================

print("\nMerged shape:")
print(merged.shape)

print("\nYear range:")
print(merged["year"].min(), "to", merged["year"].max())

print("\nNumber of counties:")
print(merged["fips"].nunique())

print("\nFirst rows:")
print(merged.head())

# Check missing values in climate lag columns
lag_cols = [
    c for c in merged.columns
    if c.startswith("annual_") and "_lag" in c
]

print("\nMissing values in lagged climate columns:")
print(merged[lag_cols].isna().sum())

print("\nRows with any missing lagged climate:")
print(merged[lag_cols].isna().any(axis=1).sum())

# Check expected outcome rows
print("\nDV rows before merge:", len(dv))
print("Rows after merge:", len(merged))

if len(dv) == len(merged):
    print("GOOD: merge did not change number of outcome rows.")
else:
    print("WARNING: merge changed number of rows.")

# Brookings check
print("\nBrookings check:")
brookings = merged[
    merged["County_Name"].astype(str).str.contains("Brookings", case=False, na=False)
]
print(brookings.head(10))

# ============================================================
# SAVE
# ============================================================

merged.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)