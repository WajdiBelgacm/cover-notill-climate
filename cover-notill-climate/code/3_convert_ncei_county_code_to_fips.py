import os
import pandas as pd

# ============================================================
# STEP 3: CONVERT NOAA/NCEI COUNTY CODE TO TRUE FIPS
# Input: daily NOAA county file from Step 2
# Output: daily NOAA county file with true county FIPS
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"

IN_FILE = os.path.join(BASE_DIR, "county_nclimgrid_daily_2000_2018.csv")

CROSSWALK_FILE = os.path.join(BASE_DIR, "us-state-codes_ncei-to-fips.csv")

OUT_FILE = os.path.join(BASE_DIR, "county_nclimgrid_daily_2000_2018_fips.csv")


# ============================================================
# LOAD DATA
# ============================================================

print("Loading daily NOAA county data...")
df = pd.read_csv(IN_FILE)

print("Loading NCEI-to-FIPS state crosswalk...")
cw = pd.read_csv(CROSSWALK_FILE, dtype=str)

print("\nDaily data shape:", df.shape)
print("Crosswalk shape:", cw.shape)

print("\nDaily columns:")
print(df.columns.tolist())

print("\nCrosswalk columns:")
print(cw.columns.tolist())


# ============================================================
# CLEAN COUNTY CODE
# ============================================================

# NOAA county code has NCEI state code + county code.
# Example:
# 39011 = NCEI state code 39 + county code 011
# South Dakota true FIPS state code is 46, so true FIPS = 46011.

df["ncei_county_code"] = df["ncei_county_code"].astype(str).str.zfill(5)

df["ncei_state_code"] = df["ncei_county_code"].str[:2]
df["county_part"] = df["ncei_county_code"].str[2:5]


# ============================================================
# CLEAN CROSSWALK
# ============================================================

cw["NCEI_code"] = cw["NCEI_code"].astype(str).str.zfill(2)
cw["FIPS_code"] = cw["FIPS_code"].astype(str).str.zfill(2)

cw = cw.rename(columns={
    "NCEI_code": "ncei_state_code",
    "FIPS_code": "fips_state_code",
    "state_name": "state_name",
    "postal_code": "state_abbr"
})

cw = cw[["ncei_state_code", "fips_state_code", "state_name", "state_abbr"]]


# ============================================================
# MERGE CROSSWALK
# ============================================================

print("\nMerging NCEI state code to FIPS state code...")

df = df.merge(
    cw,
    on="ncei_state_code",
    how="left"
)

missing = df["fips_state_code"].isna().sum()

print("Rows missing FIPS state code:", missing)

if missing > 0:
    print("\nProblem rows:")
    print(df[df["fips_state_code"].isna()][["ncei_county_code", "county_name"]].drop_duplicates().head(20))
    raise SystemExit("Stop: some NCEI state codes did not match the crosswalk.")


# ============================================================
# CREATE TRUE COUNTY FIPS
# ============================================================

df["fips"] = df["fips_state_code"] + df["county_part"]

# Put useful ID columns first
first_cols = [
    "fips",
    "ncei_county_code",
    "ncei_state_code",
    "fips_state_code",
    "county_part",
    "state_abbr",
    "state_name",
    "county_name",
    "date",
    "year",
    "month",
    "day"
]

other_cols = [c for c in df.columns if c not in first_cols]

df = df[first_cols + other_cols]


# ============================================================
# CHECK BROOKINGS
# ============================================================

print("\nBrookings check:")
brookings = df[df["county_name"].str.contains("Brookings", case=False, na=False)]
print(
    brookings[[
        "ncei_county_code",
        "fips",
        "county_name",
        "state_abbr",
        "date",
        "prcp",
        "tmin",
        "tmax",
        "tavg"
    ]].head(10)
)

print("\nUnique Brookings IDs:")
print(
    brookings[[
        "ncei_county_code",
        "fips",
        "county_name",
        "state_abbr",
        "state_name"
    ]].drop_duplicates()
)


# ============================================================
# SAVE
# ============================================================

print("\nSaving file with true FIPS...")
df.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)

print("\nFinal shape:")
print(df.shape)