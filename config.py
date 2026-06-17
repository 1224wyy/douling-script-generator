import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 默认用 SQLite（本地开发），部署时用 DATABASE_URL 环境变量
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    # Render 给的 URL 是 postgres:// 开头，SQLAlchemy 1.4+ 需要 postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    DATABASE_URL = f'sqlite:///{os.path.join(BASE_DIR, "data", "douling.db")}'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'douling-clone-secret-key')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max upload
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md'}
