# app/api.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import WrfTask
from app.wrf.connector import WrfConnector
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/tasks/<task_id>/check')
def check_task_status(task_id):
    """检查任务状态API"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # 获取WRF连接器
    from flask import current_app
    connector = WrfConnector(current_app.config)

    # 检查任务状态
    status, message = connector.check_job_status(task)

    # 如果状态改变，更新数据库
    if status != task.status:
        task.status = status
        task.message = message

        if status == 'running' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif status in ['completed', 'failed'] and not task.completed_at:
            task.completed_at = datetime.utcnow()

            # 如果任务完成，获取结果文件
            if status == 'completed':
                connector.get_results(task)

        db.session.commit()

    return jsonify({
        'task_id': task.task_id,
        'status': task.status,
        'message': task.message
    })

@api_bp.route('/tasks/<task_id>/run', methods=['POST'])
def run_task(task_id):
    """运行任务API"""
    task = WrfTask.query.filter_by(task_id=task_id).first_or_404()

    # 只有等待中的任务可以启动
    if task.status != 'pending':
        return jsonify({
            'success': False,
            'message': '只有等待中的任务可以启动'
        }), 400

    # 获取WRF连接器
    from flask import current_app
    connector = WrfConnector(current_app.config)

    # 提交任务
    success, message = connector.submit_job(task)

    if success:
        task.status = 'running'
        task.message = message
        task.started_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'task_id': task.task_id,
            'status': task.status,
            'message': task.message
        })
    else:
        return jsonify({
            'success': False,
            'message': message
        }), 500