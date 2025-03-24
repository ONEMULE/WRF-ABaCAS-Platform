"""
WRF连接器模块，负责与WRF模型虚拟机的通信和任务管理
"""
import os
import json
import time
import uuid
import paramiko
import logging
import tempfile  # 添加tempfile模块
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
        # 从配置中读取连接信息，而非硬编码
        self.host = getattr(config, 'WRF_VM_HOST', '192.168.44.130')  # 更新默认IP
        self.port = getattr(config, 'WRF_VM_PORT', 2222)  # 添加SSH端口配置
        self.user = getattr(config, 'WRF_VM_USER', 'onemule')
        self.password = getattr(config, 'WRF_VM_PASSWORD', None)  # 添加密码支持

        # 更新WRF相关路径
        self.wrf_path = getattr(config, 'WRF_VM_PATH', '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1')
        self.wps_path = getattr(config, 'WRF_WPS_PATH', '/home/onemule/Models/WRF_TUTORIAL/WPS-4.6.0')  # 添加WPS路径
        self.work_dir = getattr(config, 'WRF_WORK_DIR', '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/test/em_real')

        # 任务目录配置
        self.tasks_root_dir = getattr(config, 'WRF_TASKS_DIR', f"{self.wrf_path}/tasks")
        self.auto_cleanup = getattr(config, 'AUTO_CLEANUP_TASKS', False)  # 是否自动清理任务目录

        # 添加SSH密钥文件路径支持
        self.key_path = getattr(config, 'SSH_KEY_PATH', None)
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

            # 准备连接参数
            connect_params = {
                'hostname': self.host,
                'port': self.port,  # 使用配置的端口
                'username': self.user,
                'timeout': 30
            }

            # 如果配置了密钥文件，使用密钥认证
            if self.key_path and os.path.exists(self.key_path):
                connect_params['key_filename'] = self.key_path
                logger.info(f"使用SSH密钥认证: {self.key_path}")
            # 如果配置了密码，使用密码认证
            elif self.password:
                connect_params['password'] = self.password
                logger.info(f"使用密码认证")

            # 连接到SSH服务器
            self.ssh.connect(**connect_params)
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            logger.info(f"成功连接到WRF虚拟机 {self.host}:{self.port}")
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

    def _get_task_work_dir(self, task):
        """获取任务的独立工作目录路径

        Args:
            task: WrfTask对象

        Returns:
            str: 任务工作目录路径
        """
        return f"{self.tasks_root_dir}/{task.task_id}"

    def submit_job(self, task):
        """提交WRF任务到虚拟机

        Args:
            task: WrfTask对象

        Returns:
            tuple: (成功标志, 消息)
        """
        if not self.connect():
            return False, "无法连接到WRF虚拟机"

        # 创建任务专用工作目录
        task_work_dir = self._get_task_work_dir(task)

        try:
            # 确保任务根目录存在
            self.ssh.exec_command(f"mkdir -p {self.tasks_root_dir}")

            # 检查任务目录是否已存在
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() == 'exists':
                # 如果目录已存在，清理旧内容
                self.ssh.exec_command(f"rm -rf {task_work_dir}/*")
                logger.info(f"清理任务工作目录: {task_work_dir}")
            else:
                # 创建新任务目录
                self.ssh.exec_command(f"mkdir -p {task_work_dir}")
                logger.info(f"创建任务工作目录: {task_work_dir}")

            # 复制必要的执行文件到任务工作目录
            self.ssh.exec_command(f"cp {self.work_dir}/real.exe {self.work_dir}/wrf.exe {task_work_dir}/")

            # 复制必要的表格文件和辅助文件
            cmd_copy_tables = f"""
            cp {self.work_dir}/*.TBL {task_work_dir}/ 2>/dev/null || true
            cp {self.work_dir}/*.formatted {task_work_dir}/ 2>/dev/null || true 
            cp {self.work_dir}/*.txt {task_work_dir}/ 2>/dev/null || true
            """
            self.ssh.exec_command(cmd_copy_tables)

            # 创建必要的软链接 - 链接WRF运行目录中的静态数据文件
            cmd_create_links = f"""
            ln -sf {self.wrf_path}/run/LANDUSE.TBL {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/VEGPARM.TBL {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/SOILPARM.TBL {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/URBPARM.TBL {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/ozone* {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/aerosol* {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/CCN_ACTIVATE.BIN {task_work_dir}/ 2>/dev/null || true
            ln -sf {self.wrf_path}/run/CAMtr_volume_mixing_ratio {task_work_dir}/ 2>/dev/null || true
            """
            self.ssh.exec_command(cmd_create_links)

            logger.info(f"已复制必要文件到任务工作目录")

        except Exception as e:
            logger.error(f"准备任务工作目录失败: {str(e)}")
            return False, f"准备任务工作目录失败: {str(e)}"

        # 上传namelist文件
        try:
            # 创建临时目录 - 使用tempfile模块
            temp_dir = tempfile.gettempdir()

            # 创建本地namelist.input文件
            namelist_input_path = os.path.join(temp_dir, f"namelist.input.{task.task_id}")
            with open(namelist_input_path, "w") as f:
                f.write(task.namelist_input)

            # 上传文件到远程服务器（如果存在则覆盖）
            self.sftp.put(namelist_input_path, f"{task_work_dir}/namelist.input")
            logger.info(f"已上传namelist.input到{task_work_dir}")

            # 如果namelist.wps存在，也上传它
            if hasattr(task, 'namelist_wps') and task.namelist_wps:
                namelist_wps_path = os.path.join(temp_dir, f"namelist.wps.{task.task_id}")
                with open(namelist_wps_path, "w") as f:
                    f.write(task.namelist_wps)
                self.sftp.put(namelist_wps_path, f"{self.wps_path}/namelist.wps")
                logger.info(f"已上传namelist.wps到{self.wps_path}")

        except Exception as e:
            logger.error(f"上传namelist文件失败: {str(e)}")
            return False, f"上传namelist文件失败: {str(e)}"

        # 上传气象数据文件
        try:
            input_files = task.get_input_files_list()  # 使用模型方法而不是直接解析JSON
            for local_path in input_files:
                filename = os.path.basename(local_path)
                remote_path = f"{task_work_dir}/{filename}"

                # 上传文件（如果存在则覆盖）
                self.sftp.put(local_path, remote_path)
                logger.info(f"已上传输入文件: {filename}")
        except Exception as e:
            logger.error(f"上传输入文件失败: {str(e)}")
            return False, f"上传输入文件失败: {str(e)}"

        # 创建并上传运行脚本
        try:
            # 创建用于执行WRF的运行脚本
            run_script = f"""#!/bin/bash
cd {task_work_dir}

# 设置执行环境
export OMP_NUM_THREADS=1
unset MPI_NUM_PROCS
unset SLURM_NTASKS

# 清理之前的输出文件
rm -f wrfout_* rsl.out.* rsl.error.* run_completed.flag run_failed.flag

# 运行real.exe
./real.exe >& real.log

# 检查real.exe执行结果
if [ ! -e wrfinput_d01 ]; then
  echo "ERROR: real.exe执行失败，未生成wrfinput文件" > run_failed.flag
  exit 1
fi

# 运行wrf.exe（单核）
./wrf.exe >& wrf.log

# 检查wrf.exe执行结果
if grep -i "SUCCESS COMPLETE WRF" wrf.log > /dev/null; then
  echo "WRF运行完成" > run_completed.flag
else
  echo "ERROR: wrf.exe执行失败，未完成模拟" > run_failed.flag
fi
"""
            # 写入本地临时脚本 - 使用tempfile模块
            run_script_path = os.path.join(temp_dir, f"run_wrf.sh.{task.task_id}")
            with open(run_script_path, "w") as f:
                f.write(run_script)

            # 上传脚本到独立任务目录
            self.sftp.put(run_script_path, f"{task_work_dir}/run_wrf.sh")

            # 设置执行权限
            self.ssh.exec_command(f"chmod +x {task_work_dir}/run_wrf.sh")
            logger.info("已上传并设置运行脚本")
        except Exception as e:
            logger.error(f"准备运行脚本失败: {str(e)}")
            return False, f"准备运行脚本失败: {str(e)}"

        # 启动WRF任务
        try:
            # 使用nohup在后台运行WRF
            cmd = f"cd {task_work_dir} && nohup ./run_wrf.sh > run.log 2>&1 &"
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
            return task.status, "无法连接到WRF虚拟机"

        # 使用任务特定的工作目录
        task_work_dir = self._get_task_work_dir(task)

        try:
            # 首先检查任务目录是否存在
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() != 'exists':
                return "failed", f"任务工作目录 {task_work_dir} 不存在"

            # 检查是否有错误标志
            try:
                self.sftp.stat(f"{task_work_dir}/run_failed.flag")
                # 获取错误原因
                stdin, stdout, stderr = self.ssh.exec_command(
                    f"cat {task_work_dir}/run_failed.flag")
                error_msg = stdout.read().decode('utf-8').strip()
                return "failed", f"WRF运行失败: {error_msg}"
            except FileNotFoundError:
                pass

            # 检查完成标志文件
            try:
                self.sftp.stat(f"{task_work_dir}/run_completed.flag")
                return "completed", "WRF模拟已成功完成"
            except FileNotFoundError:
                pass

            # 检查是否有错误日志
            stdin, stdout, stderr = self.ssh.exec_command(
                f"grep -i 'error\\|fatal' {task_work_dir}/wrf.log 2>/dev/null || echo ''")
            errors = stdout.read().decode('utf-8').strip()

            if errors:
                return "failed", f"WRF运行出错: {errors[:500]}"  # 截取前500个字符

            # 检查进程是否在运行 - 使用更精确的进程匹配
            stdin, stdout, stderr = self.ssh.exec_command(
                f"ps -ef | grep -E 'wrf.exe|real.exe' | grep -v grep | grep {task.task_id}")
            running = stdout.read().decode('utf-8').strip()

            if running:
                return "running", "WRF任务正在运行中"
            else:
                # 检查日志末尾
                stdin, stdout, stderr = self.ssh.exec_command(
                    f"tail -n 20 {task_work_dir}/wrf.log 2>/dev/null || echo ''")
                log_tail = stdout.read().decode('utf-8').strip()

                if "SUCCESS COMPLETE WRF" in log_tail:
                    return "completed", "WRF模拟已成功完成"
                else:
                    return "failed", "WRF进程已终止，但没有生成完成标志"

        except Exception as e:
            logger.error(f"检查任务状态失败: {str(e)}")
            return task.status, f"检查任务状态失败: {str(e)}"

    def get_results(self, task):
        """从WRF虚拟机获取结果文件

        Args:
            task: WrfTask对象

        Returns:
            bool: 是否成功获取结果
        """
        if not self.connect():
            logger.error(f"无法连接到WRF虚拟机，获取结果失败")
            return False

        # 使用任务特定的工作目录
        task_work_dir = self._get_task_work_dir(task)

        try:
            # 检查任务目录是否存在
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() != 'exists':
                logger.error(f"任务工作目录 {task_work_dir} 不存在，无法获取结果")
                return False

            # 创建结果目录
            results_dir = os.path.join(self.config.RESULTS_FOLDER, task.task_id)
            os.makedirs(results_dir, exist_ok=True)

            # 获取WRF输出文件列表
            stdin, stdout, stderr = self.ssh.exec_command(f"ls -1 {task_work_dir}/wrfout_* 2>/dev/null || echo ''")
            wrfout_list = stdout.read().decode('utf-8').strip()

            if not wrfout_list:
                logger.warning(f"未找到WRF输出文件")

            wrfout_files = wrfout_list.split('\n') if wrfout_list else []

            # 下载每个输出文件
            for remote_path in wrfout_files:
                if not remote_path:
                    continue

                filename = os.path.basename(remote_path)
                local_path = os.path.join(results_dir, filename)

                logger.info(f"下载结果文件: {filename}")
                self.sftp.get(remote_path, local_path)

                # 添加到任务的输出文件列表
                task.add_output_file({
                    "filename": filename,
                    "path": local_path,
                    "type": "wrfout",
                    "size": os.path.getsize(local_path)
                })

            # 下载日志文件
            log_files = ["wrf.log", "real.log", "run.log", "rsl.out.0000", "rsl.error.0000"]
            for log_file in log_files:
                remote_path = f"{task_work_dir}/{log_file}"
                try:
                    # 检查文件是否存在
                    stdin, stdout, stderr = self.ssh.exec_command(f"test -f {remote_path} && echo 'exists'")
                    if stdout.read().decode('utf-8').strip() == 'exists':
                        local_path = os.path.join(results_dir, log_file)
                        self.sftp.get(remote_path, local_path)

                        # 添加到任务的输出文件列表
                        task.add_output_file({
                            "filename": log_file,
                            "path": local_path,
                            "type": "log",
                            "size": os.path.getsize(local_path)
                        })
                except Exception as e:
                    logger.warning(f"无法下载日志文件 {log_file}: {str(e)}")

            # 保存更新
            db.session.commit()
            logger.info(f"已成功获取任务 {task.task_id} 的结果文件")

            # 如果配置了自动清理，在下载完成后清理任务目录
            if self.auto_cleanup:
                self.cleanup_task(task)

            return True

        except Exception as e:
            logger.error(f"获取结果文件失败: {str(e)}")
            return False

    def cleanup_task(self, task):
        """清理任务工作目录

        Args:
            task: WrfTask对象

        Returns:
            bool: 是否成功清理
        """
        if not self.connect():
            logger.error("无法连接到WRF虚拟机，清理任务失败")
            return False

        task_work_dir = self._get_task_work_dir(task)
        try:
            # 检查目录是否存在
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() == 'exists':
                # 删除目录
                self.ssh.exec_command(f"rm -rf {task_work_dir}")
                logger.info(f"已清理任务 {task.task_id} 的工作目录")
                return True
            else:
                logger.warning(f"任务工作目录 {task_work_dir} 不存在，无需清理")
                return True
        except Exception as e:
            logger.error(f"清理任务工作目录失败: {str(e)}")
            return False