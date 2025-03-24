"""
WRF连接器模块，负责与WRF模型虚拟机的通信和任务管理
"""
import os
import json
import time
import uuid
import paramiko
import logging
from datetime import datetime
from app import db
from app.models import WrfTask

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('wrf_connector')


class WrfConnector:
    """WRF连接器类，用于与WRF虚拟机通信"""

    def __init__(self, config):
        """初始化连接器

        Args:
            config: 应用配置对象
        """
        self.config = config
        self.host = "192.168.9.139"  # 指定的Ubuntu虚拟机IP
        self.user = "onemule"        # 指定的用户名
        self.wrf_path = "/home/onemule/WRF/src/v4.6.1/WRF"  # WRF安装路径
        self.work_dir = "/home/onemule/WRF/src/v4.6.1/WRF/test/em_real"  # 工作目录
        self.ssh = None
        self.sftp = None
        self.connected = False

    def connect(self):
        """连接到WRF虚拟机"""
        if self.connected:
            return True

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接（使用无密码SSH认证）
            self.ssh.connect(self.host, username=self.user, timeout=30)
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            logger.info(f"成功连接到WRF虚拟机 {self.host}")
            return True
        except Exception as e:
            logger.error(f"连接WRF虚拟机失败: {str(e)}")
            return False

    def disconnect(self):
        """断开与WRF虚拟机的连接"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        self.connected = False
        logger.info("已断开与WRF虚拟机的连接")

    def submit_job(self, task):
        """提交WRF任务到虚拟机

        Args:
            task: WrfTask对象

        Returns:
            tuple: (成功标志, 消息)
        """
        if not self.connect():
            return False, "无法连接到WRF虚拟机"

        # 使用指定的工作目录
        remote_work_dir = self.work_dir
        
        # 上传namelist文件
        try:
            # 创建本地namelist.input文件
            with open(f"/tmp/namelist.input.{task.task_id}", "w") as f:
                f.write(task.namelist_input)

            # 上传文件到远程服务器（如果存在则覆盖）
            self.sftp.put(f"/tmp/namelist.input.{task.task_id}", f"{remote_work_dir}/namelist.input")
            logger.info(f"已上传namelist.input到{remote_work_dir}")
            
            # 如果namelist.wps存在，也上传它
            if hasattr(task, 'namelist_wps') and task.namelist_wps:
                with open(f"/tmp/namelist.wps.{task.task_id}", "w") as f:
                    f.write(task.namelist_wps)
                self.sftp.put(f"/tmp/namelist.wps.{task.task_id}", f"{remote_work_dir}/namelist.wps")
                logger.info(f"已上传namelist.wps到{remote_work_dir}")
                
        except Exception as e:
            logger.error(f"上传namelist文件失败: {str(e)}")
            return False, f"上传namelist文件失败: {str(e)}"

        # 上传气象数据文件
        try:
            input_files = json.loads(task.input_files)
            for local_path in input_files:
                filename = os.path.basename(local_path)
                remote_path = f"{remote_work_dir}/{filename}"

                # 上传文件（如果存在则覆盖）
                self.sftp.put(local_path, remote_path)
                logger.info(f"已上传输入文件: {filename}")
        except Exception as e:
            logger.error(f"上传输入文件失败: {str(e)}")
            return False, f"上传输入文件失败: {str(e)}"

        # 创建并上传运行脚本
        try:
            # 创建用于单核执行WRF的运行脚本
            run_script = f"""#!/bin/bash
cd {remote_work_dir}

# 设置单核执行环境
export OMP_NUM_THREADS=1
unset MPI_NUM_PROCS
unset SLURM_NTASKS

# 运行real.exe
./real.exe >& real.log

# 运行wrf.exe（单核）
./wrf.exe >& wrf.log

# 创建完成标志
echo "WRF运行完成" > run_completed.flag
"""
            # 写入本地临时脚本
            with open(f"/tmp/run_wrf.sh.{task.task_id}", "w") as f:
                f.write(run_script)

            # 上传脚本到远程服务器
            self.sftp.put(f"/tmp/run_wrf.sh.{task.task_id}", f"{remote_work_dir}/run_wrf.sh")

            # 设置执行权限
            self.ssh.exec_command(f"chmod +x {remote_work_dir}/run_wrf.sh")
            logger.info("已上传并设置运行脚本")
        except Exception as e:
            logger.error(f"准备运行脚本失败: {str(e)}")
            return False, f"准备运行脚本失败: {str(e)}"

        # 启动WRF任务
        try:
            # 使用nohup在后台运行WRF
            cmd = f"cd {remote_work_dir} && nohup ./run_wrf.sh > run.log 2>&1 &"
            self.ssh.exec_command(cmd)

            logger.info(f"已启动WRF任务: {cmd}")
            return True, "WRF任务已提交到虚拟机运行"
        except Exception as e:
            logger.error(f"启动WRF任务失败: {str(e)}")
            return False, f"启动WRF任务失败: {str(e)}"

    def check_job_status(self, task):
        """检查WRF任务状态

        Args:
            task: WrfTask对象

        Returns:
            tuple: (状态, 消息)
        """
        if not self.connect():
            return "unknown", "无法连接到WRF虚拟机"

        remote_work_dir = self.work_dir

        # 检查完成标志
        try:
            self.sftp.stat(f"{remote_work_dir}/run_completed.flag")
            
            # 检查wrf.log中的错误
            _, stdout, _ = self.ssh.exec_command(f"grep -i 'error\\|fatal' {remote_work_dir}/wrf.log")
            errors = stdout.read().decode().strip()

            if errors:
                return "failed", f"WRF运行完成但存在错误: {errors}"
            else:
                return "completed", "WRF运行成功完成"
        except FileNotFoundError:
            # 检查wrf.exe是否正在运行
            _, stdout, _ = self.ssh.exec_command(f"ps aux | grep wrf.exe | grep -v grep")
            processes = stdout.read().decode().strip()

            if processes:
                # 获取运行进度
                _, stdout, _ = self.ssh.exec_command(f"tail -n 20 {remote_work_dir}/wrf.log")
                log_tail = stdout.read().decode().strip()

                # 尝试从日志中提取时间步进度
                progress = "正在运行"
                import re
                time_step_match = re.search(r'Timing for main: time (\d+\.\d+)', log_tail)
                if time_step_match:
                    progress = f"正在运行，时间步: {time_step_match.group(1)}"

                return "running", progress
            
            # 检查real.exe是否正在运行
            _, stdout, _ = self.ssh.exec_command(f"ps aux | grep real.exe | grep -v grep")
            processes = stdout.read().decode().strip()
            
            if processes:
                return "running", "正在运行real.exe（预处理）"
                
            # 检查是否有错误日志
            _, stdout, _ = self.ssh.exec_command(f"grep -i 'error\\|fatal' {remote_work_dir}/real.log {remote_work_dir}/wrf.log 2>/dev/null || true")
            errors = stdout.read().decode().strip()

            if errors:
                return "failed", f"WRF运行失败: {errors}"
            else:
                # 检查进程是否已提交但尚未启动
                _, stdout, _ = self.ssh.exec_command(f"cat {remote_work_dir}/run.log 2>/dev/null || true")
                log_content = stdout.read().decode().strip()
                
                if log_content:
                    return "running", "WRF任务已提交，正在准备运行"
                else:
                    return "unknown", "WRF任务状态未知"

    def get_results(self, task):
        """获取WRF任务结果

        Args:
            task: WrfTask对象

        Returns:
            tuple: (成功标志, 消息, 结果文件列表)
        """
        if not self.connect():
            return False, "无法连接到WRF虚拟机", []

        remote_work_dir = self.work_dir
        local_result_dir = os.path.join(self.config['RESULTS_FOLDER'], task.task_id)

        # 确保本地结果目录存在
        os.makedirs(local_result_dir, exist_ok=True)

        try:
            # 获取远程输出文件列表（wrfout文件和日志）
            _, stdout, _ = self.ssh.exec_command(f"find {remote_work_dir} -name 'wrfout_*' -o -name '*.log'")
            remote_files = stdout.read().decode().strip().split('\n')

            # 下载结果文件
            result_files = []
            for remote_path in remote_files:
                if not remote_path:  # 跳过空行
                    continue

                filename = os.path.basename(remote_path)
                local_path = os.path.join(local_result_dir, filename)

                self.sftp.get(remote_path, local_path)
                result_files.append(local_path)
                logger.info(f"已下载结果文件: {filename}")

            # 更新任务状态
            task.output_files = json.dumps(result_files)
            task.completed_at = datetime.utcnow()
            db.session.commit()

            return True, f"成功下载 {len(result_files)} 个结果文件", result_files
        except Exception as e:
            logger.error(f"获取结果文件失败: {str(e)}")
            return False, f"获取结果文件失败: {str(e)}", []