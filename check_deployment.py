#!/usr/bin/env python3
"""
سكريبت للتحقق من جاهزية النظام للنشر على Render
"""

import os
import sys
from pathlib import Path

def check_file_exists(filename, description):
    """التحقق من وجود ملف"""
    if os.path.exists(filename):
        print(f"✅ {description}: {filename}")
        return True
    else:
        print(f"❌ {description} مفقود: {filename}")
        return False

def check_file_content(filename, required_content, description):
    """التحقق من محتوى ملف"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            if required_content in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - المحتوى المطلوب غير موجود")
                return False
    except FileNotFoundError:
        print(f"❌ {description} - الملف غير موجود: {filename}")
        return False

def main():
    print("🔍 فحص جاهزية نظام VAYON للنشر على Render")
    print("=" * 50)
    
    all_good = True
    
    # فحص الملفات الأساسية
    print("\n📁 فحص الملفات الأساسية:")
    files_to_check = [
        ("vayon_advanced.py", "الملف الرئيسي للتطبيق"),
        ("advanced_database.py", "ملف قاعدة البيانات"),
        ("requirements.txt", "متطلبات Python"),
        ("Procfile", "ملف تشغيل Render"),
        ("runtime.txt", "إصدار Python"),
        (".gitignore", "ملف Git ignore"),
        ("README.md", "وثائق المشروع"),
    ]
    
    for filename, description in files_to_check:
        if not check_file_exists(filename, description):
            all_good = False
    
    # فحص محتوى الملفات المهمة
    print("\n🔍 فحص محتوى الملفات:")
    
    # فحص Procfile
    if not check_file_content("Procfile", "gunicorn vayon_advanced:app", "Procfile يحتوي على أمر gunicorn"):
        all_good = False
    
    # فحص requirements.txt
    required_packages = ["Flask", "gunicorn", "psycopg2-binary"]
    try:
        with open("requirements.txt", 'r') as f:
            requirements = f.read()
            for package in required_packages:
                if package.lower() in requirements.lower():
                    print(f"✅ {package} موجود في requirements.txt")
                else:
                    print(f"❌ {package} مفقود من requirements.txt")
                    all_good = False
    except FileNotFoundError:
        print("❌ requirements.txt غير موجود")
        all_good = False
    
    # فحص runtime.txt
    if not check_file_content("runtime.txt", "python-3.11", "runtime.txt يحدد Python 3.11"):
        all_good = False
    
    # فحص vayon_advanced.py للإعدادات
    print("\n⚙️ فحص إعدادات التطبيق:")
    
    if not check_file_content("vayon_advanced.py", "os.environ.get('DATABASE_URL')", "دعم متغير DATABASE_URL"):
        all_good = False
    
    if not check_file_content("vayon_advanced.py", "os.environ.get('PORT'", "دعم متغير PORT"):
        all_good = False
    
    # فحص المجلدات المطلوبة
    print("\n📂 فحص المجلدات:")
    folders_to_check = [
        ("static", "ملفات CSS/JS/Images"),
        ("templates", "قوالب HTML"),
        ("static/css", "ملفات CSS"),
        ("static/js", "ملفات JavaScript"),
    ]
    
    for folder, description in folders_to_check:
        if os.path.exists(folder) and os.path.isdir(folder):
            print(f"✅ {description}: {folder}")
        else:
            print(f"❌ {description} مفقود: {folder}")
            all_good = False
    
    # فحص الملفات الحساسة
    print("\n🔒 فحص الأمان:")
    sensitive_files = ["instance/", "*.db", "__pycache__/"]
    
    gitignore_exists = os.path.exists(".gitignore")
    if gitignore_exists:
        with open(".gitignore", 'r') as f:
            gitignore_content = f.read()
            for pattern in sensitive_files:
                if pattern in gitignore_content:
                    print(f"✅ {pattern} مستبعد من Git")
                else:
                    print(f"⚠️ {pattern} قد لا يكون مستبعد من Git")
    
    # النتيجة النهائية
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 النظام جاهز للنشر على Render!")
        print("\n📋 الخطوات التالية:")
        print("1. ارفع الكود على GitHub")
        print("2. أنشئ حساب على Render.com")
        print("3. أنشئ PostgreSQL Database")
        print("4. أنشئ Web Service")
        print("5. اربط GitHub Repository")
        print("6. أضف متغيرات البيئة (SECRET_KEY, DATABASE_URL)")
        print("7. انشر التطبيق!")
        print("\n📖 راجع DEPLOY_GUIDE.md للتفاصيل الكاملة")
        return 0
    else:
        print("❌ هناك مشاكل يجب حلها قبل النشر")
        print("راجع الأخطاء أعلاه وأصلحها")
        return 1

if __name__ == "__main__":
    sys.exit(main())
