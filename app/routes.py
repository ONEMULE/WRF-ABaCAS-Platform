from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from datetime import datetime
import os
import json
import uuid
from werkzeug.utils import secure_filename

from app import db
from app.models import NamelistConfig, WrfTask
from app.forms import CreateTaskForm, UploadNamelistForm, UploadMetFilesForm, TaskNamelistUploadForm

# Modified here: Change Blueprint name from 'main' to empty string to ensure it matches root path
bp = Blueprint('main', __name__)

# Index page
@bp.route('/')
@bp.route('/index')
def index():
    """Index page"""
    # Confirm template can be rendered
    return render_template('index.html')

# Set upload file directory
def get_task_upload_dir(task_id):
    """Get task file upload directory"""
    task_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], task_id)
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    return task_dir

# Namelist configuration routes
@bp.route('/namelists')
def namelist_list():
    """Namelist configuration list page"""
    namelists = NamelistConfig.query.all()
    return render_template('wrf/namelist_list.html', namelists=namelists)

@bp.route('/namelists/<int:namelist_id>')
def namelist_detail(namelist_id):
    """Show namelist configuration details"""
    # Get namelist configuration
    namelist = NamelistConfig.query.get_or_404(namelist_id)

    # Read namelist file content
    namelist_input_content = ""
    namelist_wps_content = ""

    if namelist.namelist_input_path and os.path.exists(namelist.namelist_input_path):
        with open(namelist.namelist_input_path, 'r') as f:
            namelist_input_content = f.read()

    if namelist.namelist_wps_path and os.path.exists(namelist.namelist_wps_path):
        with open(namelist.namelist_wps_path, 'r') as f:
            namelist_wps_content = f.read()

    return render_template('wrf/namelist_detail.html',
                          namelist=namelist,
                          namelist_input_content=namelist_input_content,
                          namelist_wps_content=namelist_wps_content)

# Task management routes
@bp.route('/tasks')
def task_list():
    """Task list page"""
    tasks = WrfTask.query.order_by(WrfTask.created_at.desc()).all()
    return render_template('tasks/list.html', tasks=tasks)

@bp.route('/tasks/create', methods=['GET', 'POST'])
def create_task():
    """Create new task"""
    form = CreateTaskForm()

    if form.validate_on_submit():
        # Create new task
        task = WrfTask(
            task_id=str(uuid.uuid4()),
            name=form.name.data,
            description=form.description.data,
            status='pending'
        )
        db.session.add(task)
        db.session.commit()

        # Create task directory
        task_dir = get_task_upload_dir(task.task_id)

        flash('任务创建成功！请继续上传所需文件。', 'success')
        return redirect(url_for('main.task_detail', task_id=task.task_id))

    return render_template('tasks/create.html', form=form)

@bp.route('/tasks/<task_id>')
def task_detail(task_id):
    """Task detail page"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # Use task specific form
    namelist_form = TaskNamelistUploadForm()
    namelist_form.task_id.data = task_id

    met_files_form = UploadMetFilesForm()
    met_files_form.task_id.data = task_id

    # Get uploaded files list
    input_files = task.get_input_files_list()

    # Check if namelist.input is uploaded
    namelist_uploaded = task.namelist_input is not None and task.namelist_input.strip() != ''

    return render_template('tasks/detail.html',
                          task=task,
                          namelist_form=namelist_form,
                          met_files_form=met_files_form,
                          input_files=input_files,
                          namelist_uploaded=namelist_uploaded)

@bp.route('/tasks/<task_id>/upload/namelist', methods=['POST'])
def upload_namelist(task_id):
    """Upload namelist.input file"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()
    form = TaskNamelistUploadForm()  # Use task specific form
    if form.validate_on_submit():
        namelist_file = form.namelist_file.data
        filename = secure_filename('namelist.input')

        # Save file
        task_dir = get_task_upload_dir(task_id)
        file_path = os.path.join(task_dir, filename)
        namelist_file.save(file_path)

        # Read file content and store to database
        with open(file_path, 'r') as f:
            task.namelist_input = f.read()

        db.session.commit()
        flash('namelist.input文件上传成功！', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.task_detail', task_id=task_id))

@bp.route('/tasks/<task_id>/upload/metfiles', methods=['POST'])
def upload_met_files(task_id):
    """Upload meteorological data files"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()
    form = UploadMetFilesForm()

    if form.validate_on_submit():
        files = form.met_files.data

        task_dir = get_task_upload_dir(task_id)
        uploaded_files = []

        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(task_dir, filename)
                file.save(file_path)

                # Add file path to task input files list
                task.add_input_file(file_path)
                uploaded_files.append(filename)

        if uploaded_files:
            db.session.commit()
            flash(f'成功上传 {len(uploaded_files)} 个文件！', 'success')
        else:
            flash('未选择任何文件！', 'warning')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')

    return redirect(url_for('main.task_detail', task_id=task_id))

@bp.route('/tasks/<task_id>/files/<filename>')
def task_file(task_id, filename):
    """Download task file"""
    task_dir = get_task_upload_dir(task_id)
    return send_from_directory(task_dir, filename)

@bp.route('/tasks/<task_id>/delete')
def delete_task(task_id):
    """Delete task"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # Delete task directory and files
    task_dir = get_task_upload_dir(task_id)
    if os.path.exists(task_dir):
        for file in os.listdir(task_dir):
            os.remove(os.path.join(task_dir, file))
        os.rmdir(task_dir)

    # Delete database record
    db.session.delete(task)
    db.session.commit()

    flash('任务已成功删除！', 'success')
    return redirect(url_for('main.task_list'))

# File management routes
@bp.route('/files')
def file_list():
    """File list page"""
    # Simple implementation, can be improved later
    return render_template('files/list.html')

@bp.route('/files/upload')
def file_upload():
    """File upload page"""
    return render_template('files/upload.html')

@bp.route('/files/batch')
def batch_process():
    """Batch process page"""
    return render_template('files/batch_process.html')

# WRF management routes
@bp.route('/wrf/namelist/upload', methods=['GET', 'POST'])
def namelist_upload():
    """Upload namelist configuration page"""
    # Create form instance
    form = UploadNamelistForm()

    # Handle form submission
    if form.validate_on_submit():
        # Create new NamelistConfig object
        namelist_config = NamelistConfig(
            name=f"Namelist配置 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=form.description.data
        )

        # Save namelist.input file
        input_file = form.namelist_input.data
        input_filename = secure_filename(input_file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'namelists')

        # Ensure upload directory exists
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Save file path
        input_path = os.path.join(upload_dir, input_filename)
        input_file.save(input_path)
        namelist_config.namelist_input_path = input_path

        # Save namelist.wps file
        wps_file = form.namelist_wps.data
        wps_filename = secure_filename(wps_file.filename)
        wps_path = os.path.join(upload_dir, wps_filename)
        wps_file.save(wps_path)
        namelist_config.namelist_wps_path = wps_path

        # Save to database
        db.session.add(namelist_config)
        db.session.commit()

        flash('Namelist配置文件上传成功！', 'success')
        return redirect(url_for('main.namelist_list'))

    # GET request or form validation failed
    return render_template('wrf/namelist_upload.html', form=form)

@bp.route('/wrf/run')
def wrf_run():
    """Run WRF page"""
    return render_template('wrf/run.html')

@bp.route('/wrf/tasks')
def wrf_task_list():
    """WRF task list page"""
    return render_template('wrf/task_list.html')

# New: Run WRF task route
@bp.route('/tasks/<task_id>/run', methods=['POST'])
def run_task(task_id):
    """Run WRF task"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()
    
    # Check task status
    if task.status not in ['pending']:
        flash('只能运行处于等待状态的任务!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    # Check if required input files exist
    if not task.namelist_input:
        flash('任务缺少namelist.input文件!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    # Check if meteorological data files exist
    input_files = task.get_input_files_list()
    if not input_files:
        flash('任务缺少气象数据文件!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    try:
        # Create WRF connector and submit task
        from app.wrf.connector import WrfConnector
        connector = WrfConnector(current_app.config)
        
        # Set task status to running
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # Submit task
        success, message = connector.submit_job(task)
        
        if success:
            flash(f'成功提交WRF任务: {message}', 'success')
        else:
            # If submission failed, reset status
            task.status = 'pending'
            task.started_at = None
            db.session.commit()
            flash(f'提交WRF任务失败: {message}', 'danger')
            
        return redirect(url_for('main.task_detail', task_id=task_id))
    except Exception as e:
        # Restore task status on exception
        task.status = 'pending'
        task.started_at = None
        db.session.commit()
        
        flash(f'运行WRF任务时发生错误: {str(e)}', 'danger')
        current_app.logger.error(f'Error running task {task_id}: {str(e)}')
        return redirect(url_for('main.task_detail', task_id=task_id))

# New: Test WRF connection
@bp.route('/wrf/test_connection')
def test_wrf_connection():
    """Test WRF virtual machine connection"""
    try:
        from app.wrf.connector import WrfConnector
        connector = WrfConnector(current_app.config)
        success = connector.connect()
        
        if success:
            return jsonify({
                'success': True, 
                'message': '成功连接到WRF虚拟机'
            })
        else:
            return jsonify({
                'success': False, 
                'message': '连接WRF虚拟机失败'
            })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'测试连接时发生错误: {str(e)}'
        })