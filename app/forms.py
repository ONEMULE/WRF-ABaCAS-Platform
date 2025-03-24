from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired, Length, Optional

class CreateTaskForm(FlaskForm):
    """Form for creating WRF tasks"""
    name = StringField('任务名称', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('任务描述', validators=[Optional(), Length(max=500)])
    submit = SubmitField('创建任务')

class UploadNamelistForm(FlaskForm):
    """Form for uploading Namelist configuration files"""
    namelist_input = FileField('Namelist.input 文件', validators=[
        FileRequired(message='请选择namelist.input文件'),
        FileAllowed(['txt', 'input'], '只允许上传文本文件或.input文件')
    ])
    namelist_wps = FileField('Namelist.wps 文件', validators=[
        FileRequired(message='请选择namelist.wps文件'),
        FileAllowed(['txt', 'wps'], '只允许上传文本文件或.wps文件')
    ])
    description = TextAreaField('配置描述', validators=[
        Length(max=500, message='描述不能超过500个字符')
    ])
    submit = SubmitField('上传配置')

class TaskNamelistUploadForm(FlaskForm):
    """Form for uploading namelist files in tasks"""
    task_id = HiddenField('任务ID')
    namelist_file = FileField('Namelist.input 文件', validators=[
        FileRequired(message='请选择namelist.input文件'),
        FileAllowed(['txt', 'input'], '只允许上传文本文件或.input文件')
    ])
    submit = SubmitField('上传Namelist')

class UploadMetFilesForm(FlaskForm):
    """Form for uploading NetCDF meteorological data files"""
    task_id = HiddenField('任务ID')
    met_files = MultipleFileField('气象数据文件', validators=[
        FileRequired()
    ])
    submit = SubmitField('上传气象数据文件')