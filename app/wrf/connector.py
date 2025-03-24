"""
WRF Connector Module, responsible for communication with the WRF model virtual machine and task management
"""
import os
import json
import time
import uuid
import paramiko
import logging
import tempfile  # Add tempfile module
from datetime import datetime
from app import db
from app.models import WrfTask

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('wrf_connector')


class WrfConnector:
    """WRF Connector class for communication with WRF virtual machine"""

    def __init__(self, config):
        """Initialize connector

        Args:
            config: Application configuration object
        """
        self.config = config
        # Read connection information from configuration, not hardcoded
        self.host = getattr(config, 'WRF_VM_HOST', '192.168.44.130')  # Update default IP
        self.port = getattr(config, 'WRF_VM_PORT', 2222)  # Add SSH port configuration
        self.user = getattr(config, 'WRF_VM_USER', 'onemule')
        self.password = getattr(config, 'WRF_VM_PASSWORD', '0308')  # Add default password

        # Update WRF related paths
        self.wrf_path = getattr(config, 'WRF_VM_PATH', '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1')
        self.wps_path = getattr(config, 'WRF_WPS_PATH', '/home/onemule/Models/WRF_TUTORIAL/WPS-4.6.0')  # Add WPS path
        self.work_dir = getattr(config, 'WRF_WORK_DIR', '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/test/em_real')

        # Task directory configuration
        self.tasks_root_dir = getattr(config, 'WRF_TASKS_DIR', f"{self.wrf_path}/tasks")
        self.auto_cleanup = getattr(config, 'AUTO_CLEANUP_TASKS', False)  # Whether to automatically clean task directories

        # Add SSH key file path support
        self.key_path = getattr(config, 'SSH_KEY_PATH', None)
        self.ssh = None
        self.sftp = None
        self.connected = False

    def connect(self):
        """Connect to WRF virtual machine"""
        if self.connected:
            return True

        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Prepare connection parameters
            connect_params = {
                'hostname': self.host,
                'port': self.port,  # Use configured port
                'username': self.user,
                'timeout': 30
            }

            # If key file is configured, use key authentication
            if self.key_path and os.path.exists(self.key_path):
                connect_params['key_filename'] = self.key_path
                logger.info(f"Using SSH key authentication: {self.key_path}")
            # If password is configured, use password authentication
            elif self.password:
                connect_params['password'] = self.password
                logger.info(f"Using password authentication")
            else:
                # If neither authentication method is configured, return error
                logger.error(f"SSH authentication failed: Password or key file not configured. Please set WRF_VM_PASSWORD or SSH_KEY_PATH in the configuration")
                return False

            # Connect to SSH server
            self.ssh.connect(**connect_params)
            self.sftp = self.ssh.open_sftp()
            self.connected = True
            logger.info(f"Successfully connected to WRF virtual machine {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WRF virtual machine: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from WRF virtual machine"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        self.connected = False
        logger.info("Disconnected from WRF virtual machine")

    def _get_task_work_dir(self, task):
        """Get the independent working directory path for the task

        Args:
            task: WrfTask object

        Returns:
            str: Task working directory path
        """
        return f"{self.tasks_root_dir}/{task.task_id}"

    def submit_job(self, task):
        """Submit WRF task to virtual machine

        Args:
            task: WrfTask object

        Returns:
            tuple: (success flag, message)
        """
        if not self.connect():
            return False, "Unable to connect to WRF virtual machine"

        # Create task-specific working directory
        task_work_dir = self._get_task_work_dir(task)

        try:
            # Ensure task root directory exists
            self.ssh.exec_command(f"mkdir -p {self.tasks_root_dir}")

            # Check if task directory already exists
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() == 'exists':
                # If directory exists, clean old content
                self.ssh.exec_command(f"rm -rf {task_work_dir}/*")
                logger.info(f"Cleaning task working directory: {task_work_dir}")
            else:
                # Create new task directory
                self.ssh.exec_command(f"mkdir -p {task_work_dir}")
                logger.info(f"Creating task working directory: {task_work_dir}")

            # Copy necessary execution files to task working directory
            self.ssh.exec_command(f"cp {self.work_dir}/real.exe {self.work_dir}/wrf.exe {task_work_dir}/")

            # Copy necessary table files and auxiliary files
            cmd_copy_tables = f"""
            cp {self.work_dir}/*.TBL {task_work_dir}/ 2>/dev/null || true
            cp {self.work_dir}/*.formatted {task_work_dir}/ 2>/dev/null || true 
            cp {self.work_dir}/*.txt {task_work_dir}/ 2>/dev/null || true
            """
            self.ssh.exec_command(cmd_copy_tables)

            # Create necessary symbolic links - link static data files in WRF run directory
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

            logger.info(f"Copied necessary files to task working directory")

        except Exception as e:
            logger.error(f"Failed to prepare task working directory: {str(e)}")
            return False, f"Failed to prepare task working directory: {str(e)}"

        # Upload namelist files
        try:
            # Create temporary directory - using tempfile module
            temp_dir = tempfile.gettempdir()

            # Create local namelist.input file
            namelist_input_path = os.path.join(temp_dir, f"namelist.input.{task.task_id}")
            with open(namelist_input_path, "w") as f:
                f.write(task.namelist_input)

            # Upload file to remote server (overwrite if exists)
            self.sftp.put(namelist_input_path, f"{task_work_dir}/namelist.input")
            logger.info(f"Uploaded namelist.input to {task_work_dir}")

            # If namelist.wps exists, upload it too
            if hasattr(task, 'namelist_wps') and task.namelist_wps:
                namelist_wps_path = os.path.join(temp_dir, f"namelist.wps.{task.task_id}")
                with open(namelist_wps_path, "w") as f:
                    f.write(task.namelist_wps)
                self.sftp.put(namelist_wps_path, f"{self.wps_path}/namelist.wps")
                logger.info(f"Uploaded namelist.wps to {self.wps_path}")

        except Exception as e:
            logger.error(f"Failed to upload namelist files: {str(e)}")
            return False, f"Failed to upload namelist files: {str(e)}"

        # Upload meteorological data files
        try:
            input_files = task.get_input_files_list()  # Use model method instead of parsing JSON directly
            for local_path in input_files:
                filename = os.path.basename(local_path)
                remote_path = f"{task_work_dir}/{filename}"

                # Upload file (overwrite if exists)
                self.sftp.put(local_path, remote_path)
                logger.info(f"Uploaded input file: {filename}")
        except Exception as e:
            logger.error(f"Failed to upload input files: {str(e)}")
            return False, f"Failed to upload input files: {str(e)}"

        # Create and upload run script
        try:
            # Create script for executing WRF
            run_script = f"""#!/bin/bash
cd {task_work_dir}

# Set execution environment
export OMP_NUM_THREADS=1
unset MPI_NUM_PROCS
unset SLURM_NTASKS

# Clean previous output files
rm -f wrfout_* rsl.out.* rsl.error.* run_completed.flag run_failed.flag

# Run real.exe
./real.exe >& real.log

# Check real.exe execution result
if [ ! -e wrfinput_d01 ]; then
  echo "ERROR: real.exe execution failed, wrfinput file not generated" > run_failed.flag
  exit 1
fi

# Run wrf.exe (single core)
./wrf.exe >& wrf.log

# Check wrf.exe execution result
if grep -i "SUCCESS COMPLETE WRF" wrf.log > /dev/null; then
  echo "WRF execution completed" > run_completed.flag
else
  echo "ERROR: wrf.exe execution failed, simulation not completed" > run_failed.flag
fi
"""
            # Write local temporary script - using tempfile module
            run_script_path = os.path.join(temp_dir, f"run_wrf.sh.{task.task_id}")
            with open(run_script_path, "w") as f:
                f.write(run_script)

            # Upload script to independent task directory
            self.sftp.put(run_script_path, f"{task_work_dir}/run_wrf.sh")

            # Set execution permissions
            self.ssh.exec_command(f"chmod +x {task_work_dir}/run_wrf.sh")
            logger.info("Uploaded and configured run script")
        except Exception as e:
            logger.error(f"Failed to prepare run script: {str(e)}")
            return False, f"Failed to prepare run script: {str(e)}"

        # Start WRF task
        try:
            # Use nohup to run WRF in background
            cmd = f"cd {task_work_dir} && nohup ./run_wrf.sh > run.log 2>&1 &"
            self.ssh.exec_command(cmd)

            logger.info(f"Started WRF task: {cmd}")
            return True, "WRF task has been submitted to the virtual machine"
        except Exception as e:
            logger.error(f"Failed to start WRF task: {str(e)}")
            return False, f"Failed to start WRF task: {str(e)}"

    def check_job_status(self, task):
        """Check WRF task status

        Args:
            task: WrfTask object

        Returns:
            tuple: (status, message)
        """
        if not self.connect():
            return task.status, "Unable to connect to WRF virtual machine"

        # Use task-specific working directory
        task_work_dir = self._get_task_work_dir(task)

        try:
            # First check if task directory exists
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() != 'exists':
                return "failed", f"Task working directory {task_work_dir} does not exist"

            # Check for error flag
            try:
                self.sftp.stat(f"{task_work_dir}/run_failed.flag")
                # Get error reason
                stdin, stdout, stderr = self.ssh.exec_command(
                    f"cat {task_work_dir}/run_failed.flag")
                error_msg = stdout.read().decode('utf-8').strip()
                return "failed", f"WRF execution failed: {error_msg}"
            except FileNotFoundError:
                pass

            # Check completion flag file
            try:
                self.sftp.stat(f"{task_work_dir}/run_completed.flag")
                return "completed", "WRF simulation completed successfully"
            except FileNotFoundError:
                pass

            # Check for error logs
            stdin, stdout, stderr = self.ssh.exec_command(
                f"grep -i 'error\\|fatal' {task_work_dir}/wrf.log 2>/dev/null || echo ''")
            errors = stdout.read().decode('utf-8').strip()

            if errors:
                return "failed", f"WRF execution error: {errors[:500]}"  # Truncate to first 500 characters

            # Check if process is running - use more precise process matching
            stdin, stdout, stderr = self.ssh.exec_command(
                f"ps -ef | grep -E 'wrf.exe|real.exe' | grep -v grep | grep {task.task_id}")
            running = stdout.read().decode('utf-8').strip()

            if running:
                return "running", "WRF task is running"
            else:
                # Check log tail
                stdin, stdout, stderr = self.ssh.exec_command(
                    f"tail -n 20 {task_work_dir}/wrf.log 2>/dev/null || echo ''")
                log_tail = stdout.read().decode('utf-8').strip()

                if "SUCCESS COMPLETE WRF" in log_tail:
                    return "completed", "WRF simulation completed successfully"
                else:
                    return "failed", "WRF process has terminated but did not generate completion flag"

        except Exception as e:
            logger.error(f"Failed to check task status: {str(e)}")
            return task.status, f"Failed to check task status: {str(e)}"

    def get_results(self, task):
        """Get result files from WRF virtual machine

        Args:
            task: WrfTask object

        Returns:
            bool: Whether results were successfully retrieved
        """
        if not self.connect():
            logger.error(f"Unable to connect to WRF virtual machine, failed to retrieve results")
            return False

        # Use task-specific working directory
        task_work_dir = self._get_task_work_dir(task)

        try:
            # Check if task directory exists
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() != 'exists':
                logger.error(f"Task working directory {task_work_dir} does not exist, cannot retrieve results")
                return False

            # Create results directory
            results_dir = os.path.join(self.config.RESULTS_FOLDER, task.task_id)
            os.makedirs(results_dir, exist_ok=True)

            # Get WRF output files list
            stdin, stdout, stderr = self.ssh.exec_command(f"ls -1 {task_work_dir}/wrfout_* 2>/dev/null || echo ''")
            wrfout_list = stdout.read().decode('utf-8').strip()

            if not wrfout_list:
                logger.warning(f"No WRF output files found")

            wrfout_files = wrfout_list.split('\n') if wrfout_list else []

            # Download each output file
            for remote_path in wrfout_files:
                if not remote_path:
                    continue

                filename = os.path.basename(remote_path)
                local_path = os.path.join(results_dir, filename)

                logger.info(f"Downloading result file: {filename}")
                self.sftp.get(remote_path, local_path)

                # Add to task's output files list
                task.add_output_file({
                    "filename": filename,
                    "path": local_path,
                    "type": "wrfout",
                    "size": os.path.getsize(local_path)
                })

            # Download log files
            log_files = ["wrf.log", "real.log", "run.log", "rsl.out.0000", "rsl.error.0000"]
            for log_file in log_files:
                remote_path = f"{task_work_dir}/{log_file}"
                try:
                    # Check if file exists
                    stdin, stdout, stderr = self.ssh.exec_command(f"test -f {remote_path} && echo 'exists'")
                    if stdout.read().decode('utf-8').strip() == 'exists':
                        local_path = os.path.join(results_dir, log_file)
                        self.sftp.get(remote_path, local_path)

                        # Add to task's output files list
                        task.add_output_file({
                            "filename": log_file,
                            "path": local_path,
                            "type": "log",
                            "size": os.path.getsize(local_path)
                        })
                except Exception as e:
                    logger.warning(f"Cannot download log file {log_file}: {str(e)}")

            # Save updates
            db.session.commit()
            logger.info(f"Successfully retrieved result files for task {task.task_id}")

            # If auto cleanup is configured, clean task directory after download
            if self.auto_cleanup:
                self.cleanup_task(task)

            return True

        except Exception as e:
            logger.error(f"Failed to retrieve result files: {str(e)}")
            return False

    def cleanup_task(self, task):
        """Clean up task working directory

        Args:
            task: WrfTask object

        Returns:
            bool: Whether cleanup was successful
        """
        if not self.connect():
            logger.error("Unable to connect to WRF virtual machine, failed to clean up task")
            return False

        task_work_dir = self._get_task_work_dir(task)
        try:
            # Check if directory exists
            stdin, stdout, stderr = self.ssh.exec_command(f"test -d {task_work_dir} && echo 'exists'")
            if stdout.read().decode('utf-8').strip() == 'exists':
                # Delete directory
                self.ssh.exec_command(f"rm -rf {task_work_dir}")
                logger.info(f"Cleaned working directory for task {task.task_id}")
                return True
            else:
                logger.warning(f"Task working directory {task_work_dir} does not exist, no cleanup needed")
                return True
        except Exception as e:
            logger.error(f"Failed to clean task working directory: {str(e)}")
            return False