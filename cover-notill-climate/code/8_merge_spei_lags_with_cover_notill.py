import os
import pandas as pd

# ============================================================
# STEP 8: CREATE SPEI LAGS AND MERGE WITH FINAL COVER/NO-TILL DATA
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"
SPEI_DIR = os.path.join(BASE_DIR, "SPEI")

MAIN_FILE = os.path.join(
    BASE_DIR,
    "cover_notill_with_annual_climate_lags_2005_2018.csv"
)

SPEI_FILE = os.path.join(
    SPEI_DIR,
    "county_year_spei01_d0d4_w0w4_458counties_2000_2018.csv"
)

OUT_FILE = os.path.join(
    BASE_DIR,
    "cover_notill_with_climate_and_spei_lags_2005_2018.csv"
)

print("=" * 80)
print("STEP 8: MERGE SPEI LAGS WITH COVER/NO-TILL FINAL DATA")
print("=" * 80)

if not os.path.exists(MAIN_FILE):
    raise SystemExit(f"Missing main file:\n{MAIN_FILE}")

if not os.path.exists(SPEI_FILE):
    raise SystemExit(f"Missing SPEI file:\n{SPEI_FILE}")

# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading main cover/no-till + climate file...")
main = pd.read_csv(MAIN_FILE)

print("Main shape:", main.shape)
print("Main columns:")
print(main.columns.tolist())

print("\nLoading annual SPEI file...")
spei = pd.read_csv(SPEI_FILE)

print("SPEI shape:", spei.shape)
print("SPEI columns:")
print(spei.columns.tolist())

# ============================================================
# CLEAN IDS
# ============================================================

# Main file uses County_FIPS and Year, not fips and year
main["fips"] = (
    main["County_FIPS"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

main["year"] = main["Year"].astype(int)

spei["fips"] = (
    spei["fips"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

spei["year"] = spei["year"].astype(int)

# SPEI variables to lag
spei_vars = [
    "spei01_d0_months",
    "spei01_d1_months",
    "spei01_d2_months",
    "spei01_d3_months",
    "spei01_d4_months",
    "spei01_w0_months",
    "spei01_w1_months",
    "spei01_w2_months",
    "spei01_w3_months",
    "spei01_w4_months",
]

# Make sure SPEI variables are numeric
for col in spei_vars:
    spei[col] = pd.to_numeric(spei[col], errors="coerce")

# ============================================================
# MERGE LAGS
# ============================================================

merged = main.copy()

for lag in [0, 1, 2, 3]:

    temp = spei[["fips", "year"] + spei_vars].copy()

    # For outcome year t:
    # lag0 uses SPEI year t
    # lag1 uses SPEI year t-1
    # lag2 uses SPEI year t-2
    # lag3 uses SPEI year t-3
    temp["year"] = temp["year"] + lag

    rename_dict = {
        var: f"{var}_lag{lag}"
        for var in spei_vars
    }

    temp = temp.rename(columns=rename_dict)

    print(f"\nMerging SPEI lag {lag}...")
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

print("\nRows before merge:", len(main))
print("Rows after merge:", len(merged))

if len(main) == len(merged):
    print("GOOD: merge did not change number of rows.")
else:
    print("WARNING: merge changed number of rows.")

print("\nYear range:")
print(merged["year"].min(), "to", merged["year"].max())

print("\nNumber of counties:")
print(merged["fips"].nunique())

spei_lag_cols = [
    c for c in merged.columns
    if c.startswith("spei01_") and "_lag" in c
]

print("\nNumber of SPEI lag columns:")
print(len(spei_lag_cols))

print("\nMissing values in SPEI lag columns:")
print(merged[spei_lag_cols].isna().sum())

print("\nRows with any missing SPEI lag:")
print(merged[spei_lag_cols].isna().any(axis=1).sum())

print("\nFirst rows:")
print(merged.head())

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