import os
import pandas as pd

# ============================================================
# STEP 7: CREATE ANNUAL SPEI CATEGORY MONTH VARIABLES
#
# Input:
#   county_month_spei01_458counties_2000_2018.csv
#
# Output:
#   county_year_spei01_d0d4_w0w4_458counties_2000_2018.csv
#
# Categories from Drought.gov-style SPEI thresholds:
#
# Dry:
#   D0: -0.7 <= SPEI <= -0.5
#   D1: -1.2 <= SPEI <= -0.8
#   D2: -1.5 <= SPEI <= -1.3
#   D3: -1.9 <= SPEI <= -1.6
#   D4: SPEI <= -2.0
#
# Wet:
#   W0:  0.5 <= SPEI <= 0.7
#   W1:  0.8 <= SPEI <= 1.2
#   W2:  1.3 <= SPEI <= 1.5
#   W3:  1.6 <= SPEI <= 1.9
#   W4:  SPEI >= 2.0
# ============================================================

SPEI_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC\SPEI"

IN_FILE = os.path.join(
    SPEI_DIR,
    "county_month_spei01_458counties_2000_2018.csv"
)

OUT_FILE = os.path.join(
    SPEI_DIR,
    "county_year_spei01_d0d4_w0w4_458counties_2000_2018.csv"
)

print("=" * 80)
print("STEP 7: CREATE ANNUAL SPEI D0-D4 AND W0-W4 VARIABLES")
print("=" * 80)

if not os.path.exists(IN_FILE):
    raise SystemExit(f"Missing input file:\n{IN_FILE}")

print("Loading county-month SPEI file...")
df = pd.read_csv(IN_FILE)

print("Input shape:", df.shape)
print("Columns:")
print(df.columns.tolist())

# ============================================================
# CLEAN VARIABLES
# ============================================================

df["fips"] = (
    df["fips"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

df["year"] = df["year"].astype(int)
df["month"] = df["month"].astype(int)
df["spei01"] = pd.to_numeric(df["spei01"], errors="coerce")

# Cap values to expected SPEI bounds
df["spei01"] = df["spei01"].clip(lower=-3.09, upper=3.09)

# ============================================================
# CREATE MONTHLY CATEGORY INDICATORS
# ============================================================

# Dry categories: exact category ranges
df["spei01_d0"] = ((df["spei01"] >= -0.7) & (df["spei01"] <= -0.5)).astype(int)
df["spei01_d1"] = ((df["spei01"] >= -1.2) & (df["spei01"] <= -0.8)).astype(int)
df["spei01_d2"] = ((df["spei01"] >= -1.5) & (df["spei01"] <= -1.3)).astype(int)
df["spei01_d3"] = ((df["spei01"] >= -1.9) & (df["spei01"] <= -1.6)).astype(int)
df["spei01_d4"] = (df["spei01"] <= -2.0).astype(int)

# Wet categories: exact category ranges
df["spei01_w0"] = ((df["spei01"] >= 0.5) & (df["spei01"] <= 0.7)).astype(int)
df["spei01_w1"] = ((df["spei01"] >= 0.8) & (df["spei01"] <= 1.2)).astype(int)
df["spei01_w2"] = ((df["spei01"] >= 1.3) & (df["spei01"] <= 1.5)).astype(int)
df["spei01_w3"] = ((df["spei01"] >= 1.6) & (df["spei01"] <= 1.9)).astype(int)
df["spei01_w4"] = (df["spei01"] >= 2.0).astype(int)

# ============================================================
# AGGREGATE TO COUNTY-YEAR
# ============================================================

print("\nAggregating monthly indicators to county-year...")

annual = (
    df.groupby(
        ["fips", "STATEFP", "county_name", "county_short_name", "year"],
        as_index=False
    )
    .agg(
        spei01_mean=("spei01", "mean"),
        spei01_min=("spei01", "min"),
        spei01_max=("spei01", "max"),

        spei01_d0_months=("spei01_d0", "sum"),
        spei01_d1_months=("spei01_d1", "sum"),
        spei01_d2_months=("spei01_d2", "sum"),
        spei01_d3_months=("spei01_d3", "sum"),
        spei01_d4_months=("spei01_d4", "sum"),

        spei01_w0_months=("spei01_w0", "sum"),
        spei01_w1_months=("spei01_w1", "sum"),
        spei01_w2_months=("spei01_w2", "sum"),
        spei01_w3_months=("spei01_w3", "sum"),
        spei01_w4_months=("spei01_w4", "sum"),

        n_months=("month", "count")
    )
)

annual = annual.sort_values(["fips", "year"]).reset_index(drop=True)

# ============================================================
# CHECKS
# ============================================================

print("\nAnnual SPEI shape:")
print(annual.shape)

print("\nYear range:")
print(annual["year"].min(), "to", annual["year"].max())

print("\nNumber of counties:")
print(annual["fips"].nunique())

print("\nMonths per county-year:")
print(annual["n_months"].describe())

print("\nFirst rows:")
print(annual.head())

print("\nBrookings check:")
print(annual[annual["fips"] == "46011"].head(20))

expected_rows = 458 * 19
actual_rows = len(annual)

print("\nExpected rows:", expected_rows)
print("Actual rows:", actual_rows)

if actual_rows == expected_rows:
    print("GOOD: row count matches 458 counties × 19 years.")
else:
    print("WARNING: row count does not match expected.")

category_cols = [
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

print("\nMissing values:")
print(annual.isna().sum())

print("\nSummary of D0-D4 and W0-W4 month variables:")
print(annual[category_cols].describe())

print("\nChecking if all category counts are between 0 and 12:")
for col in category_cols:
    print(f"{col}: min={annual[col].min()}, max={annual[col].max()}")

# Check total classified dry/wet months per county-year
annual["spei01_total_dry_category_months"] = annual[
    [
        "spei01_d0_months",
        "spei01_d1_months",
        "spei01_d2_months",
        "spei01_d3_months",
        "spei01_d4_months",
    ]
].sum(axis=1)

annual["spei01_total_wet_category_months"] = annual[
    [
        "spei01_w0_months",
        "spei01_w1_months",
        "spei01_w2_months",
        "spei01_w3_months",
        "spei01_w4_months",
    ]
].sum(axis=1)

print("\nTotal dry-category months summary:")
print(annual["spei01_total_dry_category_months"].describe())

print("\nTotal wet-category months summary:")
print(annual["spei01_total_wet_category_months"].describe())

# ============================================================
# SAVE
# ============================================================

annual.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)