#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WRF Model Setup Tool

This script helps users to:
1. Configure WRF namelist files (namelist.wps and namelist.input)
2. Download required meteorological data from appropriate sources
3. Set up domain, projection, physics options, and simulation duration

Author: AI Assistant
Date: 2025-03-20
"""

import os
import sys
import datetime
import subprocess
import argparse
import json
import requests
from dateutil.relativedelta import relativedelta

class WRFSetup:
    def __init__(self):
        self.config = {
            "start_date": None,
            "end_date": None,
            "domain": {
                "e_we": None,
                "e_sn": None,
                "dx": None,
                "dy": None,
                "ref_lat": None,
                "ref_lon": None,
                "truelat1": None,
                "truelat2": None,
                "stand_lon": None,
                "max_dom": 1,
                "parent_grid_ratio": [1, 3, 3],
                "i_parent_start": [1, 31, 31],
                "j_parent_start": [1, 17, 33],
                "parent_time_step_ratio": [1, 3, 3]
            },
            "projection": None,
            "physics": {
                "mp_physics": None,
                "ra_lw_physics": None,
                "ra_sw_physics": None,
                "sf_surface_physics": None,
                "bl_pbl_physics": None,
                "cu_physics": None
            },
            "data_source": None,
            "output_dir": "./wrf_run"
        }
        
        # Available options for physics schemes
        self.physics_options = {
            "mp_physics": {
                1: "Kessler scheme",
                2: "Lin et al. scheme",
                3: "WSM3 scheme",
                4: "WSM5 scheme",
                6: "WSM6 scheme",
                8: "Thompson scheme",
                10: "Morrison 2-moment scheme"
            },
            "ra_lw_physics": {
                1: "RRTM scheme",
                3: "CAM scheme",
                4: "RRTMG scheme"
            },
            "ra_sw_physics": {
                1: "Dudhia scheme",
                2: "Goddard shortwave",
                3: "CAM scheme",
                4: "RRTMG scheme"
            },
            "sf_surface_physics": {
                1: "Thermal diffusion scheme",
                2: "Noah Land Surface Model",
                3: "RUC Land Surface Model",
                4: "Noah-MP Land Surface Model"
            },
            "bl_pbl_physics": {
                1: "YSU scheme",
                2: "Mellor-Yamada-Janjic scheme",
                4: "QNSE scheme",
                5: "MYNN2 scheme",
                6: "MYNN3 scheme"
            },
            "cu_physics": {
                0: "No cumulus",
                1: "Kain-Fritsch scheme",
                2: "Betts-Miller-Janjic scheme",
                3: "Grell-Freitas scheme",
                5: "Grell-3D scheme"
            }
        }
        
        # Available map projections
        self.projections = {
            1: "Lambert Conformal",
            2: "Polar Stereographic",
            3: "Mercator",
            6: "Lat-Lon (including global)"
        }
        
        # Available data sources
        self.data_sources = {
            "GFS": "NCEP Global Forecast System",
            "ERA5": "ECMWF ERA5 Reanalysis",
            "FNL": "NCEP Final Analysis",
            "NARR": "North American Regional Reanalysis"
        }
    
    def show_menu(self):
        """Display the main menu and get user choices"""
        print("\n===== WRF Model Setup Tool =====\n")
        
        # 1. Set simulation period
        self.set_simulation_period()
        
        # 2. Set domain configuration
        self.set_domain_config()
        
        # 3. Set map projection
        self.set_map_projection()
        
        # 4. Set physics options
        self.set_physics_options()
        
        # 5. Set data source
        self.set_data_source()
        
        # 6. Set output directory
        self.config["output_dir"] = input("\nEnter output directory path [./wrf_run]: ") or "./wrf_run"
        
        # Show summary
        self.show_summary()
        
        # Confirm and proceed
        proceed = input("\nProceed with this configuration? (y/n): ")
        if proceed.lower() == 'y':
            self.create_output_dir()
            self.create_namelist_wps()
            self.create_namelist_input()
            self.download_data()
            print("\nSetup complete! You can now proceed with your WRF simulation.")
        else:
            print("\nSetup cancelled. Please run the script again to configure WRF.")
    
    def set_simulation_period(self):
        """Set the simulation start and end dates"""
        print("\n--- Simulation Period ---")
        
        # Default to current date
        default_start = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        default_end = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d_%H:%M:%S")
        
        print(f"Enter dates in format YYYY-MM-DD_HH:MM:SS")
        start_date = input(f"Start date [{default_start}]: ") or default_start
        end_date = input(f"End date [{default_end}]: ") or default_end
        
        self.config["start_date"] = start_date
        self.config["end_date"] = end_date
    
    def set_domain_config(self):
        """Set the domain configuration"""
        print("\n--- Domain Configuration ---")
        
        self.config["domain"]["max_dom"] = int(input("Number of domains [1]: ") or "1")
        self.config["domain"]["ref_lat"] = float(input("Reference latitude [40.0]: ") or "40.0")
        self.config["domain"]["ref_lon"] = float(input("Reference longitude [116.0]: ") or "116.0")
        self.config["domain"]["dx"] = float(input("Grid resolution (dx) in km for domain 1 [30.0]: ") or "30.0")
        self.config["domain"]["dy"] = float(input("Grid resolution (dy) in km for domain 1 [30.0]: ") or "30.0")
        self.config["domain"]["e_we"] = int(input("Number of grid points in west-east direction [100]: ") or "100")
        self.config["domain"]["e_sn"] = int(input("Number of grid points in south-north direction [100]: ") or "100")
        
        if self.config["domain"]["max_dom"] > 1:
            print("\nFor nested domains:")
            for i in range(1, self.config["domain"]["max_dom"]):
                print(f"\nDomain {i+1}:")
                self.config["domain"]["parent_grid_ratio"][i] = int(input(f"Grid ratio relative to parent domain [3]: ") or "3")
                self.config["domain"]["i_parent_start"][i] = int(input(f"I-offset from parent domain [31]: ") or "31")
                self.config["domain"]["j_parent_start"][i] = int(input(f"J-offset from parent domain [17]: ") or "17")
                self.config["domain"]["parent_time_step_ratio"][i] = int(input(f"Time step ratio relative to parent domain [3]: ") or "3")
    
    def set_map_projection(self):
        """Set the map projection"""
        print("\n--- Map Projection ---")
        print("Available projections:")
        for key, value in self.projections.items():
            print(f"{key}: {value}")
        
        proj_choice = int(input("\nSelect projection [1]: ") or "1")
        self.config["projection"] = proj_choice
        
        if proj_choice == 1:  # Lambert
            self.config["domain"]["truelat1"] = float(input("True latitude 1 [30.0]: ") or "30.0")
            self.config["domain"]["truelat2"] = float(input("True latitude 2 [60.0]: ") or "60.0")
            self.config["domain"]["stand_lon"] = float(input("Standard longitude [116.0]: ") or "116.0")
        elif proj_choice == 2:  # Polar
            self.config["domain"]["truelat1"] = float(input("True latitude [60.0]: ") or "60.0")
            self.config["domain"]["stand_lon"] = float(input("Standard longitude [116.0]: ") or "116.0")
        elif proj_choice == 3:  # Mercator
            self.config["domain"]["truelat1"] = float(input("True latitude [0.0]: ") or "0.0")
        elif proj_choice == 6:  # Lat-Lon
            pass
    
    def set_physics_options(self):
        """Set the physics options"""
        print("\n--- Physics Options ---")
        
        # Microphysics
        print("\nMicrophysics schemes:")
        for key, value in self.physics_options["mp_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["mp_physics"] = int(input("\nSelect microphysics scheme [6]: ") or "6")
        
        # Radiation - longwave
        print("\nLongwave radiation schemes:")
        for key, value in self.physics_options["ra_lw_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["ra_lw_physics"] = int(input("\nSelect longwave radiation scheme [1]: ") or "1")
        
        # Radiation - shortwave
        print("\nShortwave radiation schemes:")
        for key, value in self.physics_options["ra_sw_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["ra_sw_physics"] = int(input("\nSelect shortwave radiation scheme [1]: ") or "1")
        
        # Surface layer
        print("\nLand surface schemes:")
        for key, value in self.physics_options["sf_surface_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["sf_surface_physics"] = int(input("\nSelect land surface scheme [2]: ") or "2")
        
        # Boundary layer
        print("\nPBL schemes:")
        for key, value in self.physics_options["bl_pbl_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["bl_pbl_physics"] = int(input("\nSelect PBL scheme [1]: ") or "1")
        
        # Cumulus
        print("\nCumulus schemes:")
        for key, value in self.physics_options["cu_physics"].items():
            print(f"{key}: {value}")
        self.config["physics"]["cu_physics"] = int(input("\nSelect cumulus scheme [1]: ") or "1")
    
    def set_data_source(self):
        """Set the data source"""
        print("\n--- Meteorological Data Source ---")
        print("Available data sources:")
        for key, value in self.data_sources.items():
            print(f"{key}: {value}")
        
        self.config["data_source"] = input("\nSelect data source [GFS]: ") or "GFS"
    
    def show_summary(self):
        """Show configuration summary"""
        print("\n===== Configuration Summary =====")
        print(f"Simulation period: {self.config['start_date']} to {self.config['end_date']}")
        print(f"Number of domains: {self.config['domain']['max_dom']}")
        print(f"Map projection: {self.projections[self.config['projection']]}")
        print(f"Reference point: ({self.config['domain']['ref_lat']}, {self.config['domain']['ref_lon']})")
        print(f"Domain 1 resolution: {self.config['domain']['dx']} km x {self.config['domain']['dy']} km")
        print(f"Domain 1 size: {self.config['domain']['e_we']} x {self.config['domain']['e_sn']} grid points")
        
        print("\nPhysics options:")
        print(f"  Microphysics: {self.physics_options['mp_physics'][self.config['physics']['mp_physics']]}")
        print(f"  Longwave radiation: {self.physics_options['ra_lw_physics'][self.config['physics']['ra_lw_physics']]}")
        print(f"  Shortwave radiation: {self.physics_options['ra_sw_physics'][self.config['physics']['ra_sw_physics']]}")
        print(f"  Land surface: {self.physics_options['sf_surface_physics'][self.config['physics']['sf_surface_physics']]}")
        print(f"  PBL: {self.physics_options['bl_pbl_physics'][self.config['physics']['bl_pbl_physics']]}")
        print(f"  Cumulus: {self.physics_options['cu_physics'][self.config['physics']['cu_physics']]}")
        
        print(f"\nData source: {self.data_sources[self.config['data_source']]}")
        print(f"Output directory: {self.config['output_dir']}")
    
    def create_output_dir(self):
        """Create the output directory"""
        if not os.path.exists(self.config["output_dir"]):
            os.makedirs(self.config["output_dir"])
            print(f"\nCreated output directory: {self.config['output_dir']}")
    
    def create_namelist_wps(self):
        """Create the namelist.wps file"""
        # Parse dates for WPS format
        start_date = datetime.datetime.strptime(self.config["start_date"], "%Y-%m-%d_%H:%M:%S")
        end_date = datetime.datetime.strptime(self.config["end_date"], "%Y-%m-%d_%H:%M:%S")
        
        start_date_str = start_date.strftime("%Y-%m-%d_%H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d_%H:%M:%S")
        
        # Create namelist.wps content
        namelist_wps = f"""&share
 wrf_core = 'ARW',
 max_dom = {self.config['domain']['max_dom']},
 start_date = {', '.join([f"'{start_date_str}'" for _ in range(self.config['domain']['max_dom'])])},
 end_date = {', '.join([f"'{end_date_str}'" for _ in range(self.config['domain']['max_dom'])])},
 interval_seconds = 21600,
/

&geogrid
 parent_id = {', '.join([str(i) for i in range(1, self.config['domain']['max_dom'] + 1)])},
 parent_grid_ratio = {', '.join([str(self.config['domain']['parent_grid_ratio'][i]) for i in range(self.config['domain']['max_dom'])])},
 i_parent_start = {', '.join([str(self.config['domain']['i_parent_start'][i]) for i in range(self.config['domain']['max_dom'])])},
 j_parent_start = {', '.join([str(self.config['domain']['j_parent_start'][i]) for i in range(self.config['domain']['max_dom'])])},
 e_we = {', '.join([str(self.config['domain']['e_we'])] + [str(int((self.config['domain']['e_we'] - 1) / self.config['domain']['parent_grid_ratio'][i] + 1)) for i in range(1, self.config['domain']['max_dom'])])},
 e_sn = {', '.join([str(self.config['domain']['e_sn'])] + [str(int((self.config['domain']['e_sn'] - 1) / self.config['domain']['parent_grid_ratio'][i] + 1)) for i in range(1, self.config['domain']['max_dom'])])},
 geog_data_res = {', '.join(['\'default\'' for _ in range(self.config['domain']['max_dom'])])},
 dx = {self.config['domain']['dx'] * 1000},
 dy = {self.config['domain']['dy'] * 1000},
 map_proj = '{self.projections[self.config["projection"]].lower().replace(" ", "_")}',
 ref_lat = {self.config['domain']['ref_lat']},
 ref_lon = {self.config['domain']['ref_lon']},"""
        
        # Add projection-specific parameters
        if self.config["projection"] == 1:  # Lambert
            namelist_wps += f"""
 truelat1 = {self.config['domain']['truelat1']},
 truelat2 = {self.config['domain']['truelat2']},
 stand_lon = {self.config['domain']['stand_lon']},"""
        elif self.config["projection"] == 2:  # Polar
            namelist_wps += f"""
 truelat1 = {self.config['domain']['truelat1']},
 stand_lon = {self.config['domain']['stand_lon']},"""
        elif self.config["projection"] == 3:  # Mercator
            namelist_wps += f"""
 truelat1 = {self.config['domain']['truelat1']},"""
        
        namelist_wps += """
 geog_data_path = '/path/to/WPS_GEOG/',
/

&ungrib
 out_format = 'WPS',
 prefix = 'FILE',
/

&metgrid
 fg_name = 'FILE',
 io_form_metgrid = 2,
/
"""
        
        # Write to file
        wps_path = os.path.join(self.config["output_dir"], "namelist.wps")
        with open(wps_path, 'w') as f:
            f.write(namelist_wps)
        
        print(f"Created namelist.wps in {wps_path}")
    
    def create_namelist_input(self):
        """Create the namelist.input file"""
        # Parse dates for WRF format
        start_date = datetime.datetime.strptime(self.config["start_date"], "%Y-%m-%d_%H:%M:%S")
        end_date = datetime.datetime.strptime(self.config["end_date"], "%Y-%m-%d_%H:%M:%S")
        
        # Calculate run duration in hours
        run_hours = int((end_date - start_date).total_seconds() / 3600)
        
        # Format dates for namelist
        start_year = start_date.year
        start_month = start_date.month
        start_day = start_date.day
        start_hour = start_date.hour
        start_minute = start_date.minute
        start_second = start_date.second
        
        end_year = end_date.year
        end_month = end_date.month
        end_day = end_date.day
        end_hour = end_date.hour
        end_minute = end_date.minute
        end_second = end_date.second
        
        # Create namelist.input content
        namelist_input = f"""&time_control
 run_days = 0,
 run_hours = {run_hours},
 run_minutes = 0,
 run_seconds = 0,
 start_year = {', '.join([str(start_year) for _ in range(self.config['domain']['max_dom'])])},
 start_month = {', '.join([str(start_month) for _ in range(self.config['domain']['max_dom'])])},
 start_day = {', '.join([str(start_day) for _ in range(self.config['domain']['max_dom'])])},
 start_hour = {', '.join([str(start_hour) for _ in range(self.config['domain']['max_dom'])])},
 start_minute = {', '.join([str(start_minute) for _ in range(self.config['domain']['max_dom'])])},
 start_second = {', '.join([str(start_second) for _ in range(self.config['domain']['max_dom'])])},
 end_year = {', '.join([str(end_year) for _ in range(self.config['domain']['max_dom'])])},
 end_month = {', '.join([str(end_month) for _ in range(self.config['domain']['max_dom'])])},
 end_day = {', '.join([str(end_day) for _ in range(self.config['domain']['max_dom'])])},
 end_hour = {', '.join([str(end_hour) for _ in range(self.config['domain']['max_dom'])])},
 end_minute = {', '.join([str(end_minute) for _ in range(self.config['domain']['max_dom'])])},
 end_second = {', '.join([str(end_second) for _ in range(self.config['domain']['max_dom'])])},
 interval_seconds = 21600,
 input_from_file = {', '.join(['true' for _ in range(self.config['domain']['max_dom'])])},
 history_interval = {', '.join(['60' for _ in range(self.config['domain']['max_dom'])])},
 frames_per_outfile = {', '.join(['1' for _ in range(self.config['domain']['max_dom'])])},
 restart = false,
 restart_interval = 7200,
 io_form_history = 2,
 io_form_restart = 2,
 io_form_input = 2,
 io_form_boundary = 2,
 debug_level = 0,
/

&domains
 time_step = 180,
 time_step_fract_num = 0,
 time_step_fract_den = 1,
 max_dom = {self.config['domain']['max_dom']},
 e_we = {', '.join([str(self.config['domain']['e_we'])] + [str(int((self.config['domain']['e_we'] - 1) / self.config['domain']['parent_grid_ratio'][i] + 1)) for i in range(1, self.config['domain']['max_dom'])])},
 e_sn = {', '.join([str(self.config['domain']['e_sn'])] + [str(int((self.config['domain']['e_sn'] - 1) / self.config['domain']['parent_grid_ratio'][i] + 1)) for i in range(1, self.config['domain']['max_dom'])])},
 e_vert = {', '.join(['33' for _ in range(self.config['domain']['max_dom'])])},
 p_top_requested = 5000,
 num_metgrid_levels = 32,
 num_metgrid_soil_levels = 4,
 dx = {self.config['domain']['dx'] * 1000},
 dy = {self.config['domain']['dy'] * 1000},
 grid_id = {', '.join([str(i+1) for i in range(self.config['domain']['max_dom'])])},
 parent_id = {', '.join(['1'] + [str(i) for i in range(1, self.config['domain']['max_dom'])])},
 i_parent_start = {', '.join([str(self.config['domain']['i_parent_start'][i]) for i in range(self.config['domain']['max_dom'])])},
 j_parent_start = {', '.join([str(self.config['domain']['j_parent_start'][i]) for i in range(self.config['domain']['max_dom'])])},
 parent_grid_ratio = {', '.join([str(self.config['domain']['parent_grid_ratio'][i]) for i in range(self.config['domain']['max_dom'])])},
 parent_time_step_ratio = {', '.join([str(self.config['domain']['parent_time_step_ratio'][i]) for i in range(self.config['domain']['max_dom'])])},
 feedback = 1,
 smooth_option = 0,
/

&physics
 physics_suite = 'CONUS',
 mp_physics = {', '.join([str(self.config['physics']['mp_physics']) for _ in range(self.config['domain']['max_dom'])])},
 ra_lw_physics = {', '.join([str(self.config['physics']['ra_lw_physics']) for _ in range(self.config['domain']['max_dom'])])},
 ra_sw_physics = {', '.join([str(self.config['physics']['ra_sw_physics']) for _ in range(self.config['domain']['max_dom'])])},
 radt = 30,
 sf_sfclay_physics = {', '.join(['1' for _ in range(self.config['domain']['max_dom'])])},
 sf_surface_physics = {', '.join([str(self.config['physics']['sf_surface_physics']) for _ in range(self.config['domain']['max_dom'])])},
 bl_pbl_physics = {', '.join([str(self.config['physics']['bl_pbl_physics']) for _ in range(self.config['domain']['max_dom'])])},
 bldt = 0,
 cu_physics = {', '.join([str(self.config['physics']['cu_physics']) for _ in range(self.config['domain']['max_dom'])])},
 cudt = 5,
 isfflx = 1,
 ifsnow = 1,
 icloud = 1,
 surface_input_source = 1,
 num_soil_layers = 4,
 num_land_cat = 21,
 sf_urban_physics = 0,
/

&fdda
/

&dynamics
 w_damping = 0,
 diff_opt = 1,
 km_opt = 4,
 diff_6th_opt = 0,
 diff_6th_factor = 0.12,
 base_temp = 290.0,
 damp_opt = 0,
 zdamp = 5000.,
 dampcoef = 0.2,
 khdif = 0,
 kvdif = 0,
 non_hydrostatic = .true.,
 moist_adv_opt = 1,
 scalar_adv_opt = 1,
 gwd_opt = 1,
/

&bdy_control
 spec_bdy_width = 5,
 spec_zone = 1,
 relax_zone = 4,
 specified = .true.,
 nested = .false.,
/

&grib2
/

&namelist_quilt
 nio_tasks_per_group = 0,
 nio_groups = 1,
/
"""
        
        # Write to file
        input_path = os.path.join(self.config["output_dir"], "namelist.input")
        with open(input_path, 'w') as f:
            f.write(namelist_input)
        
        print(f"Created namelist.input in {input_path}")
    
    def download_data(self):
        """Download meteorological data based on user selection"""
        print("\n--- Downloading Meteorological Data ---")
        
        # Parse dates
        start_date = datetime.datetime.strptime(self.config["start_date"], "%Y-%m-%d_%H:%M:%S")
        end_date = datetime.datetime.strptime(self.config["end_date"], "%Y-%m-%d_%H:%M:%S")
        
        # Create download script
        download_script = "#!/bin/bash\n\n"
        download_script += f"# Download script for {self.config['data_source']} data\n"
        download_script += f"# Date range: {self.config['start_date']} to {self.config['end_date']}\n\n"
        
        data_dir = os.path.join(self.config["output_dir"], "data")
        download_script += f"mkdir -p {data_dir}\n"
        download_script += f"cd {data_dir}\n\n"
        
        if self.config["data_source"] == "GFS":
            download_script += self._create_gfs_download_script(start_date, end_date)
        elif self.config["data_source"] == "ERA5":
            download_script += self._create_era5_download_script(start_date, end_date)
        elif self.config["data_source"] == "FNL":
            download_script += self._create_fnl_download_script(start_date, end_date)
        elif self.config["data_source"] == "NARR":
            download_script += self._create_narr_download_script(start_date, end_date)
        
        # Write download script
        script_path = os.path.join(self.config["output_dir"], "download_data.sh")
        with open(script_path, 'w') as f:
            f.write(download_script)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        print(f"Created download script: {script_path}")
        print("You can run this script to download the required meteorological data.")
    
    def _create_gfs_download_script(self, start_date, end_date):
        """Create download script for GFS data"""
        script = "# GFS data download using wget\n\n"
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            day = current_date.strftime("%d")
            
            for hour in ["00", "06", "12", "18"]:
                script += f"# {year}-{month}-{day}_{hour}\n"
                script += f"wget -c https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year}{month}{day}/{hour}/atmos/gfs.t{hour}z.pgrb2.0p25.f000\n"
                script += f"wget -c https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year}{month}{day}/{hour}/atmos/gfs.t{hour}z.pgrb2.0p25.f003\n"
                script += f"wget -c https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year}{month}{day}/{hour}/atmos/gfs.t{hour}z.pgrb2.0p25.f006\n"
                script += f"wget -c https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year}{month}{day}/{hour}/atmos/gfs.t{hour}z.pgrb2.0p25.f009\n"
                script += f"wget -c https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year}{month}{day}/{hour}/atmos/gfs.t{hour}z.pgrb2.0p25.f012\n"
                script += "\n"
            
            current_date += datetime.timedelta(days=1)
        
        script += "echo 'GFS data download complete.'\n"
        return script
    
    def _create_era5_download_script(self, start_date, end_date):
        """Create download script for ERA5 data using CDS API"""
        script = "# ERA5 data download using CDS API\n\n"
        script += "# Make sure you have the CDS API key set up in ~/.cdsapirc\n\n"
        
        script += "cat > era5_request.py << 'EOL'\n"
        script += "import cdsapi\n\n"
        script += "c = cdsapi.Client()\n\n"
        
        # Format dates for ERA5 request
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        script += "c.retrieve(\n"
        script += "    'reanalysis-era5-pressure-levels',\n"
        script += "    {\n"
        script += "        'product_type': 'reanalysis',\n"
        script += "        'format': 'grib',\n"
        script += "        'variable': [\n"
        script += "            'geopotential', 'relative_humidity', 'specific_humidity',\n"
        script += "            'temperature', 'u_component_of_wind', 'v_component_of_wind',\n"
        script += "        ],\n"
        script += "        'pressure_level': [\n"
        script += "            '1', '2', '3', '5', '7', '10', '20', '30',\n"
        script += "            '50', '70', '100', '125', '150', '175', '200',\n"
        script += "            '225', '250', '300', '350', '400', '450', '500',\n"
        script += "            '550', '600', '650', '700', '750', '775', '800',\n"
        script += "            '825', '850', '875', '900', '925', '950', '975', '1000',\n"
        script += "        ],\n"
        script += f"        'date': '{start_str}/{end_str}',\n"
        script += "        'time': ['00:00', '06:00', '12:00', '18:00'],\n"
        script += "        'area': [90, -180, -90, 180],\n"
        script += "    },\n"
        script += "    'era5_pressure_levels.grib')\n\n"
        
        script += "c.retrieve(\n"
        script += "    'reanalysis-era5-single-levels',\n"
        script += "    {\n"
        script += "        'product_type': 'reanalysis',\n"
        script += "        'format': 'grib',\n"
        script += "        'variable': [\n"
        script += "            '10m_u_component_of_wind', '10m_v_component_of_wind', '2m_dewpoint_temperature',\n"
        script += "            '2m_temperature', 'land_sea_mask', 'mean_sea_level_pressure',\n"
        script += "            'sea_ice_cover', 'sea_surface_temperature', 'skin_temperature',\n"
        script += "            'snow_depth', 'soil_temperature_level_1', 'soil_temperature_level_2',\n"
        script += "            'soil_temperature_level_3', 'soil_temperature_level_4', 'surface_pressure',\n"
        script += "            'volumetric_soil_water_layer_1', 'volumetric_soil_water_layer_2',\n"
        script += "            'volumetric_soil_water_layer_3', 'volumetric_soil_water_layer_4',\n"
        script += "        ],\n"
        script += f"        'date': '{start_str}/{end_str}',\n"
        script += "        'time': ['00:00', '06:00', '12:00', '18:00'],\n"
        script += "        'area': [90, -180, -90, 180],\n"
        script += "    },\n"
        script += "    'era5_surface.grib')\n"
        script += "EOL\n\n"
        
        script += "python era5_request.py\n\n"
        script += "echo 'ERA5 data download complete.'\n"
        return script
    
    def _create_fnl_download_script(self, start_date, end_date):
        """Create download script for FNL data"""
        script = "# FNL data download using wget\n\n"
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            day = current_date.strftime("%d")
            
            for hour in ["00", "06", "12", "18"]:
                script += f"# {year}-{month}-{day}_{hour}\n"
                script += f"wget -c https://rda.ucar.edu/data/ds083.2/grib2/{year}/{year}.{month}/{year}{month}{day}/fnl_{year}{month}{day}_{hour}_00.grib2\n"
                script += "\n"
            
            current_date += datetime.timedelta(days=1)
        
        script += "echo 'FNL data download complete.'\n"
        return script
    
    def _create_narr_download_script(self, start_date, end_date):
        """Create download script for NARR data"""
        script = "# NARR data download using wget\n\n"
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.strftime("%Y")
            month = current_date.strftime("%m")
            day = current_date.strftime("%d")
            
            for hour in ["00", "03", "06", "09", "12", "15", "18", "21"]:
                script += f"# {year}-{month}-{day}_{hour}\n"
                script += f"wget -c https://www.ncei.noaa.gov/data/north-american-regional-reanalysis/access/{year}{month}/{year}{month}{day}/narr-a_221_{year}{month}{day}_{hour}00_000.grb\n"
                script += "\n"
            
            current_date += datetime.timedelta(days=1)
        
        script += "echo 'NARR data download complete.'\n"
        return script

def main():
    """Main function to run the WRF setup tool"""
    print("WRF Model Setup Tool")
    print("====================")
    
    wrf_setup = WRFSetup()
    wrf_setup.show_menu()

if __name__ == "__main__":
    main()