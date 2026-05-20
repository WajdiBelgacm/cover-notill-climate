import os
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr

# ============================================================
# STEP 6: CREATE COUNTY-MONTH SPEI-01 FROM GRIDDED SPEI
# Method:
#   Use all SPEI grid-cell centers that fall inside each county polygon,
#   then average those grid-cell SPEI values to county-month level.
#
# Years: 2000–2018
# Counties: 458 counties from Counry_Cover_Notill.csv
# ============================================================

BASE_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC"
SPEI_DIR = os.path.join(BASE_DIR, "SPEI")

SPEI_FILE = os.path.join(
    SPEI_DIR,
    "nclimgrid-spei-gamma-01.nc"
)

COUNTY_SHP = os.path.join(
    SPEI_DIR,
    "tl_2023_us_county",
    "tl_2023_us_county.shp"
)

DV_FILE = os.path.join(
    BASE_DIR,
    "Counry_Cover_Notill.csv"
)

OUT_FILE = os.path.join(
    SPEI_DIR,
    "county_month_spei01_458counties_2000_2018.csv"
)

print("=" * 80)
print("STEP 6: COUNTY-MONTH SPEI-01 FROM POLYGON AGGREGATION")
print("=" * 80)

# ============================================================
# CHECK FILES
# ============================================================

for fp in [SPEI_FILE, COUNTY_SHP, DV_FILE]:
    if not os.path.exists(fp):
        raise SystemExit(f"Missing file:\n{fp}")
    print("Found:", fp)

# ============================================================
# LOAD TARGET COUNTIES
# ============================================================

print("\nLoading dependent-variable county file...")
dv = pd.read_csv(DV_FILE)

dv["fips"] = (
    dv["County_FIPS"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.zfill(5)
)

target_fips = sorted(dv["fips"].dropna().unique())

print("Target counties:", len(target_fips))
print("First 10 target FIPS:", target_fips[:10])

# ============================================================
# LOAD COUNTY POLYGONS
# ============================================================

print("\nLoading county polygons...")
counties = gpd.read_file(COUNTY_SHP)

counties["GEOID"] = counties["GEOID"].astype(str).str.zfill(5)

counties = counties[counties["GEOID"].isin(target_fips)].copy()

print("County polygons after filtering:", counties.shape)
print("Unique county GEOIDs:", counties["GEOID"].nunique())

missing_counties = sorted(set(target_fips) - set(counties["GEOID"]))
if missing_counties:
    print("WARNING: Missing counties from polygon file:")
    print(missing_counties[:50])

# SPEI grid is lon/lat, so use EPSG:4326
counties = counties.to_crs("EPSG:4326")

counties_small = counties[
    ["GEOID", "STATEFP", "NAME", "NAMELSAD", "geometry"]
].copy()

counties_small = counties_small.rename(
    columns={
        "GEOID": "fips",
        "NAME": "county_short_name",
        "NAMELSAD": "county_name"
    }
)

# Bounding box only for speed
minx, miny, maxx, maxy = counties_small.total_bounds
buffer = 0.2
minx -= buffer
miny -= buffer
maxx += buffer
maxy += buffer

print("\nStudy-area bounding box used only for speed:")
print("min lon:", minx)
print("min lat:", miny)
print("max lon:", maxx)
print("max lat:", maxy)

# ============================================================
# OPEN SPEI FILE AND SUBSET TIME/SPACE
# ============================================================

print("\nOpening SPEI NetCDF...")
ds = xr.open_dataset(SPEI_FILE)

spei_var = "spei_01"

if spei_var not in ds.data_vars:
    raise SystemExit(f"Variable {spei_var} not found. Variables are: {list(ds.data_vars)}")

print("SPEI variable:", spei_var)

# Keep 2000–2018 only
ds = ds.sel(time=slice("2000-01-01", "2018-12-01"))

# Keep only rough bounding box
ds = ds.sel(
    lon=slice(minx, maxx),
    lat=slice(miny, maxy)
)

lats = ds["lat"].values
lons = ds["lon"].values
times = pd.to_datetime(ds["time"].values)

print("\nSPEI subset dimensions:")
print(ds.dims)

print("Lat size:", len(lats))
print("Lon size:", len(lons))
print("Time periods:", len(times))
print("Time range:", times.min(), "to", times.max())

# ============================================================
# CREATE GRID-CELL CENTER POINTS
# ============================================================

print("\nCreating SPEI grid-cell center points...")

lon_mesh, lat_mesh = np.meshgrid(lons, lats)

grid_df = pd.DataFrame({
    "grid_id": np.arange(lon_mesh.size),
    "lon": lon_mesh.ravel(),
    "lat": lat_mesh.ravel()
})

grid_gdf = gpd.GeoDataFrame(
    grid_df,
    geometry=gpd.points_from_xy(grid_df["lon"], grid_df["lat"]),
    crs="EPSG:4326"
)

print("Grid-cell centers in bounding box:", grid_gdf.shape[0])

# ============================================================
# SPATIAL JOIN: GRID-CELL CENTERS INSIDE COUNTY POLYGONS
# ============================================================

print("\nAssigning grid-cell centers to county polygons...")

joined = gpd.sjoin(
    grid_gdf,
    counties_small,
    how="inner",
    predicate="within"
)

print("Joined grid-cell centers:", joined.shape[0])
print("Counties with at least one grid-cell center:", joined["fips"].nunique())

missing_after_join = sorted(set(target_fips) - set(joined["fips"]))
if missing_after_join:
    print("\nWARNING: Counties with no grid-cell center inside polygon:")
    print(missing_after_join[:50])
    print("These counties may be very small or coastal. We can handle them later if needed.")

cell_map = joined[
    [
        "grid_id",
        "lat",
        "lon",
        "fips",
        "STATEFP",
        "county_name",
        "county_short_name"
    ]
].copy()

nlon = len(lons)
cell_map["lat_idx"] = cell_map["grid_id"] // nlon
cell_map["lon_idx"] = cell_map["grid_id"] % nlon

print("\nCell map preview:")
print(cell_map.head())

print("\nGrid cells per county summary:")
print(cell_map.groupby("fips").size().describe())

# ============================================================
# AGGREGATE MONTHLY SPEI TO COUNTY-MONTH
# ============================================================

print("\nAggregating monthly SPEI to counties...")

records = []

for t_idx, date in enumerate(times):
    if t_idx == 0 or (t_idx + 1) % 12 == 0:
        print(f"Processing {t_idx + 1}/{len(times)}: {date.strftime('%Y-%m')}")

    # One monthly SPEI grid
    arr = ds[spei_var].isel(time=t_idx).values

    temp = cell_map.copy()
    temp["spei01"] = arr[
        temp["lat_idx"].values,
        temp["lon_idx"].values
    ]

    monthly = (
        temp.groupby(
            ["fips", "STATEFP", "county_name", "county_short_name"],
            as_index=False
        )
        .agg(
            spei01=("spei01", "mean"),
            n_grid_cells=("spei01", "count")
        )
    )

    monthly["date"] = date
    monthly["year"] = date.year
    monthly["month"] = date.month

    records.append(monthly)

county_month = pd.concat(records, ignore_index=True)

county_month = county_month[
    [
        "fips",
        "STATEFP",
        "county_name",
        "county_short_name",
        "date",
        "year",
        "month",
        "spei01",
        "n_grid_cells"
    ]
].copy()

county_month = county_month.sort_values(["fips", "date"]).reset_index(drop=True)

# ============================================================
# CHECKS
# ============================================================

print("\nCounty-month SPEI shape:")
print(county_month.shape)

print("\nYear range:")
print(county_month["year"].min(), "to", county_month["year"].max())

print("\nNumber of counties:")
print(county_month["fips"].nunique())

print("\nMonths per county:")
print(county_month.groupby("fips")["date"].nunique().describe())

print("\nMissing SPEI values:")
print(county_month["spei01"].isna().sum())

print("\nFirst rows:")
print(county_month.head())

print("\nBrookings check:")
print(county_month[county_month["fips"] == "46011"].head(15))

expected_rows = len(target_fips) * 19 * 12
actual_rows = len(county_month)

print("\nExpected rows:", expected_rows)
print("Actual rows:", actual_rows)

if expected_rows == actual_rows:
    print("GOOD: row count matches 458 counties × 19 years × 12 months.")
else:
    print("WARNING: row count does not match expected county-month panel.")

# ============================================================
# SAVE
# ============================================================

county_month.to_csv(OUT_FILE, index=False)

print("\nDONE.")
print("Saved file:")
print(OUT_FILE)