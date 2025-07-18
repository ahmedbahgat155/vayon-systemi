#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إعادة إنشاء قاعدة البيانات
"""

import os
import sys
from decimal import Decimal

# إضافة المجلد الحالي للمسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Supplier, Product, Customer

def reset_database():
    """إعادة إنشاء قاعدة البيانات من الصفر"""
    
    with app.app_context():
        print("🔄 بدء إعادة إنشاء قاعدة البيانات...")
        
        # حذف جميع الجداول
        print("🗑️ حذف الجداول القديمة...")
        db.drop_all()
        
        # إنشاء جميع الجداول
        print("🏗️ إنشاء الجداول الجديدة...")
        db.create_all()
        
        # إنشاء المستخدم الافتراضي
        print("👤 إنشاء المستخدم الافتراضي...")
        admin_user = User(
            username='admin',
            email='admin@vayon.com',
            full_name='مدير النظام',
            role='admin',
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        
        # إضافة موردين تجريبيين
        print("🚚 إضافة موردين تجريبيين...")
        suppliers = [
            Supplier(
                name='شركة الأقمشة المصرية',
                contact_person='أحمد محمد',
                phone='01012345678',
                email='info@fabrics-egypt.com',
                address='القاهرة، مصر الجديدة',
                tax_number='123456789',
                payment_terms='آجل 30 يوم',
                credit_limit=Decimal('50000.00'),
                current_balance=Decimal('0.00'),
                supplier_type='raw_materials',
                rating=5,
                notes='مورد موثوق للأقمشة القطنية',
                is_active=True,
                created_by=admin_user.id
            ),
            Supplier(
                name='مصنع الخيوط الحديث',
                contact_person='فاطمة أحمد',
                phone='01098765432',
                email='sales@modern-threads.com',
                address='الإسكندرية، سموحة',
                tax_number='987654321',
                payment_terms='نقداً عند الاستلام',
                credit_limit=Decimal('25000.00'),
                current_balance=Decimal('0.00'),
                supplier_type='raw_materials',
                rating=4,
                notes='متخصص في الخيوط والإكسسوارات',
                is_active=True,
                created_by=admin_user.id
            ),
            Supplier(
                name='شركة الشحن السريع',
                contact_person='محمود علي',
                phone='01155667788',
                email='logistics@fast-shipping.com',
                address='الجيزة، المهندسين',
                payment_terms='آجل 15 يوم',
                credit_limit=Decimal('10000.00'),
                current_balance=Decimal('0.00'),
                supplier_type='services',
                rating=4,
                notes='خدمات شحن وتوصيل',
                is_active=True,
                created_by=admin_user.id
            )
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        # إضافة منتجات تجريبية
        print("📦 إضافة منتجات تجريبية...")
        products = [
            Product(
                name='قماش قطني أبيض',
                code='FAB-001',
                type='raw_material',
                category='أقمشة',
                unit='متر',
                cost_price=Decimal('25.00'),
                selling_price=Decimal('35.00'),
                current_stock=Decimal('100.00'),
                min_stock=Decimal('10.00'),
                is_active=True,
                created_by=admin_user.id
            ),
            Product(
                name='خيط بوليستر أحمر',
                code='THR-001',
                type='raw_material',
                category='خيوط',
                unit='بكرة',
                cost_price=Decimal('15.00'),
                selling_price=Decimal('22.00'),
                current_stock=Decimal('50.00'),
                min_stock=Decimal('5.00'),
                is_active=True,
                created_by=admin_user.id
            ),
            Product(
                name='أزرار بلاستيك',
                code='BTN-001',
                type='raw_material',
                category='إكسسوارات',
                unit='قطعة',
                cost_price=Decimal('0.50'),
                selling_price=Decimal('1.00'),
                current_stock=Decimal('1000.00'),
                min_stock=Decimal('100.00'),
                is_active=True,
                created_by=admin_user.id
            )
        ]
        
        for product in products:
            db.session.add(product)
        
        # إضافة عملاء تجريبيين
        print("👥 إضافة عملاء تجريبيين...")
        customers = [
            Customer(
                name='محل الأزياء الحديثة',
                phone='01123456789',
                email='info@modern-fashion.com',
                address='القاهرة، وسط البلد',
                city='القاهرة',
                notes='عميل تجزئة',
                is_active=True,
                created_by=admin_user.id
            ),
            Customer(
                name='مصنع الملابس الجاهزة',
                phone='01234567890',
                email='orders@garment-factory.com',
                address='الإسكندرية، برج العرب',
                city='الإسكندرية',
                notes='عميل مصنع',
                is_active=True,
                created_by=admin_user.id
            )
        ]
        
        for customer in customers:
            db.session.add(customer)
        
        # حفظ جميع التغييرات
        db.session.commit()
        
        print("✅ تم إنشاء قاعدة البيانات بنجاح!")
        print(f"👤 المستخدم: admin / كلمة المرور: admin123")
        print(f"🚚 تم إضافة {len(suppliers)} موردين")
        print(f"📦 تم إضافة {len(products)} منتجات")
        print(f"👥 تم إضافة {len(customers)} عملاء")

if __name__ == '__main__':
    reset_database()
