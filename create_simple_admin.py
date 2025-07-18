#!/usr/bin/env python3
"""
إنشاء حساب المدير الأول - نسخة مبسطة
"""

import os
import sys
from vayon_advanced import app, db
from advanced_database import User, Treasury

def create_simple_admin():
    """إنشاء حساب المدير بشكل مبسط"""
    
    print("🔧 إنشاء حساب المدير...")
    
    with app.app_context():
        try:
            # إنشاء الجداول
            db.create_all()
            print("✅ تم إنشاء قاعدة البيانات")
            
            # حذف أي مدير موجود
            existing_admins = User.query.filter_by(role='admin').all()
            for admin in existing_admins:
                db.session.delete(admin)
            
            if existing_admins:
                print(f"🗑️  تم حذف {len(existing_admins)} مدير موجود")
            
            # بيانات المدير الجديد
            admin_data = {
                'username': 'admin',
                'email': 'admin@vayon.com', 
                'full_name': 'مدير النظام',
                'password': 'admin123'
            }
            
            # إنشاء المدير
            admin = User(
                username=admin_data['username'],
                email=admin_data['email'],
                full_name=admin_data['full_name'],
                role='admin',
                is_active=True
            )
            admin.set_password(admin_data['password'])
            
            db.session.add(admin)
            print("✅ تم إنشاء حساب المدير")
            
            # إنشاء خزينة رئيسية بسيطة
            existing_treasury = Treasury.query.first()
            if not existing_treasury:
                main_treasury = Treasury(
                    name='الخزينة الرئيسية',
                    description='الخزينة الرئيسية للشركة',
                    current_balance=0.0
                )
                db.session.add(main_treasury)
                print("✅ تم إنشاء الخزينة الرئيسية")
            
            # حفظ التغييرات
            db.session.commit()
            
            print("\n🎉 تم إنشاء حساب المدير بنجاح!")
            print("="*50)
            print("📋 بيانات تسجيل الدخول:")
            print(f"🔑 اسم المستخدم: {admin_data['username']}")
            print(f"🔐 كلمة المرور: {admin_data['password']}")
            print(f"📧 البريد الإلكتروني: {admin_data['email']}")
            print("="*50)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ: {e}")
            return False

if __name__ == "__main__":
    print("🚀 إنشاء حساب المدير - نظام VAYON")
    print("="*40)
    
    success = create_simple_admin()
    
    if success:
        print("\n✅ تم بنجاح!")
        print("🌐 اذهب الآن لرابط النظام:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n❌ فشل!")
        
    print("\nاضغط Enter للخروج...")
    input()
