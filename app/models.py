from datetime import datetime
from app import db
import json

class NamelistConfig(db.Model):
    """WRF的namelist配置模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(500))
    namelist_input_path = db.Column(db.String(255))
    namelist_wps_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 解决方案1：添加updated_at列到数据库
    # 解决方案2：从模型中删除updated_at (推荐)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WrfTask(db.Model):
    """WRF运行任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    message = db.Column(db.Text)
    namelist_input = db.Column(db.Text)
    input_files = db.Column(db.Text)  # JSON存储的文件路径列表
    output_files = db.Column(db.Text)  # JSON存储的文件对象列表
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    # 解决方案1：添加updated_at列到数据库
    # 解决方案2：从模型中删除updated_at (推荐)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def add_input_file(self, file_path):
        """添加输入文件路径"""
        files = self.get_input_files_list()
        if file_path not in files:
            files.append(file_path)
            self.input_files = json.dumps(files)

    def get_input_files_list(self):
        """获取输入文件路径列表"""
        if not self.input_files:
            return []
        return json.loads(self.input_files)

    def add_output_file(self, file_info):
        """添加输出文件信息"""
        files = self.get_output_files_list()
        files.append(file_info)
        self.output_files = json.dumps(files)

    def get_output_files_list(self):
        """获取输出文件信息列表"""
        if not self.output_files:
            return []
        return json.loads(self.output_files)
        return files