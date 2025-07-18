from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

# دالة لتوليد UUID
def generate_uuid():
    return str(uuid.uuid4())

# 1. جدول المستخدمين
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# 2. جدول فواتير البيع
class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_address = db.Column(db.Text)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    
    # تفاصيل الفاتورة
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    discount_percentage = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # معلومات الدفع
    payment_method = db.Column(db.String(50))  # cash, card, transfer
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial
    
    # معلومات الشحن
    shipping_number = db.Column(db.String(100))  # رقم البوليصة
    shipping_company = db.Column(db.String(100))
    shipping_cost = db.Column(db.Float, default=0.0)
    shipping_status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered
    collection_status = db.Column(db.String(20), default='pending')  # pending, collected, failed
    
    # معلومات النظام
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # العلاقات
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('SaleReturn', backref='original_sale', lazy=True)
    
    def __repr__(self):
        return f'<Sale {self.invoice_number}>'

# 3. جدول عناصر فواتير البيع
class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    
    product_name = db.Column(db.String(100), nullable=False)  # نسخة من اسم المنتج وقت البيع
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)
    
    # تكلفة المنتج وقت البيع (لحساب الربح)
    cost_price = db.Column(db.Float, default=0.0)
    manufacturing_cost = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<SaleItem {self.product_name}>'

# 4. جدول مرتجعات البيع
class SaleReturn(db.Model):
    __tablename__ = 'sales_returns'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    
    total_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='approved')  # pending, approved, rejected
    
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    items = db.relationship('SaleReturnItem', backref='sale_return', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SaleReturn {self.return_number}>'

# 5. جدول عناصر مرتجعات البيع
class SaleReturnItem(db.Model):
    __tablename__ = 'sale_return_items'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    return_id = db.Column(db.String(36), db.ForeignKey('sales_returns.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<SaleReturnItem {self.product_name}>'

# 6. جدول فواتير الشراء
class Purchase(db.Model):
    __tablename__ = 'purchases'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    supplier_phone = db.Column(db.String(20))
    supplier_address = db.Column(db.Text)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    
    # تفاصيل الفاتورة
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    discount_percentage = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # معلومات الدفع
    payment_method = db.Column(db.String(50))
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')
    
    # معلومات النظام
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # العلاقات
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('PurchaseReturn', backref='original_purchase', lazy=True)
    
    def __repr__(self):
        return f'<Purchase {self.invoice_number}>'

# 7. جدول عناصر فواتير الشراء
class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    purchase_id = db.Column(db.String(36), db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)

    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<PurchaseItem {self.product_name}>'

# 8. جدول مرتجعات الشراء
class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_returns'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_purchase_id = db.Column(db.String(36), db.ForeignKey('purchases.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())

    total_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='approved')

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    items = db.relationship('PurchaseReturnItem', backref='purchase_return', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PurchaseReturn {self.return_number}>'

# 9. جدول عناصر مرتجعات الشراء
class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    return_id = db.Column(db.String(36), db.ForeignKey('purchase_returns.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)

    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<PurchaseReturnItem {self.product_name}>'

# 10. جدول المنتجات
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    product_type = db.Column(db.String(20), nullable=False)  # raw (خام) أو finished (جاهز)
    unit = db.Column(db.String(20), nullable=False)  # متر، قطعة، كيلو، إلخ

    # الأسعار والتكاليف
    cost_price = db.Column(db.Float, default=0.0)  # سعر الشراء
    selling_price = db.Column(db.Float, default=0.0)  # سعر البيع
    manufacturing_cost = db.Column(db.Float, default=0.0)  # تكلفة التصنيع للمنتجات الجاهزة

    # المخزون
    current_stock = db.Column(db.Float, default=0.0)
    min_stock_level = db.Column(db.Float, default=0.0)

    # معلومات إضافية
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)

    # معلومات النظام
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    inventory_movements = db.relationship('InventoryMovement', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

# 11. جدول حركة المخزون
class InventoryMovement(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)

    movement_type = db.Column(db.String(20), nullable=False)  # in, out
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)

    # المرجع (فاتورة، مرتجع، تعديل يدوي)
    reference_type = db.Column(db.String(50))  # sale, purchase, sale_return, purchase_return, adjustment
    reference_id = db.Column(db.String(36))
    reference_number = db.Column(db.String(50))  # رقم الفاتورة أو المرتجع

    # معلومات إضافية
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InventoryMovement {self.product.name}: {self.movement_type} {self.quantity}>'

# 12. جدول الخزينة
class Treasury(db.Model):
    __tablename__ = 'treasury'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    name = db.Column(db.String(100), nullable=False)  # الخزينة الرئيسية، خزينة الشحن
    treasury_type = db.Column(db.String(20), nullable=False)  # main, shipping
    current_balance = db.Column(db.Float, default=0.0)

    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    transactions = db.relationship('TreasuryTransaction', backref='treasury', lazy=True)

    def __repr__(self):
        return f'<Treasury {self.name}>'

# 13. جدول حركات الخزينة
class TreasuryTransaction(db.Model):
    __tablename__ = 'treasury_transactions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    treasury_id = db.Column(db.String(36), db.ForeignKey('treasury.id'), nullable=False)

    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    # المرجع
    reference_type = db.Column(db.String(50))  # sale, purchase, sale_return, purchase_return, manual
    reference_id = db.Column(db.String(36))
    reference_number = db.Column(db.String(50))

    # معلومات النظام
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TreasuryTransaction {self.transaction_type}: {self.amount}>'

# 14. جدول الشحنات
class Shipment(db.Model):
    __tablename__ = 'shipments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)

    # معلومات البوليصة
    tracking_number = db.Column(db.String(100), unique=True, nullable=False)  # رقم البوليصة
    shipping_company = db.Column(db.String(100), nullable=False)
    shipping_cost = db.Column(db.Float, default=0.0)

    # حالات الشحن
    shipping_status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered, returned
    collection_status = db.Column(db.String(20), default='pending')  # pending, collected, failed

    # التواريخ
    shipped_date = db.Column(db.Date)
    delivered_date = db.Column(db.Date)
    collection_date = db.Column(db.Date)

    # معلومات إضافية
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقة
    sale = db.relationship('Sale', backref='shipment', uselist=False)

    def __repr__(self):
        return f'<Shipment {self.tracking_number}>'

# 15. جدول الصلاحيات
class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # صلاحيات فواتير البيع
    can_view_sales = db.Column(db.Boolean, default=True)
    can_create_sales = db.Column(db.Boolean, default=False)
    can_edit_sales = db.Column(db.Boolean, default=False)
    can_delete_sales = db.Column(db.Boolean, default=False)

    # صلاحيات فواتير الشراء
    can_view_purchases = db.Column(db.Boolean, default=True)
    can_create_purchases = db.Column(db.Boolean, default=False)
    can_edit_purchases = db.Column(db.Boolean, default=False)
    can_delete_purchases = db.Column(db.Boolean, default=False)

    # صلاحيات المرتجعات
    can_view_returns = db.Column(db.Boolean, default=True)
    can_create_returns = db.Column(db.Boolean, default=False)
    can_edit_returns = db.Column(db.Boolean, default=False)
    can_delete_returns = db.Column(db.Boolean, default=False)

    # صلاحيات المخزون
    can_view_inventory = db.Column(db.Boolean, default=True)
    can_edit_inventory = db.Column(db.Boolean, default=False)
    can_delete_inventory = db.Column(db.Boolean, default=False)

    # صلاحيات الخزينة
    can_view_treasury = db.Column(db.Boolean, default=True)
    can_edit_treasury = db.Column(db.Boolean, default=False)

    # صلاحيات الشحن
    can_view_shipments = db.Column(db.Boolean, default=True)
    can_edit_shipments = db.Column(db.Boolean, default=False)

    # صلاحيات التقارير
    can_view_reports = db.Column(db.Boolean, default=True)
    can_view_profit_reports = db.Column(db.Boolean, default=False)  # تقارير الأرباح حساسة

    # صلاحيات إدارية
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_permissions = db.Column(db.Boolean, default=False)
    can_backup = db.Column(db.Boolean, default=False)

    # معلومات النظام
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقة
    user = db.relationship('User', backref='permissions', foreign_keys=[user_id])

    def __repr__(self):
        return f'<Permission for {self.user.username}>'

# 16. جدول السجلات (Logs)
class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, logout
    table_name = db.Column(db.String(50))  # اسم الجدول المتأثر
    record_id = db.Column(db.String(36))  # معرف السجل المتأثر

    old_values = db.Column(db.Text)  # القيم القديمة (JSON)
    new_values = db.Column(db.Text)  # القيم الجديدة (JSON)

    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقة
    user = db.relationship('User', backref='logs')

    def __repr__(self):
        return f'<Log {self.action} by {self.user.username}>'

# 17. جدول النسخ الاحتياطية
class Backup(db.Model):
    __tablename__ = 'backups'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # بالبايت

    backup_type = db.Column(db.String(20), default='auto')  # auto, manual
    status = db.Column(db.String(20), default='success')  # success, failed, in_progress
    error_message = db.Column(db.Text)

    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Backup {self.filename}>'
