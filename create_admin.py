#!/usr/bin/env python3
"""
إنشاء حساب المدير الأول مباشرة في قاعدة البيانات
"""

import os
import sys
from vayon_advanced import app, db
from advanced_database import User, Treasury

def create_admin_account():
    """إنشاء حساب المدير الأول"""
    
    print("🔧 إنشاء حساب المدير الأول...")
    
    with app.app_context():
        try:
            # إنشاء الجداول إذا لم تكن موجودة
            db.create_all()
            print("✅ تم إنشاء قاعدة البيانات")
            
            # التحقق من وجود مدير بالفعل
            existing_admin = User.query.filter_by(role='admin').first()
            if existing_admin:
                print(f"⚠️  يوجد مدير بالفعل: {existing_admin.username}")
                response = input("هل تريد حذف المدير الحالي وإنشاء جديد؟ (y/n): ")
                if response.lower() != 'y':
                    print("❌ تم إلغاء العملية")
                    return False
                
                # حذف المدير الحالي
                db.session.delete(existing_admin)
                db.session.commit()
                print("🗑️  تم حذف المدير الحالي")
            
            # بيانات المدير الافتراضية
            admin_data = {
                'username': 'admin',
                'email': 'admin@vayon.com',
                'full_name': 'مدير النظام',
                'password': 'admin123'
            }
            
            print("\n📝 بيانات المدير الافتراضية:")
            print(f"اسم المستخدم: {admin_data['username']}")
            print(f"البريد الإلكتروني: {admin_data['email']}")
            print(f"الاسم الكامل: {admin_data['full_name']}")
            print(f"كلمة المرور: {admin_data['password']}")
            
            response = input("\nهل تريد استخدام هذه البيانات؟ (y/n): ")
            if response.lower() != 'y':
                # إدخال بيانات مخصصة
                admin_data['username'] = input("اسم المستخدم: ") or admin_data['username']
                admin_data['email'] = input("البريد الإلكتروني: ") or admin_data['email']
                admin_data['full_name'] = input("الاسم الكامل: ") or admin_data['full_name']
                admin_data['password'] = input("كلمة المرور: ") or admin_data['password']
            
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
            
            # إنشاء الخزائن الافتراضية إذا لم تكن موجودة
            main_treasury = Treasury.query.filter_by(treasury_type='main').first()
            if not main_treasury:
                main_treasury = Treasury(
                    name='الخزينة الرئيسية',
                    treasury_type='main',
                    current_balance=0.0,
                    description='الخزينة الرئيسية للشركة'
                )
                db.session.add(main_treasury)
                print("✅ تم إنشاء الخزينة الرئيسية")
            
            shipping_treasury = Treasury.query.filter_by(treasury_type='shipping').first()
            if not shipping_treasury:
                shipping_treasury = Treasury(
                    name='خزينة شركة الشحن',
                    treasury_type='shipping',
                    current_balance=0.0,
                    description='خزينة خاصة بأموال شركة الشحن'
                )
                db.session.add(shipping_treasury)
                print("✅ تم إنشاء خزينة الشحن")
            
            # حفظ جميع التغييرات
            db.session.commit()
            
            print("\n🎉 تم إنشاء حساب المدير بنجاح!")
            print("="*50)
            print("📋 بيانات تسجيل الدخول:")
            print(f"🔑 اسم المستخدم: {admin_data['username']}")
            print(f"🔐 كلمة المرور: {admin_data['password']}")
            print(f"📧 البريد الإلكتروني: {admin_data['email']}")
            print("="*50)
            print("🌐 يمكنك الآن تسجيل الدخول للنظام")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ في إنشاء المدير: {e}")
            return False

if __name__ == "__main__":
    print("🚀 مرحباً بك في أداة إنشاء المدير - نظام VAYON")
    print("="*50)
    
    success = create_admin_account()
    
    if success:
        print("\n✅ العملية مكتملة بنجاح!")
        print("🔗 اذهب الآن لرابط النظام وسجل دخول")
    else:
        print("\n❌ فشلت العملية!")
        
    input("\nاضغط Enter للخروج...")
