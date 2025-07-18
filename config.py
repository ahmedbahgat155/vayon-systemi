import os
from datetime import timedelta

class Config:
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///vayon.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات الأمان
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vayon-secret-key-2024-fashion-brand'
    WTF_CSRF_ENABLED = True
    
    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # تغيير إلى True في الإنتاج
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # إعدادات التطبيق
    COMPANY_NAME = "VAYON"
    COMPANY_NAME_AR = "فايون"
    
    # إعدادات النسخ الاحتياطي
    BACKUP_INTERVAL_MINUTES = 3
    BACKUP_FOLDER = 'backups'
    MAX_BACKUP_FILES = 100
    
    # إعدادات الألوان
    PRIMARY_COLOR = "#1B222A"      # الأزرق الغامق
    SECONDARY_COLOR = "#DBC7A5"    # البيج الفاتح  
    ACCENT_COLOR = "#916138"       # الجملي
    
    # إعدادات الملفات
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # إعدادات التقارير
    REPORTS_FOLDER = 'reports'
    
    @staticmethod
    def init_app(app):
        # إنشاء المجلدات المطلوبة
        folders = [Config.BACKUP_FOLDER, Config.UPLOAD_FOLDER, Config.REPORTS_FOLDER]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
