import os
import pandas as pd

# ============================================================
# STEP 4: CREATE ANNUAL CLIMATE VARIABLES FOR 458 COUNTIES
# Variables:
#   annual_prcp
#   annual_tavg
#   annual_tmin
#   annual_tmax
#
# Years: 2000–2018
# No GDD / No EDD
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"

CLIMATE_DAILY_FILE = os.path.join(
    BASE_DIR,
    "county_nclimgrid_daily_2000_2018_fips.csv"
)

DV_FILE = os.path.join(
    BASE_DIR,
    "Counry_Cover_Notill.csv"
)

OUT_FILE = os.path.join(
    BASE_DIR,
    "county_year_annual_climate_458counties_2000_2018.csv"
)

print("=" * 70)
print("STEP 4: ANNUAL CLIMATE VARIABLES")
print("=" * 70)

print("\nChecking input files...")

if not os.path.exists(CLIMATE_DAILY_FILE):
    raise SystemExit(f"Missing climate file:\n{CLIMATE_DAILY_FILE}")

if not os.path.exists(DV_FILE):
    raise SystemExit(f"Missing dependent-variable file:\n{DV_FILE}")

print("Climate file found:")
print(CLIMATE_DAILY_FILE)

print("Dependent-variable file found:")
print(DV_FILE)

# ============================================================
# LOAD DEPENDENT VARIABLE FILE TO GET TARGET COUNTIES
# ============================================================

print("\nLoading dependent-variable county file...")
dv = pd.read_csv(DV_FILE)

print("DV file shape:", dv.shape)
print("DV columns:")
print(dv.columns.tolist())

possible_fips_cols = [
    c for c in dv.columns
    if "fips" in c.lower() or "geoid" in c.lower()
]

if not possible_fips_cols:
    raise SystemExit("No FIPS/GEOID column found in dependent-variable file.")

dv_fips_col = possible_fips_cols[0]
print("\nUsing DV FIPS column:", dv_fips_col)

dv["fips"] = (
    dv[dv_fips_col]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

target_fips = sorted(dv["fips"].dropna().unique())

print("Number of target counties:", len(target_fips))
print("First 10 target FIPS:", target_fips[:10])

# ============================================================
# LOAD DAILY CLIMATE FILE
# ============================================================

print("\nLoading daily climate file...")
clim = pd.read_csv(CLIMATE_DAILY_FILE)

print("Climate daily shape before filtering:", clim.shape)
print("Climate columns:")
print(clim.columns.tolist())

clim["fips"] = (
    clim["fips"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

clim = clim[clim["fips"].isin(target_fips)].copy()

print("Climate daily shape after filtering:", clim.shape)
print("Number of climate counties after filtering:", clim["fips"].nunique())

# ============================================================
# CLEAN VARIABLES
# ============================================================

clim["date"] = pd.to_datetime(clim["date"])
clim["year"] = clim["year"].astype(int)

for col in ["prcp", "tavg", "tmin", "tmax"]:
    clim[col] = pd.to_numeric(clim[col], errors="coerce")

clim = clim[(clim["year"] >= 2000) & (clim["year"] <= 2018)].copy()

# ============================================================
# CREATE ANNUAL COUNTY-YEAR VARIABLES
# ============================================================

print("\nCreating annual county-year climate variables...")

annual = (
    clim.groupby(
        ["fips", "county_name", "state_abbr", "state_name", "year"],
        as_index=False
    )
    .agg(
        annual_prcp=("prcp", "sum"),
        annual_tavg=("tavg", "mean"),
        annual_tmin=("tmin", "mean"),
        annual_tmax=("tmax", "mean"),
        n_days=("date", "count")
    )
)

# ============================================================
# CHECKS
# ============================================================

print("\nAnnual climate shape:")
print(annual.shape)

print("\nYear range:")
print(annual["year"].min(), "to", annual["year"].max())

print("\nNumber of counties:")
print(annual["fips"].nunique())

print("\nDays per county-year:")
print(annual["n_days"].describe())

print("\nFirst rows:")
print(annual.head())

print("\nBrookings check:")
brookings = annual[annual["county_name"].str.contains("Brookings", case=False, na=False)]
print(brookings.head(10))

expected_rows = len(target_fips) * 19
actual_rows = len(annual)

print("\nExpected rows:", expected_rows)
print("Actual rows:", actual_rows)

if actual_rows != expected_rows:
    print("WARNING: actual rows do not equal expected counties × 19 years.")
else:
    print("GOOD: row count matches expected county-year panel.")

print("\nMissing values:")
print(annual[["annual_prcp", "annual_tavg", "annual_tmin", "annual_tmax"]].isna().sum())

# ============================================================
# SAVE
# ============================================================

annual.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)