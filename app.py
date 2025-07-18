#!/usr/bin/env python3
"""
VAYON - نظام إدارة الأزياء الرجالية الفاخرة
نظام ERP احترافي باللغة العربية
"""

import os
import uuid
import json
import threading
import time
import shutil
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, and_, or_, desc
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vayon-erp-2024-secret')

# إعدادات قاعدة البيانات
if os.environ.get('DATABASE_URL'):
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vayon_erp.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BACKUP_FOLDER'] = 'backups'

# إنشاء المجلدات المطلوبة
os.makedirs('uploads', exist_ok=True)
os.makedirs('backups', exist_ok=True)
os.makedirs('reports', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول لهذه الصفحة'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# ==================== نماذج قاعدة البيانات ====================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # admin, seller, viewer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def can_access(self, resource):
        """التحقق من صلاحيات الوصول"""
        if self.role == 'admin':
            return True
        elif self.role == 'seller':
            return resource in ['dashboard', 'sales', 'customers', 'inventory_view', 'reports_view']
        elif self.role == 'viewer':
            return resource in ['dashboard', 'reports_view', 'inventory_view']
        return False

class BusinessSettings(db.Model):
    __tablename__ = 'business_settings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = db.Column(db.String(200), default='VAYON')
    business_name_en = db.Column(db.String(200), default='VAYON')
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    currency = db.Column(db.String(10), default='ج.م')
    logo_path = db.Column(db.String(255))
    backup_interval = db.Column(db.Integer, default=3)  # دقائق
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # العلاقات
    sales = db.relationship('Sale', backref='customer', lazy=True)



class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # raw_material, finished_product
    category = db.Column(db.String(50))
    unit = db.Column(db.String(20), nullable=False)  # متر، قطعة، كيلو، جرام
    
    # المخزون
    current_stock = db.Column(db.Numeric(12, 3), default=0)
    min_stock = db.Column(db.Numeric(12, 3), default=0)
    
    # الأسعار
    cost_price = db.Column(db.Numeric(12, 2), default=0)  # سعر التكلفة
    selling_price = db.Column(db.Numeric(12, 2), default=0)  # سعر البيع
    manufacturing_cost = db.Column(db.Numeric(12, 2), default=0)  # تكلفة التصنيع
    
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # العلاقات
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    purchase_items = db.relationship('PurchaseItem', backref='product', lazy=True)
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # in, out, adjustment
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2))
    reference_type = db.Column(db.String(20))  # sale, purchase, return, adjustment, manufacturing
    reference_id = db.Column(db.String(36))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

class Cashbox(db.Model):
    __tablename__ = 'cashboxes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # main, shipping
    current_balance = db.Column(db.Numeric(15, 2), default=0)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    transactions = db.relationship('CashTransaction', backref='cashbox', lazy=True)

class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cashbox_id = db.Column(db.String(36), db.ForeignKey('cashboxes.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # in, out, transfer
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    reference_type = db.Column(db.String(20))  # sale, purchase, return, transfer, adjustment
    reference_id = db.Column(db.String(36))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

    # المبالغ
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    paid_amount = db.Column(db.Numeric(15, 2), default=0)
    remaining_amount = db.Column(db.Numeric(15, 2), default=0)

    # الشحن
    shipping_company = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    shipping_status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered
    collection_status = db.Column(db.String(20), default='pending')  # pending, collected, failed

    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, returned, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('SaleReturn', backref='original_sale', lazy=True)

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)
    cost_price = db.Column(db.Numeric(12, 2))  # لحساب الربح
    notes = db.Column(db.Text)

class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)

    # المبالغ
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    paid_amount = db.Column(db.Numeric(15, 2), default=0)
    remaining_amount = db.Column(db.Numeric(15, 2), default=0)

    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('PurchaseReturn', backref='original_purchase', lazy=True)

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id = db.Column(db.String(36), db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)
    notes = db.Column(db.Text)

class SaleReturn(db.Model):
    __tablename__ = 'sale_returns'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    items = db.relationship('SaleReturnItem', backref='sale_return', lazy=True, cascade='all, delete-orphan')

class SaleReturnItem(db.Model):
    __tablename__ = 'sale_return_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_return_id = db.Column(db.String(36), db.ForeignKey('sale_returns.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)

class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_returns'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_purchase_id = db.Column(db.String(36), db.ForeignKey('purchases.id'), nullable=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    items = db.relationship('PurchaseReturnItem', backref='purchase_return', lazy=True, cascade='all, delete-orphan')

class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_return_id = db.Column(db.String(36), db.ForeignKey('purchase_returns.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(15, 2), nullable=False)

class Factory(db.Model):
    __tablename__ = 'factories'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    specialization = db.Column(db.String(100))  # تخصص المصنع (قمصان، بناطيل، إلخ)
    production_capacity = db.Column(db.Integer)  # الطاقة الإنتاجية اليومية
    quality_rating = db.Column(db.Integer, default=5)  # تقييم الجودة من 1-5
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    manufacturing_orders = db.relationship('ManufacturingOrder', backref='factory', lazy=True)

class ManufacturingOrder(db.Model):
    __tablename__ = 'manufacturing_orders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    factory_id = db.Column(db.String(36), db.ForeignKey('factories.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.DateTime)
    actual_delivery_date = db.Column(db.DateTime)

    # الحالة
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled

    # التكاليف
    raw_materials_cost = db.Column(db.Numeric(15, 2), default=0)
    manufacturing_cost = db.Column(db.Numeric(15, 2), default=0)
    total_cost = db.Column(db.Numeric(15, 2), default=0)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    raw_materials = db.relationship('ManufacturingOrderRawMaterial', backref='manufacturing_order', lazy=True, cascade='all, delete-orphan')
    finished_products = db.relationship('ManufacturingOrderFinishedProduct', backref='manufacturing_order', lazy=True, cascade='all, delete-orphan')

class ManufacturingOrderRawMaterial(db.Model):
    __tablename__ = 'manufacturing_order_raw_materials'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manufacturing_order_id = db.Column(db.String(36), db.ForeignKey('manufacturing_orders.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)  # المادة الخام
    quantity_required = db.Column(db.Numeric(12, 3), nullable=False)
    quantity_sent = db.Column(db.Numeric(12, 3), default=0)
    unit_cost = db.Column(db.Numeric(12, 2))
    total_cost = db.Column(db.Numeric(15, 2))
    notes = db.Column(db.Text)

    # العلاقات
    product = db.relationship('Product', backref='manufacturing_raw_materials')

class ManufacturingOrderFinishedProduct(db.Model):
    __tablename__ = 'manufacturing_order_finished_products'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manufacturing_order_id = db.Column(db.String(36), db.ForeignKey('manufacturing_orders.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)  # المنتج الجاهز
    quantity_expected = db.Column(db.Numeric(12, 3), nullable=False)
    quantity_received = db.Column(db.Numeric(12, 3), default=0)
    quality_grade = db.Column(db.String(10), default='A')  # A, B, C
    unit_cost = db.Column(db.Numeric(12, 2))
    total_cost = db.Column(db.Numeric(15, 2))
    notes = db.Column(db.Text)

    # العلاقات
    product = db.relationship('Product', backref='manufacturing_finished_products')

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    tax_number = db.Column(db.String(50))
    payment_terms = db.Column(db.String(100))  # شروط الدفع
    credit_limit = db.Column(db.Numeric(15, 2), default=0)  # حد الائتمان
    current_balance = db.Column(db.Numeric(15, 2), default=0)  # الرصيد الحالي
    supplier_type = db.Column(db.String(50), default='raw_materials')  # raw_materials, services, both
    rating = db.Column(db.Integer, default=5)  # تقييم من 1-5
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    purchase_invoices = db.relationship('PurchaseInvoice', backref='supplier', lazy=True)

class PurchaseInvoice(db.Model):
    __tablename__ = 'purchase_invoices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'), nullable=False)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)

    # المبالغ
    subtotal = db.Column(db.Numeric(15, 2), default=0)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    discount_amount = db.Column(db.Numeric(15, 2), default=0)
    tax_percentage = db.Column(db.Numeric(5, 2), default=0)
    tax_amount = db.Column(db.Numeric(15, 2), default=0)
    shipping_cost = db.Column(db.Numeric(15, 2), default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0)

    # الدفع
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, paid
    paid_amount = db.Column(db.Numeric(15, 2), default=0)
    remaining_amount = db.Column(db.Numeric(15, 2), default=0)
    payment_method = db.Column(db.String(50))  # cash, bank_transfer, check, credit

    # الحالة
    status = db.Column(db.String(20), default='draft')  # draft, confirmed, received, cancelled

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # العلاقات
    items = db.relationship('PurchaseInvoiceItem', backref='purchase_invoice', lazy=True, cascade='all, delete-orphan')

class PurchaseInvoiceItem(db.Model):
    __tablename__ = 'purchase_invoice_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_invoice_id = db.Column(db.String(36), db.ForeignKey('purchase_invoices.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False)
    total_cost = db.Column(db.Numeric(15, 2), nullable=False)
    received_quantity = db.Column(db.Numeric(12, 3), default=0)  # الكمية المستلمة
    notes = db.Column(db.Text)

    # العلاقات
    product = db.relationship('Product', backref='purchase_invoice_items')

class Backup(db.Model):
    __tablename__ = 'backups'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    backup_type = db.Column(db.String(20), default='auto')  # auto, manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))

# ==================== الوظائف المساعدة ====================

def generate_invoice_number(prefix='INV'):
    """توليد رقم فاتورة فريد"""
    today = datetime.now()
    date_str = today.strftime('%Y%m%d')

    if prefix == 'INV':
        # فواتير البيع
        last_invoice = SalesInvoice.query.filter(
            SalesInvoice.invoice_number.like(f'INV-{date_str}-%')
        ).order_by(desc(SalesInvoice.invoice_number)).first()
    elif prefix == 'PUR':
        # فواتير الشراء
        last_invoice = PurchaseInvoice.query.filter(
            PurchaseInvoice.invoice_number.like(f'PUR-{date_str}-%')
        ).order_by(desc(PurchaseInvoice.invoice_number)).first()
    else:
        last_invoice = None

    if last_invoice:
        # استخراج الرقم التسلسلي من آخر فاتورة
        last_number = int(last_invoice.invoice_number.split('-')[-1])
        new_number = last_number + 1
    else:
        new_number = 1

    return f'{prefix}-{date_str}-{new_number:04d}'

def update_stock(product_id, quantity, movement_type, reference_type=None, reference_id=None, unit_cost=None):
    """تحديث المخزون"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return False

        if movement_type == 'in':
            product.current_stock += Decimal(str(quantity))
        elif movement_type == 'out':
            if product.current_stock < Decimal(str(quantity)):
                return False
            product.current_stock -= Decimal(str(quantity))

        # تسجيل حركة المخزون
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=Decimal(str(quantity)),
            unit_cost=Decimal(str(unit_cost)) if unit_cost else None,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=current_user.id if current_user.is_authenticated else None
        )

        db.session.add(movement)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تحديث المخزون: {e}")
        return False

def update_cashbox(cashbox_id, amount, transaction_type, reference_type=None, reference_id=None, description=None):
    """تحديث الخزنة"""
    try:
        cashbox = Cashbox.query.get(cashbox_id)
        if not cashbox:
            return False

        if transaction_type == 'in':
            cashbox.current_balance += Decimal(str(amount))
        elif transaction_type == 'out':
            if cashbox.current_balance < Decimal(str(amount)):
                return False
            cashbox.current_balance -= Decimal(str(amount))

        # تسجيل المعاملة
        transaction = CashTransaction(
            cashbox_id=cashbox_id,
            transaction_type=transaction_type,
            amount=Decimal(str(amount)),
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            created_by=current_user.id if current_user.is_authenticated else None
        )

        db.session.add(transaction)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"خطأ في تحديث الخزنة: {e}")
        return False

# ==================== Routes ====================

@app.route('/health')
def health_check():
    """فحص صحة التطبيق"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'message': 'VAYON ERP System is running'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    try:
        with app.app_context():
            db.create_all()

        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('setup_first_admin'))
    except Exception as e:
        print(f"خطأ في الصفحة الرئيسية: {e}")
        return redirect(url_for('setup_first_admin'))

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    return redirect(url_for('dashboard'))

@app.route('/setup-first-admin', methods=['GET', 'POST'])
def setup_first_admin():
    """إعداد أول مدير"""
    try:
        with app.app_context():
            db.create_all()
        admin_exists = User.query.filter_by(role='admin').first()
        if admin_exists:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"خطأ في إعداد المدير: {e}")

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, full_name, password, confirm_password]):
            flash('جميع الحقول مطلوبة', 'error')
            return render_template('setup_first_admin.html')

        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'error')
            return render_template('setup_first_admin.html')

        if len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل', 'error')
            return render_template('setup_first_admin.html')

        try:
            admin = User(
                username=username,
                email=email,
                full_name=full_name,
                role='admin',
                is_active=True
            )
            admin.set_password(password)

            db.session.add(admin)

            # إنشاء الخزائن الافتراضية
            main_cashbox = Cashbox(
                name='الخزنة الرئيسية',
                type='main',
                current_balance=0,
                description='الخزنة الرئيسية للشركة'
            )

            shipping_cashbox = Cashbox(
                name='خزنة شركة الشحن',
                type='shipping',
                current_balance=0,
                description='خزنة خاصة بأموال شركة الشحن'
            )

            # إنشاء إعدادات الشركة الافتراضية
            business_settings = BusinessSettings(
                business_name='VAYON',
                business_name_en='VAYON',
                address='',
                phone='',
                email=email,
                currency='ج.م'
            )

            db.session.add(main_cashbox)
            db.session.add(shipping_cashbox)
            db.session.add(business_settings)
            db.session.commit()

            flash('تم إنشاء حساب المدير الأول بنجاح', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')

    return render_template('setup_first_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """تسجيل الدخول"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('setup_first_admin'))
    except Exception as e:
        print(f"خطأ في تسجيل الدخول: {e}")
        return redirect(url_for('setup_first_admin'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('اسم المستخدم وكلمة المرور مطلوبان', 'error')
            return render_template('login.html')

        try:
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password) and user.is_active:
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                db.session.commit()

                flash(f'مرحباً بك {user.full_name}', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        except Exception as e:
            flash('حدث خطأ في تسجيل الدخول', 'error')
            print(f"خطأ في تسجيل الدخول: {e}")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم الرئيسية"""
    try:
        # حساب الإحصائيات الأساسية
        today = datetime.now().date()

        # إحصائيات اليوم
        today_sales = Sale.query.filter(
            func.date(Sale.sale_date) == today,
            Sale.status == 'active'
        ).all()

        today_sales_count = len(today_sales)
        today_sales_amount = sum([float(sale.total_amount) for sale in today_sales])
        today_profit = sum([
            float(sale.total_amount) - sum([
                float(item.cost_price or 0) * float(item.quantity)
                for item in sale.items
            ]) for sale in today_sales
        ])

        # إحصائيات عامة
        total_customers = Customer.query.filter_by(is_active=True).count()
        total_products = Product.query.filter_by(is_active=True).count()
        total_suppliers = Supplier.query.filter_by(is_active=True).count()

        # المنتجات منخفضة المخزون
        low_stock_products = Product.query.filter(
            Product.current_stock <= Product.min_stock,
            Product.min_stock > 0,
            Product.is_active == True
        ).count()

        # رصيد الخزائن
        main_cashbox = Cashbox.query.filter_by(type='main', is_active=True).first()
        shipping_cashbox = Cashbox.query.filter_by(type='shipping', is_active=True).first()

        main_balance = float(main_cashbox.current_balance) if main_cashbox else 0
        shipping_balance = float(shipping_cashbox.current_balance) if shipping_cashbox else 0

        # الشحنات المعلقة
        pending_shipments = Sale.query.filter(
            Sale.shipping_status.in_(['pending', 'shipped']),
            Sale.status == 'active'
        ).count()

        # المبيعات غير المحصلة
        unpaid_sales = Sale.query.filter(
            Sale.remaining_amount > 0,
            Sale.status == 'active'
        ).count()

        stats = {
            'today_sales_count': today_sales_count,
            'today_sales_amount': today_sales_amount,
            'today_profit': today_profit,
            'total_customers': total_customers,
            'total_products': total_products,
            'total_suppliers': total_suppliers,
            'low_stock_products': low_stock_products,
            'main_balance': main_balance,
            'shipping_balance': shipping_balance,
            'pending_shipments': pending_shipments,
            'unpaid_sales': unpaid_sales
        }

        # آخر المعاملات
        recent_sales = Sale.query.order_by(desc(Sale.created_at)).limit(5).all()
        recent_purchases = Purchase.query.order_by(desc(Purchase.created_at)).limit(5).all()

        return render_template('dashboard.html',
                             stats=stats,
                             recent_sales=recent_sales,
                             recent_purchases=recent_purchases)

    except Exception as e:
        print(f"خطأ في لوحة التحكم: {e}")
        # إرجاع إحصائيات افتراضية في حالة الخطأ
        stats = {
            'today_sales_count': 0,
            'today_sales_amount': 0,
            'today_profit': 0,
            'total_customers': 0,
            'total_products': 0,
            'total_suppliers': 0,
            'low_stock_products': 0,
            'main_balance': 0,
            'shipping_balance': 0,
            'pending_shipments': 0,
            'unpaid_sales': 0
        }
        return render_template('dashboard.html',
                             stats=stats,
                             recent_sales=[],
                             recent_purchases=[])

# ==================== صفحات إدارة المخزون ====================

@app.route('/inventory')
@login_required
def inventory_list():
    """قائمة المنتجات"""
    try:
        search = request.args.get('search', '')
        product_type = request.args.get('type', '')

        query = Product.query.filter_by(is_active=True)

        if search:
            query = query.filter(
                or_(
                    Product.name.contains(search),
                    Product.code.contains(search)
                )
            )

        if product_type:
            query = query.filter_by(type=product_type)

        products = query.order_by(Product.created_at.desc()).all()

        return render_template('inventory/list.html', products=products, search=search, product_type=product_type)

    except Exception as e:
        flash(f'حدث خطأ في تحميل المنتجات: {str(e)}', 'error')
        return render_template('inventory/list.html', products=[], search='', product_type='')

@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """إضافة منتج جديد"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لإضافة المنتجات', 'error')
        return redirect(url_for('inventory_list'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            code = request.form.get('code')
            product_type = request.form.get('type')
            category = request.form.get('category')
            unit = request.form.get('unit')
            current_stock = request.form.get('current_stock', 0)
            min_stock = request.form.get('min_stock', 0)
            cost_price = request.form.get('cost_price', 0)
            selling_price = request.form.get('selling_price', 0)
            manufacturing_cost = request.form.get('manufacturing_cost', 0)
            description = request.form.get('description', '')

            if not all([name, code, product_type, unit]):
                flash('الحقول المطلوبة: الاسم، الكود، النوع، الوحدة', 'error')
                return render_template('inventory/add.html')

            # التحقق من عدم تكرار الكود
            existing_product = Product.query.filter_by(code=code).first()
            if existing_product:
                flash('كود المنتج موجود مسبقاً', 'error')
                return render_template('inventory/add.html')

            product = Product(
                name=name,
                code=code,
                type=product_type,
                category=category,
                unit=unit,
                current_stock=Decimal(str(current_stock)),
                min_stock=Decimal(str(min_stock)),
                cost_price=Decimal(str(cost_price)),
                selling_price=Decimal(str(selling_price)),
                manufacturing_cost=Decimal(str(manufacturing_cost)),
                description=description,
                created_by=current_user.id
            )

            db.session.add(product)
            db.session.commit()

            flash(f'تم إضافة المنتج "{name}" بنجاح', 'success')
            return redirect(url_for('inventory_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إضافة المنتج: {str(e)}', 'error')

    return render_template('inventory/add.html')

@app.route('/inventory/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """تعديل منتج"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لتعديل المنتجات', 'error')
        return redirect(url_for('inventory_list'))

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.category = request.form.get('category')
            product.unit = request.form.get('unit')
            product.min_stock = Decimal(str(request.form.get('min_stock', 0)))
            product.cost_price = Decimal(str(request.form.get('cost_price', 0)))
            product.selling_price = Decimal(str(request.form.get('selling_price', 0)))
            product.manufacturing_cost = Decimal(str(request.form.get('manufacturing_cost', 0)))
            product.description = request.form.get('description', '')

            db.session.commit()

            flash(f'تم تحديث المنتج "{product.name}" بنجاح', 'success')
            return redirect(url_for('inventory_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في تحديث المنتج: {str(e)}', 'error')

    return render_template('inventory/edit.html', product=product)

@app.route('/inventory/stock-adjustment/<product_id>', methods=['GET', 'POST'])
@login_required
def stock_adjustment(product_id):
    """تعديل المخزون"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لتعديل المخزون', 'error')
        return redirect(url_for('inventory_list'))

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        try:
            adjustment_type = request.form.get('adjustment_type')  # increase, decrease, set
            quantity = Decimal(str(request.form.get('quantity', 0)))
            notes = request.form.get('notes', '')

            old_stock = product.current_stock

            if adjustment_type == 'increase':
                product.current_stock += quantity
                movement_type = 'in'
            elif adjustment_type == 'decrease':
                if product.current_stock < quantity:
                    flash('الكمية المطلوب خصمها أكبر من المخزون المتاح', 'error')
                    return render_template('inventory/stock_adjustment.html', product=product)
                product.current_stock -= quantity
                movement_type = 'out'
            elif adjustment_type == 'set':
                quantity = quantity - old_stock
                product.current_stock = old_stock + quantity
                movement_type = 'in' if quantity >= 0 else 'out'
                quantity = abs(quantity)

            # تسجيل حركة المخزون
            movement = StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity=quantity,
                reference_type='adjustment',
                notes=f"تعديل يدوي: {notes}",
                created_by=current_user.id
            )

            db.session.add(movement)
            db.session.commit()

            flash(f'تم تعديل مخزون "{product.name}" من {old_stock} إلى {product.current_stock}', 'success')
            return redirect(url_for('inventory_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في تعديل المخزون: {str(e)}', 'error')

    return render_template('inventory/stock_adjustment.html', product=product)

# ==================== صفحات إدارة العملاء ====================

@app.route('/customers')
@login_required
def customers_list():
    """قائمة العملاء"""
    if not current_user.can_access('customers'):
        flash('ليس لديك صلاحية لعرض العملاء', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')

        query = Customer.query.filter_by(is_active=True)

        if search:
            query = query.filter(
                or_(
                    Customer.name.contains(search),
                    Customer.phone.contains(search),
                    Customer.email.contains(search)
                )
            )

        customers = query.order_by(Customer.created_at.desc()).all()

        return render_template('customers/list.html', customers=customers, search=search)

    except Exception as e:
        flash(f'حدث خطأ في تحميل العملاء: {str(e)}', 'error')
        return render_template('customers/list.html', customers=[], search='')

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    """إضافة عميل جديد"""
    if not current_user.can_access('customers'):
        flash('ليس لديك صلاحية لإضافة العملاء', 'error')
        return redirect(url_for('customers_list'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            city = request.form.get('city')
            notes = request.form.get('notes')

            if not name:
                flash('اسم العميل مطلوب', 'error')
                return render_template('customers/add.html')

            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(customer)
            db.session.commit()

            flash(f'تم إضافة العميل "{name}" بنجاح', 'success')
            return redirect(url_for('customers_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إضافة العميل: {str(e)}', 'error')

    return render_template('customers/add.html')

@app.route('/customers/edit/<customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    """تعديل عميل"""
    if not current_user.can_access('customers'):
        flash('ليس لديك صلاحية لتعديل العملاء', 'error')
        return redirect(url_for('customers_list'))

    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        try:
            customer.name = request.form.get('name')
            customer.phone = request.form.get('phone')
            customer.email = request.form.get('email')
            customer.address = request.form.get('address')
            customer.city = request.form.get('city')
            customer.notes = request.form.get('notes')

            db.session.commit()

            flash(f'تم تحديث بيانات العميل "{customer.name}" بنجاح', 'success')
            return redirect(url_for('customers_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في تحديث العميل: {str(e)}', 'error')

    return render_template('customers/edit.html', customer=customer)

# ==================== صفحات فواتير البيع ====================

@app.route('/sales')
@login_required
def sales_list():
    """قائمة فواتير البيع"""
    if not current_user.can_access('sales'):
        flash('ليس لديك صلاحية لعرض فواتير البيع', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')
        status = request.args.get('status', '')

        query = Sale.query

        if search:
            query = query.join(Customer).filter(
                or_(
                    Sale.invoice_number.contains(search),
                    Customer.name.contains(search)
                )
            )

        if status:
            query = query.filter_by(status=status)

        sales = query.order_by(desc(Sale.created_at)).all()

        return render_template('sales/list.html', sales=sales, search=search, status=status)

    except Exception as e:
        flash(f'حدث خطأ في تحميل فواتير البيع: {str(e)}', 'error')
        return render_template('sales/list.html', sales=[], search='', status='')

@app.route('/sales/add', methods=['GET', 'POST'])
@login_required
def add_sale():
    """إضافة فاتورة بيع جديدة"""
    if not current_user.can_access('sales'):
        flash('ليس لديك صلاحية لإضافة فواتير البيع', 'error')
        return redirect(url_for('sales_list'))

    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            discount_amount = Decimal(str(request.form.get('discount_amount', 0)))
            tax_amount = Decimal(str(request.form.get('tax_amount', 0)))
            paid_amount = Decimal(str(request.form.get('paid_amount', 0)))
            shipping_company = request.form.get('shipping_company', '')
            notes = request.form.get('notes', '')

            # بيانات المنتجات
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')

            if not customer_id or not product_ids:
                flash('يجب اختيار العميل وإضافة منتج واحد على الأقل', 'error')
                return render_template('sales/add.html',
                                     customers=Customer.query.filter_by(is_active=True).all(),
                                     products=Product.query.filter_by(is_active=True).all())

            # إنشاء الفاتورة
            invoice_number = generate_invoice_number('SAL')

            sale = Sale(
                invoice_number=invoice_number,
                customer_id=customer_id,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                paid_amount=paid_amount,
                shipping_company=shipping_company,
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(sale)
            db.session.flush()  # للحصول على ID الفاتورة

            subtotal = Decimal('0')

            # إضافة عناصر الفاتورة
            for i, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                quantity = Decimal(str(quantities[i]))
                unit_price = Decimal(str(unit_prices[i]))
                total_price = quantity * unit_price

                # التحقق من توفر المخزون
                product = Product.query.get(product_id)
                if product.current_stock < quantity:
                    flash(f'المخزون المتاح من "{product.name}" هو {product.current_stock} {product.unit} فقط', 'error')
                    db.session.rollback()
                    return render_template('sales/add.html',
                                         customers=Customer.query.filter_by(is_active=True).all(),
                                         products=Product.query.filter_by(is_active=True).all())

                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    cost_price=product.cost_price
                )

                db.session.add(sale_item)
                subtotal += total_price

                # تحديث المخزون
                update_stock(product_id, quantity, 'out', 'sale', sale.id, product.cost_price)

            # حساب الإجمالي
            sale.subtotal = subtotal
            sale.total_amount = subtotal - discount_amount + tax_amount
            sale.remaining_amount = sale.total_amount - paid_amount

            # تحديث الخزنة الرئيسية
            if paid_amount > 0:
                main_cashbox = Cashbox.query.filter_by(type='main', is_active=True).first()
                if main_cashbox:
                    update_cashbox(main_cashbox.id, paid_amount, 'in', 'sale', sale.id, f'دفعة من فاتورة {invoice_number}')

            db.session.commit()

            flash(f'تم إنشاء فاتورة البيع رقم {invoice_number} بنجاح', 'success')
            return redirect(url_for('sales_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إنشاء الفاتورة: {str(e)}', 'error')

    customers = Customer.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()

    return render_template('sales/add.html', customers=customers, products=products)

@app.route('/sales/view/<sale_id>')
@login_required
def view_sale(sale_id):
    """عرض فاتورة البيع"""
    if not current_user.can_access('sales'):
        flash('ليس لديك صلاحية لعرض فواتير البيع', 'error')
        return redirect(url_for('dashboard'))

    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales/view.html', sale=sale)

# ==================== صفحات إدارة الخزنة ====================

@app.route('/cashbox')
@login_required
def cashbox_dashboard():
    """لوحة تحكم الخزنة"""
    if not current_user.can_access('treasury'):
        flash('ليس لديك صلاحية لعرض الخزنة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # الخزائن
        cashboxes = Cashbox.query.filter_by(is_active=True).all()

        # آخر المعاملات
        recent_transactions = CashTransaction.query.order_by(desc(CashTransaction.created_at)).limit(10).all()

        # إحصائيات اليوم
        today = datetime.now().date()
        today_transactions = CashTransaction.query.filter(
            func.date(CashTransaction.created_at) == today
        ).all()

        today_income = sum([float(t.amount) for t in today_transactions if t.transaction_type == 'in'])
        today_expenses = sum([float(t.amount) for t in today_transactions if t.transaction_type == 'out'])

        stats = {
            'total_balance': sum([float(c.current_balance) for c in cashboxes]),
            'today_income': today_income,
            'today_expenses': today_expenses,
            'today_net': today_income - today_expenses,
            'transactions_count': len(today_transactions)
        }

        return render_template('cashbox/dashboard.html',
                             cashboxes=cashboxes,
                             recent_transactions=recent_transactions,
                             stats=stats)

    except Exception as e:
        flash(f'حدث خطأ في تحميل بيانات الخزنة: {str(e)}', 'error')
        return render_template('cashbox/dashboard.html',
                             cashboxes=[],
                             recent_transactions=[],
                             stats={})

@app.route('/cashbox/transaction', methods=['GET', 'POST'])
@login_required
def add_cash_transaction():
    """إضافة معاملة نقدية"""
    if not current_user.can_access('treasury'):
        flash('ليس لديك صلاحية لإضافة معاملات نقدية', 'error')
        return redirect(url_for('cashbox_dashboard'))

    if request.method == 'POST':
        try:
            cashbox_id = request.form.get('cashbox_id')
            transaction_type = request.form.get('transaction_type')
            amount = Decimal(str(request.form.get('amount', 0)))
            description = request.form.get('description')

            if not all([cashbox_id, transaction_type, amount > 0, description]):
                flash('جميع الحقول مطلوبة والمبلغ يجب أن يكون أكبر من صفر', 'error')
                return render_template('cashbox/add_transaction.html',
                                     cashboxes=Cashbox.query.filter_by(is_active=True).all())

            # التحقق من رصيد الخزنة في حالة السحب
            if transaction_type == 'out':
                cashbox = Cashbox.query.get(cashbox_id)
                if cashbox.current_balance < amount:
                    flash('رصيد الخزنة غير كافي لهذه العملية', 'error')
                    return render_template('cashbox/add_transaction.html',
                                         cashboxes=Cashbox.query.filter_by(is_active=True).all())

            # تحديث الخزنة
            success = update_cashbox(cashbox_id, amount, transaction_type, 'manual', None, description)

            if success:
                flash('تم تسجيل المعاملة النقدية بنجاح', 'success')
                return redirect(url_for('cashbox_dashboard'))
            else:
                flash('حدث خطأ في تسجيل المعاملة', 'error')

        except Exception as e:
            flash(f'حدث خطأ في تسجيل المعاملة: {str(e)}', 'error')

    cashboxes = Cashbox.query.filter_by(is_active=True).all()
    return render_template('cashbox/add_transaction.html', cashboxes=cashboxes)

# ==================== صفحات إدارة المصانع ====================

@app.route('/factories')
@login_required
def factories_list():
    """قائمة المصانع"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لعرض المصانع', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')

        query = Factory.query.filter_by(is_active=True)

        if search:
            query = query.filter(
                or_(
                    Factory.name.contains(search),
                    Factory.specialization.contains(search),
                    Factory.contact_person.contains(search)
                )
            )

        factories = query.order_by(Factory.created_at.desc()).all()

        return render_template('factories/list.html', factories=factories, search=search)

    except Exception as e:
        flash(f'حدث خطأ في تحميل المصانع: {str(e)}', 'error')
        return render_template('factories/list.html', factories=[], search='')

@app.route('/factories/add', methods=['GET', 'POST'])
@login_required
def add_factory():
    """إضافة مصنع جديد"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لإضافة المصانع', 'error')
        return redirect(url_for('factories_list'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            contact_person = request.form.get('contact_person')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            specialization = request.form.get('specialization')
            production_capacity = request.form.get('production_capacity', 0)
            quality_rating = request.form.get('quality_rating', 5)
            notes = request.form.get('notes')

            if not name:
                flash('اسم المصنع مطلوب', 'error')
                return render_template('factories/add.html')

            factory = Factory(
                name=name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address,
                specialization=specialization,
                production_capacity=int(production_capacity) if production_capacity else 0,
                quality_rating=int(quality_rating),
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(factory)
            db.session.commit()

            flash(f'تم إضافة المصنع "{name}" بنجاح', 'success')
            return redirect(url_for('factories_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إضافة المصنع: {str(e)}', 'error')

    return render_template('factories/add.html')

# ==================== صفحات أوامر التصنيع ====================

@app.route('/manufacturing-orders')
@login_required
def manufacturing_orders_list():
    """قائمة أوامر التصنيع"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لعرض أوامر التصنيع', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')
        status = request.args.get('status', '')

        query = ManufacturingOrder.query

        if search:
            query = query.join(Factory).filter(
                or_(
                    ManufacturingOrder.order_number.contains(search),
                    Factory.name.contains(search)
                )
            )

        if status:
            query = query.filter_by(status=status)

        orders = query.order_by(desc(ManufacturingOrder.created_at)).all()

        return render_template('manufacturing/list.html', orders=orders, search=search, status=status)

    except Exception as e:
        flash(f'حدث خطأ في تحميل أوامر التصنيع: {str(e)}', 'error')
        return render_template('manufacturing/list.html', orders=[], search='', status='')

@app.route('/manufacturing-orders/add', methods=['GET', 'POST'])
@login_required
def add_manufacturing_order():
    """إضافة أمر تصنيع جديد"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لإضافة أوامر التصنيع', 'error')
        return redirect(url_for('manufacturing_orders_list'))

    if request.method == 'POST':
        try:
            factory_id = request.form.get('factory_id')
            expected_delivery_date = request.form.get('expected_delivery_date')
            manufacturing_cost = Decimal(str(request.form.get('manufacturing_cost', 0)))
            notes = request.form.get('notes', '')

            # بيانات المواد الخام
            raw_material_ids = request.form.getlist('raw_material_id[]')
            raw_material_quantities = request.form.getlist('raw_material_quantity[]')

            # بيانات المنتجات الجاهزة
            finished_product_ids = request.form.getlist('finished_product_id[]')
            finished_product_quantities = request.form.getlist('finished_product_quantity[]')

            if not factory_id or not raw_material_ids or not finished_product_ids:
                flash('يجب اختيار المصنع وإضافة مواد خام ومنتجات جاهزة', 'error')
                return render_template('manufacturing/add.html',
                                     factories=Factory.query.filter_by(is_active=True).all(),
                                     raw_materials=Product.query.filter_by(type='raw_material', is_active=True).all(),
                                     finished_products=Product.query.filter_by(type='finished_product', is_active=True).all())

            # إنشاء أمر التصنيع
            order_number = generate_invoice_number('MFG')

            manufacturing_order = ManufacturingOrder(
                order_number=order_number,
                factory_id=factory_id,
                expected_delivery_date=datetime.strptime(expected_delivery_date, '%Y-%m-%d') if expected_delivery_date else None,
                manufacturing_cost=manufacturing_cost,
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(manufacturing_order)
            db.session.flush()  # للحصول على ID الأمر

            raw_materials_cost = Decimal('0')

            # إضافة المواد الخام
            for i, raw_material_id in enumerate(raw_material_ids):
                if not raw_material_id:
                    continue

                quantity = Decimal(str(raw_material_quantities[i]))

                # التحقق من توفر المخزون
                product = Product.query.get(raw_material_id)
                if product.current_stock < quantity:
                    flash(f'المخزون المتاح من "{product.name}" هو {product.current_stock} {product.unit} فقط', 'error')
                    db.session.rollback()
                    return render_template('manufacturing/add.html',
                                         factories=Factory.query.filter_by(is_active=True).all(),
                                         raw_materials=Product.query.filter_by(type='raw_material', is_active=True).all(),
                                         finished_products=Product.query.filter_by(type='finished_product', is_active=True).all())

                unit_cost = product.cost_price
                total_cost = quantity * unit_cost

                raw_material_item = ManufacturingOrderRawMaterial(
                    manufacturing_order_id=manufacturing_order.id,
                    product_id=raw_material_id,
                    quantity_required=quantity,
                    quantity_sent=quantity,  # نفترض أنها ترسل كاملة
                    unit_cost=unit_cost,
                    total_cost=total_cost
                )

                db.session.add(raw_material_item)
                raw_materials_cost += total_cost

                # تحديث المخزون (خصم المواد الخام)
                update_stock(raw_material_id, quantity, 'out', 'manufacturing', manufacturing_order.id, unit_cost)

            # إضافة المنتجات الجاهزة المتوقعة
            for i, finished_product_id in enumerate(finished_product_ids):
                if not finished_product_id:
                    continue

                quantity = Decimal(str(finished_product_quantities[i]))
                product = Product.query.get(finished_product_id)

                finished_product_item = ManufacturingOrderFinishedProduct(
                    manufacturing_order_id=manufacturing_order.id,
                    product_id=finished_product_id,
                    quantity_expected=quantity,
                    unit_cost=product.cost_price
                )

                db.session.add(finished_product_item)

            # حساب التكلفة الإجمالية
            manufacturing_order.raw_materials_cost = raw_materials_cost
            manufacturing_order.total_cost = raw_materials_cost + manufacturing_cost
            manufacturing_order.status = 'in_progress'

            db.session.commit()

            flash(f'تم إنشاء أمر التصنيع رقم {order_number} بنجاح', 'success')
            return redirect(url_for('manufacturing_orders_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إنشاء أمر التصنيع: {str(e)}', 'error')

    factories = Factory.query.filter_by(is_active=True).all()
    raw_materials = Product.query.filter_by(type='raw_material', is_active=True).all()
    finished_products = Product.query.filter_by(type='finished_product', is_active=True).all()

    return render_template('manufacturing/add.html',
                         factories=factories,
                         raw_materials=raw_materials,
                         finished_products=finished_products)

@app.route('/manufacturing-orders/receive/<order_id>', methods=['GET', 'POST'])
@login_required
def receive_manufacturing_order(order_id):
    """استلام الإنتاج من المصنع"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لاستلام الإنتاج', 'error')
        return redirect(url_for('manufacturing_orders_list'))

    order = ManufacturingOrder.query.get_or_404(order_id)

    if order.status != 'in_progress':
        flash('لا يمكن استلام إنتاج من أمر غير قيد التنفيذ', 'error')
        return redirect(url_for('manufacturing_orders_list'))

    if request.method == 'POST':
        try:
            # بيانات المنتجات المستلمة
            product_ids = request.form.getlist('product_id[]')
            quantities_received = request.form.getlist('quantity_received[]')
            quality_grades = request.form.getlist('quality_grade[]')
            notes_list = request.form.getlist('product_notes[]')

            total_received = 0
            quality_issues = 0

            for i, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                quantity_received = Decimal(str(quantities_received[i]))
                quality_grade = quality_grades[i]
                product_notes = notes_list[i] if i < len(notes_list) else ''

                # العثور على المنتج في الأمر
                finished_product = ManufacturingOrderFinishedProduct.query.filter_by(
                    manufacturing_order_id=order_id,
                    product_id=product_id
                ).first()

                if finished_product:
                    finished_product.quantity_received = quantity_received
                    finished_product.quality_grade = quality_grade
                    finished_product.notes = product_notes

                    # إضافة المنتجات للمخزون
                    if quantity_received > 0:
                        update_stock(product_id, quantity_received, 'in', 'manufacturing_receive', order_id, finished_product.unit_cost)
                        total_received += float(quantity_received)

                        if quality_grade in ['B', 'C']:
                            quality_issues += 1

            # تحديث حالة الأمر
            order.status = 'completed'
            order.actual_delivery_date = datetime.utcnow()

            # تحديث تقييم المصنع بناءً على الجودة
            if quality_issues == 0:
                # جودة ممتازة - زيادة التقييم
                if order.factory.quality_rating < 5:
                    order.factory.quality_rating = min(5, order.factory.quality_rating + 0.1)
            elif quality_issues > total_received * 0.3:
                # مشاكل جودة كثيرة - تقليل التقييم
                order.factory.quality_rating = max(1, order.factory.quality_rating - 0.2)

            db.session.commit()

            flash(f'تم استلام الإنتاج من أمر التصنيع {order.order_number} بنجاح', 'success')
            return redirect(url_for('manufacturing_orders_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في استلام الإنتاج: {str(e)}', 'error')

    return render_template('manufacturing/receive.html', order=order)

@app.route('/manufacturing-orders/view/<order_id>')
@login_required
def view_manufacturing_order(order_id):
    """عرض تفاصيل أمر التصنيع"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لعرض أوامر التصنيع', 'error')
        return redirect(url_for('dashboard'))

    order = ManufacturingOrder.query.get_or_404(order_id)
    return render_template('manufacturing/view.html', order=order)

@app.route('/manufacturing-orders/cancel/<order_id>', methods=['POST'])
@login_required
def cancel_manufacturing_order(order_id):
    """إلغاء أمر التصنيع"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لإلغاء أوامر التصنيع', 'error')
        return redirect(url_for('manufacturing_orders_list'))

    order = ManufacturingOrder.query.get_or_404(order_id)

    if order.status not in ['pending', 'in_progress']:
        flash('لا يمكن إلغاء أمر مكتمل أو ملغي مسبقاً', 'error')
        return redirect(url_for('manufacturing_orders_list'))

    try:
        # إرجاع المواد الخام للمخزون
        for raw_material in order.raw_materials:
            if raw_material.quantity_sent > 0:
                update_stock(raw_material.product_id, raw_material.quantity_sent, 'in',
                           'manufacturing_cancel', order_id, raw_material.unit_cost)

        order.status = 'cancelled'
        db.session.commit()

        flash(f'تم إلغاء أمر التصنيع {order.order_number} وإرجاع المواد للمخزون', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ في إلغاء الأمر: {str(e)}', 'error')

    return redirect(url_for('manufacturing_orders_list'))

# ==================== تقارير التصنيع ====================

@app.route('/manufacturing-reports')
@login_required
def manufacturing_reports():
    """تقارير التصنيع والربحية"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لعرض تقارير التصنيع', 'error')
        return redirect(url_for('dashboard'))

    try:
        # إحصائيات عامة
        total_orders = ManufacturingOrder.query.count()
        completed_orders = ManufacturingOrder.query.filter_by(status='completed').count()
        in_progress_orders = ManufacturingOrder.query.filter_by(status='in_progress').count()
        cancelled_orders = ManufacturingOrder.query.filter_by(status='cancelled').count()

        # إحصائيات التكلفة
        completed_orders_list = ManufacturingOrder.query.filter_by(status='completed').all()
        total_manufacturing_cost = sum([float(order.total_cost) for order in completed_orders_list])
        total_raw_materials_cost = sum([float(order.raw_materials_cost) for order in completed_orders_list])
        total_labor_cost = sum([float(order.manufacturing_cost) for order in completed_orders_list])

        # أداء المصانع
        factories_performance = []
        for factory in Factory.query.filter_by(is_active=True).all():
            factory_orders = ManufacturingOrder.query.filter_by(factory_id=factory.id).all()
            completed_count = len([o for o in factory_orders if o.status == 'completed'])
            total_cost = sum([float(o.total_cost) for o in factory_orders if o.status == 'completed'])

            # حساب متوسط وقت التسليم
            delivery_times = []
            for order in factory_orders:
                if order.status == 'completed' and order.expected_delivery_date and order.actual_delivery_date:
                    expected = order.expected_delivery_date
                    actual = order.actual_delivery_date
                    delay_days = (actual - expected).days
                    delivery_times.append(delay_days)

            avg_delay = sum(delivery_times) / len(delivery_times) if delivery_times else 0

            factories_performance.append({
                'factory': factory,
                'total_orders': len(factory_orders),
                'completed_orders': completed_count,
                'total_cost': total_cost,
                'avg_delay_days': avg_delay,
                'quality_rating': factory.quality_rating
            })

        # أوامر متأخرة
        overdue_orders = ManufacturingOrder.query.filter(
            ManufacturingOrder.status == 'in_progress',
            ManufacturingOrder.expected_delivery_date < datetime.now()
        ).all()

        stats = {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'in_progress_orders': in_progress_orders,
            'cancelled_orders': cancelled_orders,
            'total_manufacturing_cost': total_manufacturing_cost,
            'total_raw_materials_cost': total_raw_materials_cost,
            'total_labor_cost': total_labor_cost,
            'completion_rate': (completed_orders / total_orders * 100) if total_orders > 0 else 0
        }

        return render_template('manufacturing/reports.html',
                             stats=stats,
                             factories_performance=factories_performance,
                             overdue_orders=overdue_orders)

    except Exception as e:
        flash(f'حدث خطأ في تحميل التقارير: {str(e)}', 'error')
        return render_template('manufacturing/reports.html',
                             stats={},
                             factories_performance=[],
                             overdue_orders=[])

# ==================== نظام متابعة مواعيد التسليم ====================

@app.route('/manufacturing-orders/delivery-tracking')
@login_required
def delivery_tracking():
    """متابعة مواعيد التسليم"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لمتابعة مواعيد التسليم', 'error')
        return redirect(url_for('dashboard'))

    try:
        today = datetime.now().date()

        # الأوامر المتأخرة
        overdue_orders = ManufacturingOrder.query.filter(
            ManufacturingOrder.status == 'in_progress',
            ManufacturingOrder.expected_delivery_date < today
        ).order_by(ManufacturingOrder.expected_delivery_date).all()

        # الأوامر المستحقة اليوم
        due_today = ManufacturingOrder.query.filter(
            ManufacturingOrder.status == 'in_progress',
            func.date(ManufacturingOrder.expected_delivery_date) == today
        ).all()

        # الأوامر المستحقة خلال الأسبوع القادم
        next_week = today + timedelta(days=7)
        due_this_week = ManufacturingOrder.query.filter(
            ManufacturingOrder.status == 'in_progress',
            ManufacturingOrder.expected_delivery_date > today,
            ManufacturingOrder.expected_delivery_date <= next_week
        ).order_by(ManufacturingOrder.expected_delivery_date).all()

        # إحصائيات التسليم
        all_completed = ManufacturingOrder.query.filter_by(status='completed').all()
        on_time_deliveries = 0
        late_deliveries = 0

        for order in all_completed:
            if order.expected_delivery_date and order.actual_delivery_date:
                if order.actual_delivery_date.date() <= order.expected_delivery_date:
                    on_time_deliveries += 1
                else:
                    late_deliveries += 1

        total_deliveries = on_time_deliveries + late_deliveries
        on_time_percentage = (on_time_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

        stats = {
            'overdue_count': len(overdue_orders),
            'due_today_count': len(due_today),
            'due_this_week_count': len(due_this_week),
            'on_time_percentage': on_time_percentage,
            'total_deliveries': total_deliveries
        }

        return render_template('manufacturing/delivery_tracking.html',
                             overdue_orders=overdue_orders,
                             due_today=due_today,
                             due_this_week=due_this_week,
                             stats=stats)

    except Exception as e:
        flash(f'حدث خطأ في تحميل متابعة التسليم: {str(e)}', 'error')
        return render_template('manufacturing/delivery_tracking.html',
                             overdue_orders=[],
                             due_today=[],
                             due_this_week=[],
                             stats={})

@app.route('/manufacturing-orders/quality-control')
@login_required
def quality_control():
    """نظام مراقبة الجودة"""
    if not current_user.role == 'admin':
        flash('ليس لديك صلاحية لمراقبة الجودة', 'error')
        return redirect(url_for('dashboard'))

    try:
        # إحصائيات الجودة
        completed_orders = ManufacturingOrder.query.filter_by(status='completed').all()

        quality_stats = {
            'grade_a': 0,
            'grade_b': 0,
            'grade_c': 0,
            'total_products': 0
        }

        factory_quality = {}

        for order in completed_orders:
            for finished_product in order.finished_products:
                if finished_product.quantity_received > 0:
                    quality_stats['total_products'] += float(finished_product.quantity_received)

                    if finished_product.quality_grade == 'A':
                        quality_stats['grade_a'] += float(finished_product.quantity_received)
                    elif finished_product.quality_grade == 'B':
                        quality_stats['grade_b'] += float(finished_product.quantity_received)
                    elif finished_product.quality_grade == 'C':
                        quality_stats['grade_c'] += float(finished_product.quantity_received)

                    # إحصائيات المصانع
                    factory_name = order.factory.name
                    if factory_name not in factory_quality:
                        factory_quality[factory_name] = {
                            'grade_a': 0, 'grade_b': 0, 'grade_c': 0, 'total': 0,
                            'factory': order.factory
                        }

                    factory_quality[factory_name]['total'] += float(finished_product.quantity_received)
                    if finished_product.quality_grade == 'A':
                        factory_quality[factory_name]['grade_a'] += float(finished_product.quantity_received)
                    elif finished_product.quality_grade == 'B':
                        factory_quality[factory_name]['grade_b'] += float(finished_product.quantity_received)
                    elif finished_product.quality_grade == 'C':
                        factory_quality[factory_name]['grade_c'] += float(finished_product.quantity_received)

        # حساب النسب المئوية
        if quality_stats['total_products'] > 0:
            quality_stats['grade_a_percentage'] = (quality_stats['grade_a'] / quality_stats['total_products']) * 100
            quality_stats['grade_b_percentage'] = (quality_stats['grade_b'] / quality_stats['total_products']) * 100
            quality_stats['grade_c_percentage'] = (quality_stats['grade_c'] / quality_stats['total_products']) * 100
        else:
            quality_stats['grade_a_percentage'] = 0
            quality_stats['grade_b_percentage'] = 0
            quality_stats['grade_c_percentage'] = 0

        # حساب نسب المصانع
        for factory_name in factory_quality:
            factory_data = factory_quality[factory_name]
            if factory_data['total'] > 0:
                factory_data['grade_a_percentage'] = (factory_data['grade_a'] / factory_data['total']) * 100
                factory_data['quality_score'] = factory_data['grade_a_percentage']
            else:
                factory_data['grade_a_percentage'] = 0
                factory_data['quality_score'] = 0

        # ترتيب المصانع حسب الجودة
        sorted_factories = sorted(factory_quality.items(), key=lambda x: x[1]['quality_score'], reverse=True)

        return render_template('manufacturing/quality_control.html',
                             quality_stats=quality_stats,
                             factory_quality=sorted_factories)

    except Exception as e:
        flash(f'حدث خطأ في تحميل مراقبة الجودة: {str(e)}', 'error')
        return render_template('manufacturing/quality_control.html',
                             quality_stats={},
                             factory_quality=[])

# ==================== صفحات إدارة الموردين ====================

@app.route('/suppliers')
@login_required
def suppliers_list():
    """قائمة الموردين"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لعرض الموردين', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')
        supplier_type = request.args.get('type', '')

        query = Supplier.query.filter_by(is_active=True)

        if search:
            query = query.filter(
                or_(
                    Supplier.name.contains(search),
                    Supplier.contact_person.contains(search),
                    Supplier.phone.contains(search)
                )
            )

        if supplier_type:
            query = query.filter_by(supplier_type=supplier_type)

        suppliers = query.order_by(Supplier.created_at.desc()).all()

        return render_template('suppliers/list.html', suppliers=suppliers, search=search, supplier_type=supplier_type)

    except Exception as e:
        flash(f'حدث خطأ في تحميل الموردين: {str(e)}', 'error')
        return render_template('suppliers/list.html', suppliers=[], search='', supplier_type='')

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    """إضافة مورد جديد"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لإضافة الموردين', 'error')
        return redirect(url_for('suppliers_list'))

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            contact_person = request.form.get('contact_person')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            tax_number = request.form.get('tax_number')
            payment_terms = request.form.get('payment_terms')
            credit_limit = Decimal(str(request.form.get('credit_limit', 0)))
            supplier_type = request.form.get('supplier_type', 'raw_materials')
            rating = int(request.form.get('rating', 5))
            notes = request.form.get('notes')

            if not name:
                flash('اسم المورد مطلوب', 'error')
                return render_template('suppliers/add.html')

            supplier = Supplier(
                name=name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address,
                tax_number=tax_number,
                payment_terms=payment_terms,
                credit_limit=credit_limit,
                supplier_type=supplier_type,
                rating=rating,
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(supplier)
            db.session.commit()

            flash(f'تم إضافة المورد "{name}" بنجاح', 'success')
            return redirect(url_for('suppliers_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إضافة المورد: {str(e)}', 'error')

    return render_template('suppliers/add.html')

# ==================== صفحات فواتير الشراء ====================

@app.route('/purchases')
@login_required
def purchases_list():
    """قائمة فواتير الشراء"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لعرض فواتير الشراء', 'error')
        return redirect(url_for('dashboard'))

    try:
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        payment_status = request.args.get('payment_status', '')

        query = PurchaseInvoice.query

        if search:
            query = query.join(Supplier).filter(
                or_(
                    PurchaseInvoice.invoice_number.contains(search),
                    Supplier.name.contains(search)
                )
            )

        if status:
            query = query.filter_by(status=status)

        if payment_status:
            query = query.filter_by(payment_status=payment_status)

        purchases = query.order_by(desc(PurchaseInvoice.created_at)).all()

        return render_template('purchases/list.html', purchases=purchases, search=search, status=status, payment_status=payment_status)

    except Exception as e:
        flash(f'حدث خطأ في تحميل فواتير الشراء: {str(e)}', 'error')
        return render_template('purchases/list.html', purchases=[], search='', status='', payment_status='')

@app.route('/purchases/add', methods=['GET', 'POST'])
@login_required
def add_purchase():
    """إضافة فاتورة شراء جديدة"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لإضافة فواتير الشراء', 'error')
        return redirect(url_for('purchases_list'))

    if request.method == 'POST':
        try:
            supplier_id = request.form.get('supplier_id')
            due_date = request.form.get('due_date')
            discount_percentage = Decimal(str(request.form.get('discount_percentage', 0)))
            tax_percentage = Decimal(str(request.form.get('tax_percentage', 0)))
            shipping_cost = Decimal(str(request.form.get('shipping_cost', 0)))
            payment_method = request.form.get('payment_method', 'cash')
            notes = request.form.get('notes', '')

            # بيانات المنتجات
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_costs = request.form.getlist('unit_cost[]')

            if not supplier_id or not product_ids:
                flash('يجب اختيار المورد وإضافة منتجات', 'error')
                return render_template('purchases/add.html',
                                     suppliers=Supplier.query.filter_by(is_active=True).all(),
                                     products=Product.query.filter_by(is_active=True).all())

            # إنشاء فاتورة الشراء
            invoice_number = generate_invoice_number('PUR')

            purchase = PurchaseInvoice(
                invoice_number=invoice_number,
                supplier_id=supplier_id,
                due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
                discount_percentage=discount_percentage,
                tax_percentage=tax_percentage,
                shipping_cost=shipping_cost,
                payment_method=payment_method,
                notes=notes,
                created_by=current_user.id
            )

            db.session.add(purchase)
            db.session.flush()  # للحصول على ID الفاتورة

            subtotal = Decimal('0')

            # إضافة عناصر الفاتورة
            for i, product_id in enumerate(product_ids):
                if not product_id:
                    continue

                quantity = Decimal(str(quantities[i]))
                unit_cost = Decimal(str(unit_costs[i]))
                total_cost = quantity * unit_cost

                item = PurchaseInvoiceItem(
                    purchase_invoice_id=purchase.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost
                )

                db.session.add(item)
                subtotal += total_cost

            # حساب المبالغ
            discount_amount = subtotal * (discount_percentage / 100)
            taxable_amount = subtotal - discount_amount + shipping_cost
            tax_amount = taxable_amount * (tax_percentage / 100)
            total_amount = taxable_amount + tax_amount

            purchase.subtotal = subtotal
            purchase.discount_amount = discount_amount
            purchase.tax_amount = tax_amount
            purchase.total_amount = total_amount
            purchase.remaining_amount = total_amount
            purchase.status = 'confirmed'

            db.session.commit()

            flash(f'تم إنشاء فاتورة الشراء رقم {invoice_number} بنجاح', 'success')
            return redirect(url_for('purchases_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ في إنشاء فاتورة الشراء: {str(e)}', 'error')

    suppliers = Supplier.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()

    return render_template('purchases/add.html', suppliers=suppliers, products=products)

@app.route('/purchases/receive/<purchase_id>', methods=['GET', 'POST'])
@login_required
def receive_purchase(purchase_id):
    """استلام البضاعة من فاتورة الشراء"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لاستلام البضاعة', 'error')
        return redirect(url_for('purchases_list'))

    try:
        purchase = PurchaseInvoice.query.get_or_404(purchase_id)

        if purchase.status != 'confirmed':
            flash('يمكن استلام البضاعة فقط من الفواتير المؤكدة', 'error')
            return redirect(url_for('purchases_list'))

        if request.method == 'POST':
            received_quantities = request.form.getlist('received_quantity[]')
            item_ids = request.form.getlist('item_id[]')
            notes = request.form.get('notes', '')

            all_received = True

            # تحديث الكميات المستلمة وتحديث المخزون
            for i, item_id in enumerate(item_ids):
                if not item_id:
                    continue

                item = PurchaseInvoiceItem.query.get(item_id)
                if not item:
                    continue

                received_qty = Decimal(str(received_quantities[i] or 0))

                if received_qty > 0:
                    # تحديث الكمية المستلمة
                    item.received_quantity = (item.received_quantity or 0) + received_qty

                    # تحديث المخزون
                    product = item.product
                    product.current_stock = (product.current_stock or 0) + received_qty

                    # تسجيل حركة المخزون
                    stock_movement = StockMovement(
                        product_id=product.id,
                        movement_type='in',
                        quantity=received_qty,
                        unit_cost=item.unit_cost,
                        reference_type='purchase_receive',
                        reference_id=purchase.id,
                        notes=f'استلام من فاتورة شراء {purchase.invoice_number}',
                        created_by=current_user.id
                    )
                    db.session.add(stock_movement)

                # التحقق من اكتمال الاستلام
                if item.received_quantity < item.quantity:
                    all_received = False

            # تحديث حالة الفاتورة
            if all_received:
                purchase.status = 'received'
            else:
                purchase.status = 'partial_received'

            # إضافة ملاحظات الاستلام
            if notes:
                purchase.notes = (purchase.notes or '') + f'\n\nملاحظات الاستلام ({datetime.now().strftime("%Y-%m-%d %H:%M")}): {notes}'

            db.session.commit()

            flash(f'تم استلام البضاعة من فاتورة {purchase.invoice_number} بنجاح', 'success')
            return redirect(url_for('purchases_list'))

        return render_template('purchases/receive.html', purchase=purchase)

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ في استلام البضاعة: {str(e)}', 'error')
        return redirect(url_for('purchases_list'))

@app.route('/purchases/view/<purchase_id>')
@login_required
def view_purchase(purchase_id):
    """عرض تفاصيل فاتورة الشراء"""
    if not current_user.can_access('purchases'):
        flash('ليس لديك صلاحية لعرض فواتير الشراء', 'error')
        return redirect(url_for('purchases_list'))

    try:
        purchase = PurchaseInvoice.query.get_or_404(purchase_id)
        return render_template('purchases/view.html', purchase=purchase)

    except Exception as e:
        flash(f'حدث خطأ في عرض الفاتورة: {str(e)}', 'error')
        return redirect(url_for('purchases_list'))

# ==================== نظام النسخ الاحتياطي التلقائي ====================

def create_backup():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"vayon_backup_{timestamp}.db"
        backup_path = os.path.join(app.config['BACKUP_FOLDER'], filename)

        # نسخ قاعدة البيانات
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
            else:
                print(f"⚠️ ملف قاعدة البيانات غير موجود: {db_path}")
                return False
        else:
            # للقواعد الأخرى مثل PostgreSQL
            import subprocess
            database_url = app.config['SQLALCHEMY_DATABASE_URI']
            try:
                subprocess.run(['pg_dump', database_url, '-f', backup_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"خطأ في نسخ PostgreSQL: {e}")
                return False

        # تسجيل النسخة الاحتياطية في قاعدة البيانات
        try:
            with app.app_context():
                backup_record = Backup(
                    filename=filename,
                    file_path=backup_path,
                    file_size=os.path.getsize(backup_path) if os.path.exists(backup_path) else 0,
                    backup_type='auto'
                )
                db.session.add(backup_record)
                db.session.commit()
        except Exception as e:
            print(f"خطأ في تسجيل النسخة الاحتياطية: {e}")

        print(f"✅ تم إنشاء نسخة احتياطية: {filename}")
        return True

    except Exception as e:
        print(f"❌ خطأ في إنشاء النسخة الاحتياطية: {e}")
        return False

def auto_backup_worker():
    """عامل النسخ الاحتياطي التلقائي كل 3 دقائق"""
    while True:
        try:
            time.sleep(180)  # 3 دقائق
            create_backup()
        except Exception as e:
            print(f"خطأ في النسخ الاحتياطي التلقائي: {e}")
            time.sleep(60)  # انتظار دقيقة في حالة الخطأ

# بدء النسخ الاحتياطي التلقائي في خيط منفصل
def start_backup_service():
    """بدء خدمة النسخ الاحتياطي"""
    try:
        backup_thread = threading.Thread(target=auto_backup_worker, daemon=True)
        backup_thread.start()
        print("🔄 تم بدء خدمة النسخ الاحتياطي التلقائي")
    except Exception as e:
        print(f"خطأ في بدء خدمة النسخ الاحتياطي: {e}")

def add_sample_data():
    """إضافة بيانات تجريبية"""
    try:
        # إضافة مواد خام تجريبية
        raw_materials = [
            Product(
                name="قماش قطني أبيض",
                type="raw_material",
                category="أقمشة",
                cost_price=Decimal('25.00'),
                selling_price=Decimal('30.00'),
                current_stock=Decimal('100.0'),
                min_stock_level=Decimal('20.0'),
                unit="متر",
                description="قماش قطني عالي الجودة للقمصان",
                is_active=True
            ),
            Product(
                name="خيوط بوليستر",
                type="raw_material",
                category="خيوط",
                cost_price=Decimal('15.00'),
                selling_price=Decimal('20.00'),
                current_stock=Decimal('50.0'),
                min_stock_level=Decimal('10.0'),
                unit="بكرة",
                description="خيوط بوليستر للخياطة",
                is_active=True
            ),
            Product(
                name="أزرار بلاستيك",
                type="raw_material",
                category="إكسسوارات",
                cost_price=Decimal('2.00'),
                selling_price=Decimal('3.00'),
                current_stock=Decimal('500.0'),
                min_stock_level=Decimal('100.0'),
                unit="قطعة",
                description="أزرار بلاستيك متنوعة الألوان",
                is_active=True
            )
        ]

        # إضافة منتجات جاهزة تجريبية
        finished_products = [
            Product(
                name="قميص قطني رجالي",
                type="finished_product",
                category="قمصان",
                cost_price=Decimal('45.00'),
                selling_price=Decimal('80.00'),
                current_stock=Decimal('25.0'),
                min_stock_level=Decimal('5.0'),
                unit="قطعة",
                description="قميص قطني رجالي كلاسيكي",
                is_active=True
            ),
            Product(
                name="بنطلون جينز",
                type="finished_product",
                category="بناطيل",
                cost_price=Decimal('60.00'),
                selling_price=Decimal('120.00'),
                current_stock=Decimal('15.0'),
                min_stock_level=Decimal('3.0'),
                unit="قطعة",
                description="بنطلون جينز عصري",
                is_active=True
            ),
            Product(
                name="جاكيت شتوي",
                type="finished_product",
                category="جاكيتات",
                cost_price=Decimal('85.00'),
                selling_price=Decimal('150.00'),
                current_stock=Decimal('8.0'),
                min_stock_level=Decimal('2.0'),
                unit="قطعة",
                description="جاكيت شتوي دافئ",
                is_active=True
            )
        ]

        # إضافة عملاء تجريبيين
        customers = [
            Customer(
                name="أحمد محمد علي",
                phone="01012345678",
                email="ahmed@example.com",
                address="القاهرة، مصر الجديدة",
                customer_type="individual",
                is_active=True
            ),
            Customer(
                name="شركة الأزياء الحديثة",
                phone="01098765432",
                email="info@modernfashion.com",
                address="الإسكندرية، سموحة",
                customer_type="company",
                is_active=True
            ),
            Customer(
                name="فاطمة أحمد",
                phone="01155667788",
                email="fatma@example.com",
                address="الجيزة، المهندسين",
                customer_type="individual",
                is_active=True
            )
        ]

        # إضافة مصانع تجريبية
        factories = [
            Factory(
                name="مصنع النيل للملابس",
                contact_person="محمد أحمد",
                phone="01011223344",
                email="nile@factory.com",
                address="العاشر من رمضان",
                specialization="قمصان وبلوزات",
                production_capacity=200,
                quality_rating=4.5,
                notes="مصنع متخصص في القمصان الرجالية",
                is_active=True
            ),
            Factory(
                name="مصنع الدلتا للجينز",
                contact_person="سارة محمود",
                phone="01099887766",
                email="delta@jeans.com",
                address="المحلة الكبرى",
                specialization="بناطيل وجينز",
                production_capacity=150,
                quality_rating=4.2,
                notes="متخصص في البناطيل والجينز",
                is_active=True
            )
        ]

        # إضافة خزنتين افتراضيتين إذا لم تكونا موجودتين
        if Cashbox.query.count() == 0:
            cashboxes = [
                Cashbox(
                    name="الخزنة الرئيسية",
                    type="main",
                    current_balance=Decimal('10000.00'),
                    is_active=True
                ),
                Cashbox(
                    name="خزنة الشحن",
                    type="shipping",
                    current_balance=Decimal('2000.00'),
                    is_active=True
                )
            ]
            for cashbox in cashboxes:
                db.session.add(cashbox)

        # حفظ البيانات
        for item in raw_materials + finished_products:
            db.session.add(item)

        for customer in customers:
            db.session.add(customer)

        for factory in factories:
            db.session.add(factory)

        db.session.commit()
        print("✅ تم إضافة البيانات التجريبية بنجاح!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في إضافة البيانات التجريبية: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("🎉 تم إنشاء قاعدة البيانات!")

        # إضافة البيانات التجريبية إذا لم تكن موجودة
        if Product.query.count() == 0:
            add_sample_data()

        print("💎 نظام VAYON ERP جاهز للعمل")
        print("🌐 يمكنك الوصول للنظام على: http://localhost:5000")
        print("🔧 للإعداد الأولي: http://localhost:5000/setup-first-admin")

        # بدء خدمة النسخ الاحتياطي
        start_backup_service()

    port = int(os.environ.get('PORT', 5000))
    debug = not os.environ.get('DATABASE_URL')

    print(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    if debug:
        print("🔧 وضع التطوير مفعل")
    else:
        print("🌐 وضع الإنتاج مفعل")

    app.run(debug=debug, host='0.0.0.0', port=port)
