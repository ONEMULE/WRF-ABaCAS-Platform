"""
WRF结果可视化模块
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

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('wrf_visualizer')


class WrfVisualizer:
    """WRF结果可视化类"""

    def __init__(self, task_id):
        """初始化可视化器

        Args:
            task_id: WRF任务ID
        """
        self.task_id = task_id
        self.result_dir = os.path.join(current_app.config['RESULTS_FOLDER'], task_id)
        self.viz_dir = os.path.join(self.result_dir, 'viz')

        # 确保可视化目录存在
        os.makedirs(self.viz_dir, exist_ok=True)

        # 查找wrfout文件
        self.wrfout_files = []
        if os.path.exists(self.result_dir):
            for filename in os.listdir(self.result_dir):
                if filename.startswith('wrfout_'):
                    self.wrfout_files.append(os.path.join(self.result_dir, filename))

        self.wrfout_files.sort()  # 按文件名排序

    def visualize_results(self):
        """可视化WRF结果"""
        if not self.wrfout_files:
            logger.warning(f"任务 {self.task_id} 没有找到wrfout文件")
            return False

        try:
            # 为每个输出文件生成可视化
            for wrfout_file in self.wrfout_files:
                self._visualize_file(wrfout_file)

            logger.info(f"任务 {self.task_id} 的可视化已完成")
            return True
        except Exception as e:
            logger.error(f"可视化任务 {self.task_id} 失败: {str(e)}")
            return False

    def _visualize_file(self, wrfout_file):
        """可视化单个wrfout文件

        Args:
            wrfout_file: wrfout文件路径
        """
        filename = os.path.basename(wrfout_file)
        logger.info(f"正在可视化文件: {filename}")

        try:
            # 打开NetCDF文件
            ncfile = Dataset(wrfout_file)

            # 获取时间信息
            times = ncfile.variables['Times'][:]
            time_str = b''.join(times[0]).decode('utf-8')

            # 生成不同变量的可视化
            self._plot_temperature(ncfile, filename, time_str)
            self._plot_wind(ncfile, filename, time_str)
            self._plot_precipitation(ncfile, filename, time_str)
            self._plot_pressure(ncfile, filename, time_str)

            ncfile.close()
        except Exception as e:
            logger.error(f"可视化文件 {filename} 失败: {str(e)}")

    def _plot_temperature(self, ncfile, filename, time_str):
        """绘制温度场

        Args:
            ncfile: NetCDF文件对象
            filename: 文件名
            time_str: 时间字符串
        """
        try:
            # 获取变量
            t2 = ncfile.variables['T2'][0] - 273.15  # 转换为摄氏度
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # 创建图形
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # 添加地图特征
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # 绘制等值线填充
            levels = np.linspace(t2.min(), t2.max(), 15)
            cf = ax.contourf(lons, lats, t2, levels=levels, cmap=get_cmap("jet"))

            # 添加颜色条和标题
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('温度 (°C)')

            plt.title(f'2米温度 - {time_str}')

            # 保存图像
            output_file = os.path.join(self.viz_dir, f'temp_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"已生成温度场可视化: {output_file}")
        except Exception as e:
            logger.error(f"绘制温度场失败: {str(e)}")

    def _plot_wind(self, ncfile, filename, time_str):
        """绘制风场

        Args:
            ncfile: NetCDF文件对象
            filename: 文件名
            time_str: 时间字符串
        """
        try:
            # 获取变量
            u10 = ncfile.variables['U10'][0]
            v10 = ncfile.variables['V10'][0]
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # 计算风速
            wind_speed = np.sqrt(u10*u10 + v10*v10)

            # 创建图形
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # 添加地图特征
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # 绘制等值线填充
            levels = np.linspace(0, np.max(wind_speed), 15)
            cf = ax.contourf(lons, lats, wind_speed, levels=levels, cmap=get_cmap("viridis"))

            # 绘制风向箭头
            skip = 8  # 箭头间隔
            ax.quiver(lons[::skip, ::skip], lats[::skip, ::skip],
                      u10[::skip, ::skip], v10[::skip, ::skip],
                      scale=50, color='white')

            # 添加颜色条和标题
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('风速 (m/s)')

            plt.title(f'10米风场 - {time_str}')

            # 保存图像
            output_file = os.path.join(self.viz_dir, f'wind_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"已生成风场可视化: {output_file}")
        except Exception as e:
            logger.error(f"绘制风场失败: {str(e)}")

    def _plot_precipitation(self, ncfile, filename, time_str):
        """绘制降水场

        Args:
            ncfile: NetCDF文件对象
            filename: 文件名
            time_str: 时间字符串
        """
        try:
            # 获取变量
            if 'RAINC' in ncfile.variables and 'RAINNC' in ncfile.variables:
                rainc = ncfile.variables['RAINC'][0]
                rainnc = ncfile.variables['RAINNC'][0]
                rain_total = rainc + rainnc

                lats = ncfile.variables['XLAT'][0]
                lons = ncfile.variables['XLONG'][0]

                # 创建图形
                fig = plt.figure(figsize=(10, 8))
                ax = plt.axes(projection=ccrs.PlateCarree())

                # 添加地图特征
                ax.add_feature(cfeature.COASTLINE)
                ax.add_feature(cfeature.BORDERS, linestyle=':')

                # 绘制等值线填充
                levels = [0, 0.1, 0.5, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
                cf = ax.contourf(lons, lats, rain_total, levels=levels, cmap=get_cmap("Blues"))

                # 添加颜色条和标题
                cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
                cbar.set_label('累积降水量 (mm)')

                plt.title(f'累积降水量 - {time_str}')

                # 保存图像
                output_file = os.path.join(self.viz_dir, f'rain_{os.path.splitext(filename)[0]}.png')
                plt.savefig(output_file, dpi=150, bbox_inches='tight')
                plt.close(fig)

                logger.info(f"已生成降水场可视化: {output_file}")
            else:
                logger.warning("文件中没有找到降水变量")
        except Exception as e:
            logger.error(f"绘制降水场失败: {str(e)}")

    def _plot_pressure(self, ncfile, filename, time_str):
        """绘制气压场

        Args:
            ncfile: NetCDF文件对象
            filename: 文件名
            time_str: 时间字符串
        """
        try:
            # 获取变量
            psfc = ncfile.variables['PSFC'][0] / 100.0  # 转换为百帕
            lats = ncfile.variables['XLAT'][0]
            lons = ncfile.variables['XLONG'][0]

            # 创建图形
            fig = plt.figure(figsize=(10, 8))
            ax = plt.axes(projection=ccrs.PlateCarree())

            # 添加地图特征
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # 绘制等值线填充
            levels = np.linspace(np.min(psfc), np.max(psfc), 15)
            cf = ax.contourf(lons, lats, psfc, levels=levels, cmap=get_cmap("rainbow"))

            # 添加等值线
            cs = ax.contour(lons, lats, psfc, levels=levels, colors='black', linewidths=0.5)
            plt.clabel(cs, inline=1, fontsize=8, fmt='%1.0f')

            # 添加颜色条和标题
            cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_label('地面气压 (hPa)')

            plt.title(f'地面气压 - {time_str}')

            # 保存图像
            output_file = os.path.join(self.viz_dir, f'pressure_{os.path.splitext(filename)[0]}.png')
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"已生成气压场可视化: {output_file}")
        except Exception as e:
            logger.error(f"绘制气压场失败: {str(e)}")

    def get_visualization_results(self):
        """获取可视化结果

        Returns:
            dict: 可视化结果字典，按类别组织
        """
        # 如果可视化目录不存在或为空，先生成可视化
        if not os.path.exists(self.viz_dir) or not os.listdir(self.viz_dir):
            self.visualize_results()

        # 组织可视化结果
        results = {
            "温度场": [],
            "风场": [],
            "降水场": [],
            "气压场": []
        }

        # 检索可视化图像
        if os.path.exists(self.viz_dir):
            for filename in os.listdir(self.viz_dir):
                if not filename.endswith('.png'):
                    continue

                file_path = os.path.join(self.viz_dir, filename)
                file_url = url_for('static',
                                   filename=f'results/{self.task_id}/viz/{filename}',
                                   _external=True)

                # 根据文件名前缀分类
                if filename.startswith('temp_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["温度场"].append({
                        "title": f"2米温度 - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('wind_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["风场"].append({
                        "title": f"10米风场 - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('rain_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["降水场"].append({
                        "title": f"累积降水量 - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })
                elif filename.startswith('pressure_'):
                    time_str = self._extract_time_from_filename(filename)
                    results["气压场"].append({
                        "title": f"地面气压 - {time_str}",
                        "path": file_path,
                        "url": file_url
                    })

        # 移除空类别
        results = {k: v for k, v in results.items() if v}

        return results

    def _extract_time_from_filename(self, filename):
        """从文件名中提取时间信息

        Args:
            filename: 文件名

        Returns:
            str: 时间字符串
        """
        # 示例: temp_wrfout_d01_2022-01-01_00:00:00.png
        try:
            parts = filename.split('_')
            if len(parts) >= 4:
                date_part = parts[3]
                time_part = parts[4].split('.')[0] if len(parts) >= 5 else ""
                return f"{date_part} {time_part}"
            return "未知时间"
        except:
            return "未知时间"
