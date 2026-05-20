# Cover Crop, No-Till, and Climate Data

This repository contains code used to construct a county-year panel of cover crop and no-till outcomes merged with annual climate, SPEI drought/wetness, and non-frost-day measures for 458 counties from 2005–2018.

The purpose of this repository is to document the data-processing workflow and make the code reproducible. The final cleaned dataset is not currently uploaded and can be shared upon reasonable request.

## Repository structure

- `cover-notill-climate/code/`: Python scripts used to download, process, aggregate, and merge the data.
- `cover-notill-climate/data_dictionary/`: Variable definitions and column descriptions.

## Data sources

The raw climate data come from public sources, including NOAA nClimGrid-Daily and NOAA/NIDIS SPEI products. Large raw files are not stored in this repository.

## Workflow

The scripts are numbered in the order they should be run:

1. Download NOAA county-level climate files.
2. Combine monthly NOAA files into daily county-level files.
3. Convert NCEI county codes to FIPS codes.
4. Create annual climate variables for 458 counties.
5. Merge annual climate variables with cover crop and no-till data.
6. Create county-month SPEI variables.
7. Create annual SPEI drought and wetness indicators.
8. Merge SPEI lag variables with cover crop and no-till data.
9. Add non-frost-day lag variables.

## Data availability

The final cleaned dataset is not currently included in this repository. It may be made available upon reasonable request.

Large raw climate files, NetCDF files, GeoTIFF files, and intermediate processing files are not uploaded to GitHub. Users should download the raw data from the original public sources and run the scripts in order.

## Notes

This repository is intended for transparency and reproducibility of the data-construction workflow. The code may require local path adjustments depending on the user's folder structure.
