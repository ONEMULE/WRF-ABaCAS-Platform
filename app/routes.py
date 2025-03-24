from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_from_directory
from datetime import datetime
import os
import json
import uuid
from werkzeug.utils import secure_filename

from app import db
from app.models import NamelistConfig, WrfTask
from app.forms import CreateTaskForm, UploadNamelistForm, UploadMetFilesForm, TaskNamelistUploadForm

# 修改这里：将Blueprint名称从'main'改为空字符串，以确保它匹配根路径
bp = Blueprint('main', __name__)

# Index page
@bp.route('/')
@bp.route('/index')
def index():
    """首页"""
    # 确认有模板可以渲染
    return render_template('index.html')

# 设置上传文件的目录
def get_task_upload_dir(task_id):
    """获取任务的文件上传目录"""
    task_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], task_id)
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    return task_dir

# Namelist configuration routes
@bp.route('/namelists')
def namelist_list():
    """Namelist配置列表页面"""
    namelists = NamelistConfig.query.all()
    return render_template('wrf/namelist_list.html', namelists=namelists)

@bp.route('/namelists/<int:namelist_id>')
def namelist_detail(namelist_id):
    """显示namelist配置详情"""
    # 获取namelist配置
    namelist = NamelistConfig.query.get_or_404(namelist_id)

    # 读取namelist文件内容
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

# 任务管理路由
@bp.route('/tasks')
def task_list():
    """任务列表页面"""
    tasks = WrfTask.query.order_by(WrfTask.created_at.desc()).all()
    return render_template('tasks/list.html', tasks=tasks)

@bp.route('/tasks/create', methods=['GET', 'POST'])
def create_task():
    """创建新任务"""
    form = CreateTaskForm()

    if form.validate_on_submit():
        # 创建新任务
        task = WrfTask(
            task_id=str(uuid.uuid4()),
            name=form.name.data,
            description=form.description.data,
            status='pending'
        )
        db.session.add(task)
        db.session.commit()

        # 创建任务目录
        task_dir = get_task_upload_dir(task.task_id)

        flash('任务创建成功！请继续上传所需文件。', 'success')
        return redirect(url_for('main.task_detail', task_id=task.task_id))

    return render_template('tasks/create.html', form=form)

@bp.route('/tasks/<task_id>')
def task_detail(task_id):
    """任务详情页面"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # 使用任务特定的表单
    namelist_form = TaskNamelistUploadForm()
    namelist_form.task_id.data = task_id

    met_files_form = UploadMetFilesForm()
    met_files_form.task_id.data = task_id

    # 获取已上传的文件列表
    input_files = task.get_input_files_list()

    # 检查是否已上传namelist.input
    namelist_uploaded = task.namelist_input is not None and task.namelist_input.strip() != ''

    return render_template('tasks/detail.html',
                          task=task,
                          namelist_form=namelist_form,
                          met_files_form=met_files_form,
                          input_files=input_files,
                          namelist_uploaded=namelist_uploaded)

@bp.route('/tasks/<task_id>/upload/namelist', methods=['POST'])
def upload_namelist(task_id):
    """上传namelist.input文件"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()
    form = TaskNamelistUploadForm()  # 使用任务特定的表单
    if form.validate_on_submit():
        namelist_file = form.namelist_file.data
        filename = secure_filename('namelist.input')

        # 保存文件
        task_dir = get_task_upload_dir(task_id)
        file_path = os.path.join(task_dir, filename)
        namelist_file.save(file_path)

        # 读取文件内容并存储到数据库
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
    """上传气象数据文件"""
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

                # 添加文件路径到任务的输入文件列表
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
    """下载任务文件"""
    task_dir = get_task_upload_dir(task_id)
    return send_from_directory(task_dir, filename)

@bp.route('/tasks/<task_id>/delete')
def delete_task(task_id):
    """删除任务"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # 删除任务目录及文件
    task_dir = get_task_upload_dir(task_id)
    if os.path.exists(task_dir):
        for file in os.listdir(task_dir):
            os.remove(os.path.join(task_dir, file))
        os.rmdir(task_dir)

    # 删除数据库记录
    db.session.delete(task)
    db.session.commit()

    flash('任务已成功删除！', 'success')
    return redirect(url_for('main.task_list'))

# 文件管理路由
@bp.route('/files')
def file_list():
    """文件列表页面"""
    # 简单实现，稍后可完善
    return render_template('files/list.html')

@bp.route('/files/upload')
def file_upload():
    """文件上传页面"""
    return render_template('files/upload.html')

@bp.route('/files/batch')
def batch_process():
    """批量处理页面"""
    return render_template('files/batch_process.html')

# WRF管理路由
@bp.route('/wrf/namelist/upload', methods=['GET', 'POST'])
def namelist_upload():
    """上传namelist配置页面"""
    # 创建表单实例
    form = UploadNamelistForm()

    # 处理表单提交
    if form.validate_on_submit():
        # 创建新的NamelistConfig对象
        namelist_config = NamelistConfig(
            name=f"Namelist配置 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description=form.description.data
        )

        # 保存namelist.input文件
        input_file = form.namelist_input.data
        input_filename = secure_filename(input_file.filename)
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'namelists')

        # 确保上传目录存在
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # 保存文件路径
        input_path = os.path.join(upload_dir, input_filename)
        input_file.save(input_path)
        namelist_config.namelist_input_path = input_path

        # 保存namelist.wps文件
        wps_file = form.namelist_wps.data
        wps_filename = secure_filename(wps_file.filename)
        wps_path = os.path.join(upload_dir, wps_filename)
        wps_file.save(wps_path)
        namelist_config.namelist_wps_path = wps_path

        # 保存到数据库
        db.session.add(namelist_config)
        db.session.commit()

        flash('Namelist配置文件上传成功！', 'success')
        return redirect(url_for('main.namelist_list'))

    # GET请求或表单验证失败
    return render_template('wrf/namelist_upload.html', form=form)

@bp.route('/wrf/run')
def wrf_run():
    """运行WRF页面"""
    return render_template('wrf/run.html')

@bp.route('/wrf/tasks')
def wrf_task_list():
    """WRF任务列表页面"""
    return render_template('wrf/task_list.html')

# 新增：运行WRF任务路由
@bp.route('/tasks/<task_id>/run', methods=['POST'])
def run_task(task_id):
    """运行WRF任务"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()
    
    # 检查任务状态
    if task.status not in ['pending']:
        flash('只能运行处于等待状态的任务!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    # 检查是否有必需的输入文件
    if not task.namelist_input:
        flash('任务缺少namelist.input文件!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    # 检查是否有气象数据文件
    input_files = task.get_input_files_list()
    if not input_files:
        flash('任务缺少气象数据文件!', 'warning')
        return redirect(url_for('main.task_detail', task_id=task_id))
    
    try:
        # 创建WRF连接器并提交任务
        from app.wrf.connector import WrfConnector
        connector = WrfConnector(current_app.config)
        
        # 设置任务状态为运行中
        task.status = 'running'
        task.started_at = datetime.utcnow()
        db.session.commit()
        
        # 提交任务
        success, message = connector.submit_job(task)
        
        if success:
            flash(f'成功提交WRF任务: {message}', 'success')
        else:
            # 如果提交失败，重置状态
            task.status = 'pending'
            task.started_at = None
            db.session.commit()
            flash(f'提交WRF任务失败: {message}', 'danger')
            
        return redirect(url_for('main.task_detail', task_id=task_id))
    except Exception as e:
        # 发生异常时恢复任务状态
        task.status = 'pending'
        task.started_at = None
        db.session.commit()
        
        flash(f'运行WRF任务时发生错误: {str(e)}', 'danger')
        current_app.logger.error(f'运行任务 {task_id} 时出错: {str(e)}')
        return redirect(url_for('main.task_detail', task_id=task_id))

# 新增：测试WRF连接
@bp.route('/wrf/test_connection')
def test_wrf_connection():
    """测试WRF虚拟机连接"""
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