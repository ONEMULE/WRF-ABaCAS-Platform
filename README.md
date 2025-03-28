# WRF-ABaCAS-Platform

## English Version

### Overview

WRF-ABaCAS-Platform is a Flask-based web application platform specifically designed for the configuration, execution, and result visualization of the Weather Research and Forecasting (WRF) model. This platform provides meteorological researchers and forecasters with a user-friendly interface to perform weather simulations and forecasts using the WRF model without having to deal with complex command-line operations.

### Key Features

#### 1. Namelist Configuration Management
- Upload and manage WRF model namelist.input and namelist.wps configuration files
- View and edit existing configurations
- Save frequently used configuration templates for reuse

#### 2. WRF Task Management
- Create new WRF simulation tasks
- Upload necessary meteorological data files (met_em files)
- Monitor task execution status (pending, running, completed, failed)
- View task details and execution logs

#### 3. Remote WRF Execution
- Connect to remote virtual machines with WRF model installed via SSH
- Automatically transfer configuration files and input data
- Execute WRF simulations remotely (including real.exe and wrf.exe)
- Monitor execution progress in real-time

#### 4. Result Visualization
- Automatically process WRF output files (wrfout)
- Generate visualizations for various meteorological elements:
  - 2-meter temperature field
  - 10-meter wind field
  - Accumulated precipitation
  - Surface pressure field
- Create professional meteorological charts using Matplotlib and Cartopy

#### 5. File Management
- Upload, download, and manage model input/output files
- Batch process data files
- Organize and store simulation results

### Technical Architecture

#### Frontend
- Responsive web interface based on HTML, CSS, and JavaScript
- Template system for page structure organization
- Real-time task status monitoring

#### Backend
- Built with Python Flask framework
- SQLAlchemy ORM for database interactions
- Paramiko library for SSH remote connections
- NetCDF4, Matplotlib, and Cartopy for data processing and visualization

#### Data Storage
- SQLite database for task and configuration information
- File system for uploaded configuration files and model outputs

### Usage Workflow

1. **Create Task**: Users first create a new WRF simulation task, providing a name and description.
2. **Upload Configuration**: Upload namelist.input file defining simulation time, region, and physical parameters.
3. **Upload Data**: Upload necessary meteorological data files (met_em files).
4. **Run Simulation**: Click the run button, and the system will transfer files to the remote WRF server and start the simulation.
5. **Monitor Status**: Users can monitor task execution status and progress in real-time.
6. **View Results**: After simulation completion, the system automatically processes output files and generates visualizations that users can view and download.

### Target Users

- Meteorological researchers
- Weather forecasters
- Meteorology students and teachers
- Environmental scientists requiring weather simulations

### Key Advantages

1. **Simplified Operations**: Simplifies complex WRF model operations through a graphical interface
2. **Remote Execution**: No need to install WRF locally; use pre-configured WRF environments through remote connections
3. **Automatic Visualization**: Automatically processes model outputs and generates professional meteorological charts
4. **Task Management**: Complete task creation, monitoring, and history recording functionality
5. **Flexible Configuration**: Supports custom namelist configurations for different simulation requirements

This platform significantly lowers the technical barrier to using the WRF model, allowing researchers to focus more on scientific questions rather than technical details, thereby improving the efficiency of meteorological research and forecasting.

---

## 中文版本

### 概述

WRF-ABaCAS-Platform 是一个基于 Flask 开发的 Web 应用平台，专门用于天气研究和预报模型（Weather Research and Forecasting, WRF）的配置、运行和结果可视化。该平台为气象研究人员和预报员提供了一个友好的界面，使他们能够更方便地使用 WRF 模型进行天气模拟和预报，而无需直接处理复杂的命令行操作。

### 主要功能

#### 1. Namelist 配置管理
- 上传和管理 WRF 模型的 namelist.input 和 namelist.wps 配置文件
- 查看和编辑现有配置
- 保存常用配置模板以便重复使用

#### 2. WRF 任务管理
- 创建新的 WRF 模拟任务
- 上传必要的气象数据文件（met_em 文件）
- 监控任务运行状态（等待中、运行中、已完成、失败）
- 查看任务详情和运行日志

#### 3. 远程 WRF 执行
- 通过 SSH 连接到配置有 WRF 模型的远程虚拟机
- 自动传输配置文件和输入数据
- 远程执行 WRF 模拟（包括 real.exe 和 wrf.exe）
- 实时监控运行进度

#### 4. 结果可视化
- 自动处理 WRF 输出文件（wrfout）
- 生成多种气象要素的可视化图像：
  - 2米温度场
  - 10米风场
  - 累积降水量
  - 地面气压场
- 使用 Matplotlib 和 Cartopy 创建专业的气象图

#### 5. 文件管理
- 上传、下载和管理模型输入/输出文件
- 批量处理数据文件
- 组织和存储模拟结果

### 技术架构

#### 前端
- 基于 HTML、CSS 和 JavaScript 的响应式网页界面
- 使用模板系统组织页面结构
- 实时任务状态监控

#### 后端
- 使用 Python Flask 框架构建 Web 应用
- SQLAlchemy ORM 用于数据库交互
- Paramiko 库用于 SSH 远程连接
- NetCDF4、Matplotlib 和 Cartopy 用于数据处理和可视化

#### 数据存储
- SQLite 数据库存储任务和配置信息
- 文件系统存储上传的配置文件和模型输出

### 使用流程

1. **创建任务**：用户首先创建一个新的 WRF 模拟任务，提供任务名称和描述。
2. **上传配置**：上传 namelist.input 文件，定义模拟的时间、区域和物理参数。
3. **上传数据**：上传必要的气象数据文件（met_em 文件）。
4. **运行模拟**：点击运行按钮，系统将文件传输到远程 WRF 服务器并启动模拟。
5. **监控状态**：用户可以实时监控任务运行状态和进度。
6. **查看结果**：模拟完成后，系统自动处理输出文件并生成可视化结果，用户可以查看和下载这些结果。

### 目标用户

- 气象研究人员
- 天气预报员
- 气象学学生和教师
- 需要进行天气模拟的环境科学家

### 优势特点

1. **简化操作**：通过图形界面简化了 WRF 模型的复杂操作流程
2. **远程执行**：无需在本地安装 WRF，通过远程连接使用已配置好的 WRF 环境
3. **自动可视化**：自动处理模型输出并生成专业气象图表
4. **任务管理**：完整的任务创建、监控和历史记录功能
5. **灵活配置**：支持自定义 namelist 配置，适应不同的模拟需求

这个平台大大降低了使用 WRF 模型的技术门槛，使研究人员能够将更多精力集中在科学问题而非技术细节上，提高了气象研究和预报的效率。