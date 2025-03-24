#!/bin/bash

# Script to run the WRF Setup Tool
# This will execute the Python script to configure WRF and download data

echo "Starting WRF Setup Tool..."
python wrf_setup.py

echo
echo "Setup complete! Check the output directory for namelist files and download script."
echo "Make sure to check and modify paths in the namelist files as needed."
echo
echo "To download meteorological data, run the download_data.sh script in your output directory."