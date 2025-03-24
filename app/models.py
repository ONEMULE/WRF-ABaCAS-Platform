from datetime import datetime
from app import db
import json

class NamelistConfig(db.Model):
    """Namelist configuration model for WRF"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(500))
    namelist_input_path = db.Column(db.String(255))
    namelist_wps_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Solution 1: Add updated_at column to database
    # Solution 2: Remove updated_at from model (recommended)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WrfTask(db.Model):
    """WRF execution task model"""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    message = db.Column(db.Text)
    namelist_input = db.Column(db.Text)
    input_files = db.Column(db.Text)  # JSON stored file path list
    output_files = db.Column(db.Text)  # JSON stored file objects list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    # Solution 1: Add updated_at column to database
    # Solution 2: Remove updated_at from model (recommended)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def add_input_file(self, file_path):
        """Add input file path"""
        files = self.get_input_files_list()
        if file_path not in files:
            files.append(file_path)
            self.input_files = json.dumps(files)

    def get_input_files_list(self):
        """Get input files path list"""
        if not self.input_files:
            return []
        return json.loads(self.input_files)

    def add_output_file(self, file_info):
        """Add output file information"""
        files = self.get_output_files_list()
        files.append(file_info)
        self.output_files = json.dumps(files)

    def get_output_files_list(self):
        """Get output files information list"""
        if not self.output_files:
            return []
        return json.loads(self.output_files)