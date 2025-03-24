"""
WRF Results Visualization Module
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from netCDF4 import Dataset
from flask import current_app, url_for
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('wrf_visualizer')


class WrfVisualizer:
    """WRF Results Visualization Class"""
    def __init__(self, task_id):
        """Initialize visualizer
        Args:
            task_id: WRF task ID
        """
        self.task_id = task_id
        self.result_dir = os.path.join(current_app.config['RESULTS_FOLDER'], task_id)
        self.viz_dir = os.path.join(self.result_dir, 'viz')

        # Ensure visualization directory exists
        os.makedirs(self.viz_dir, exist_ok=True)

        # Find wrfout files
        self.wrfout_files = []
        if os.path.exists(self.result_dir):
            for filename in os.listdir(self.result_dir):
                if filename.startswith('wrfout_'):
                    self.wrfout_files.append(os.path.join(self.result_dir, filename))

        self.wrfout_files.sort()  # Sort by filename

    def visualize_results(self):
        """Visualize WRF results"""
        if not self.wrfout_files:
            logger.warning(f"No wrfout files found for task {self.task_id}")
            return False

        try:
            # Generate visualizations for each output file
            for wrfout_file in self.wrfout_files:
                self._visualize_file(wrfout_file)

            logger.info(f"Visualization completed for task {self.task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to visualize task {self.task_id}: {str(e)}")
            return False

    def _visualize_file(self, wrfout_file):
        """Visualize single wrfout file
        Args:
            wrfout_file: wrfout file path
        """
        filename = os.path.basename(wrfout_file)
        logger.info(f"Visualizing file: {filename}")

        try:
            # Open NetCDF file
            ncfile = Dataset(wrfout_file)

            # Get time information
            times = ncfile.variables['Times'][:]
            time_str = b''.join(times[0]).decode('utf-8')

            # Generate visualizations for different variables
            self._plot_temperature(ncfile, filename, time_str)
            self._plot_wind(ncfile, filename, time_str)
            self._plot_precipitation(ncfile, filename, time_str)
            self._plot_pressure(ncfile, filename, time_str)

            ncfile.close()
        except Exception as e:
            logger.error(f"Failed to visualize file {filename}: {str(e)}")

    def _plot_temperature(self, ncfile, filename, time_str):
        """Plot temperature field
        Args:
            ncfile: NetCDF file object
            filename: File name
            time_str: Time string
        """
        try:
            # Get variables
            t2 = ncfile.variables['T2'][0] - 273.15  # Convert to Celsius
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # Create figure
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # Add map features
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # Draw contour fill
            levels = np.linspace(t2.min(), t2.max(), 15)
            cf = ax.contourf(lons, lats, t2, levels=levels, cmap=get_cmap("jet"))

            # Add colorbar and title
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('Temperature (°C)')

            plt.title(f'2-meter Temperature - {time_str}')

            # Save image
            output_file = os.path.join(self.viz_dir, f'temp_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Temperature field visualization generated: {output_file}")
        except Exception as e:
            logger.error(f"Failed to plot temperature field: {str(e)}")

    def _plot_wind(self, ncfile, filename, time_str):
        """Plot wind field
        Args:
            ncfile: NetCDF file object
            filename: File name
            time_str: Time string
        """
        try:
            # Get variables
            u10 = ncfile.variables['U10'][0]
            v10 = ncfile.variables['V10'][0]
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # Calculate wind speed
            wind_speed = np.sqrt(u10*u10 + v10*v10)

            # Create figure
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # Add map features
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # Draw contour fill
            levels = np.linspace(0, np.max(wind_speed), 15)
            cf = ax.contourf(lons, lats, wind_speed, levels=levels, cmap=get_cmap("viridis"))

            # Draw wind direction arrows
            skip = 8  # Arrow spacing
            ax.quiver(lons[::skip, ::skip], lats[::skip, ::skip],
                      u10[::skip, ::skip], v10[::skip, ::skip],
                      scale=50, color='white')

            # Add colorbar and title
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('Wind Speed (m/s)')

            plt.title(f'10-meter Wind Field - {time_str}')

            # Save image
            output_file = os.path.join(self.viz_dir, f'wind_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Wind field visualization generated: {output_file}")
        except Exception as e:
            logger.error(f"Failed to plot wind field: {str(e)}")

    def _plot_precipitation(self, ncfile, filename, time_str):
        """Plot precipitation field
        Args:
            ncfile: NetCDF file object
            filename: File name
            time_str: Time string
        """
        try:
            # Get variables
            if 'RAINC' in ncfile.variables and 'RAINNC' in ncfile.variables:
                rainc = ncfile.variables['RAINC'][0]
                rainnc = ncfile.variables['RAINNC'][0]
                rain_total = rainc + rainnc

                lats = ncfile.variables['XLAT'][0]
                lons = ncfile.variables['XLONG'][0]

                # Create figure
                fig = plt.figure(figsize=(10, 8))
                ax = plt.axes(projection=ccrs.PlateCarree())

                # Add map features
                ax.add_feature(cfeature.COASTLINE)
                ax.add_feature(cfeature.BORDERS, linestyle=':')

                # Draw contour fill
                levels = [0, 0.1, 0.5, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
                cf = ax.contourf(lons, lats, rain_total, levels=levels, cmap=get_cmap("Blues"))

                # Add colorbar and title
                cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
                cbar.set_label('Accumulated Precipitation (mm)')

                plt.title(f'Accumulated Precipitation - {time_str}')

                # Save image
                output_file = os.path.join(self.viz_dir, f'rain_{os.path.splitext(filename)[0]}.png')
                plt.savefig(output_file, dpi=150, bbox_inches='tight')
                plt.close(fig)

                logger.info(f"Precipitation field visualization generated: {output_file}")
            else:
                logger.warning("No precipitation variables found in the file")
        except Exception as e:
            logger.error(f"Failed to plot precipitation field: {str(e)}")

    def _plot_pressure(self, ncfile, filename, time_str):
        """Plot pressure field
        Args:
            ncfile: NetCDF file object
            filename: File name
            time_str: Time string
        """
        try:
            # Get variables
            psfc = ncfile.variables['PSFC'][0] / 100.0  # Convert to hPa
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # Create figure
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # Add map features
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # Draw contour fill
            levels = np.linspace(np.min(psfc), np.max(psfc), 15)
            cf = ax.contourf(lons, lats, psfc, levels=levels, cmap=get_cmap("rainbow"))

            # Add contour lines
            cs = ax.contour(lons, lats, psfc, levels=levels, colors='black', linewidths=0.5)
            plt.clabel(cs, inline=1, fontsize=8, fmt='%1.0f')

            # Add colorbar and title
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('Surface Pressure (hPa)')

            plt.title(f'Surface Pressure - {time_str}')

            # Save image
            output_file = os.path.join(self.viz_dir, f'pressure_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Pressure field visualization generated: {output_file}")
        except Exception as e:
            logger.error(f"Failed to plot pressure field: {str(e)}")

    def get_visualization_results(self):
        """Get visualization results
        Returns:
            dict: Visualization results dictionary, organized by category
        """
        # If visualization directory does not exist or is empty, generate visualizations first
        if not os.path.exists(self.viz_dir) or not os.listdir(self.viz_dir):
            self.visualize_results()

        # Organize visualization results
        results = {
            "Temperature Field": [],
            "Wind Field": [],
            "Precipitation Field": [],
            "Pressure Field": []
        }

        # Retrieve visualization images
        if os.path.exists(self.viz_dir):
            for filename in os.listdir(self.viz_dir):
                if not filename.endswith('.png'):
                    continue

                file_path = os.path.join(self.viz_dir, filename)
                file_url = url_for('static',
                                   filename=f'results/{self.task_id}/viz/{filename}',
                                   _external=True)

                # Categorize by filename prefix
                if filename.startswith('temp_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["Temperature Field"].append({
                        "title": f"2-meter Temperature - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('wind_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["Wind Field"].append({
                        "title": f"10-meter Wind Field - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('rain_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["Precipitation Field"].append({
                        "title": f"Accumulated Precipitation - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('pressure_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["Pressure Field"].append({
                        "title": f"Surface Pressure - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })

        # Remove empty categories
        results = {k: v for k, v in results.items() if v}

        return results

    def _extract_time_from_filename(self, filename):
        """Extract time information from filename
        Args:
            filename: File name

        Returns:
            str: Time string
        """
        # Example: temp_wrfout_d01_2022-01-01_00:00:00.png
        try:
            parts = filename.split('_')
            if len(parts) >= 4:
                date_part = parts[3]
                time_part = parts[4].split('.')[0] if len(parts) >= 5 else ""
                return f"{date_part} {time_part}"
            return "Unknown Time"
        except:
            return "Unknown Time"
