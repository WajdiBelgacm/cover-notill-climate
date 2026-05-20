import os
import time
import requests

# ============================================================
# DOWNLOAD NOAA nClimGrid-Daily COUNTY FILES
# Years: 2000–2018
# Months: January–December
# Variables: prcp, tmin, tmax, tavg
# Region: county-level area averages
# Status: scaled
# ============================================================

BASE_URL = "https://www.ncei.noaa.gov/data/nclimgrid-daily/access/averages"

OUT_DIR = r"C:\Users\wajdi.belgacem\Desktop\Cover crop data CTIC\nclimgrid_county_raw_2000_2018"

START_YEAR = 2000
END_YEAR = 2018

VARIABLES = ["prcp", "tmin", "tmax", "tavg"]
MONTHS = range(1, 13)

os.makedirs(OUT_DIR, exist_ok=True)


def download_file(url, out_path, max_retries=3):
    """
    Download one file with retry logic.
    Skips file if it already exists.
    """

    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        print(f"Already exists: {os.path.basename(out_path)}")
        return True

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Downloading: {os.path.basename(out_path)}")

            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(response.content)

                print(f"Saved: {out_path}")
                return True

            else:
                print(f"FAILED status {response.status_code}: {url}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt} failed:")
            print(e)
            time.sleep(3)

    return False


# ============================================================
# MAIN LOOP
# ============================================================

total_files = 0
success_files = 0
failed_files = []

for year in range(START_YEAR, END_YEAR + 1):

    year_dir = os.path.join(OUT_DIR, str(year))
    os.makedirs(year_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print(f"YEAR {year}")
    print("=" * 60)

    for month in MONTHS:

        ym = f"{year}{month:02d}"

        for var in VARIABLES:

            total_files += 1

            filename = f"{var}-{ym}-cty-scaled.csv"
            url = f"{BASE_URL}/{year}/{filename}"
            out_path = os.path.join(year_dir, filename)

            ok = download_file(url, out_path)

            if ok:
                success_files += 1
            else:
                failed_files.append(url)

print("\n" + "=" * 60)
print("DOWNLOAD SUMMARY")
print("=" * 60)
print(f"Total expected files: {total_files}")
print(f"Successfully downloaded/skipped existing: {success_files}")
print(f"Failed files: {len(failed_files)}")

if failed_files:
    print("\nFailed URLs:")
    for url in failed_files:
        print(url)

print("\nDone.")