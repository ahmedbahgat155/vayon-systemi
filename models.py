from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# سيتم تهيئة db من app.py
db = None

def create_models(database):
    global db
    db = database

    # جدول المستخدمين
    class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, manager, user
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # صلاحيات مخصصة
    can_view_inventory = db.Column(db.Boolean, default=True)
    can_edit_inventory = db.Column(db.Boolean, default=False)
    can_delete_inventory = db.Column(db.Boolean, default=False)
    
    can_view_invoices = db.Column(db.Boolean, default=True)
    can_edit_invoices = db.Column(db.Boolean, default=False)
    can_delete_invoices = db.Column(db.Boolean, default=False)
    
    can_view_returns = db.Column(db.Boolean, default=True)
    can_edit_returns = db.Column(db.Boolean, default=False)
    can_delete_returns = db.Column(db.Boolean, default=False)
    
    can_view_treasury = db.Column(db.Boolean, default=True)
    can_edit_treasury = db.Column(db.Boolean, default=False)
    
    can_view_shipping = db.Column(db.Boolean, default=True)
    can_edit_shipping = db.Column(db.Boolean, default=False)
    
    can_view_reports = db.Column(db.Boolean, default=True)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_backup = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

# جدول العملاء
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقات
    sales_invoices = db.relationship('SalesInvoice', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

# جدول الموردين
class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقات
    purchase_invoices = db.relationship('PurchaseInvoice', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

# جدول فئات المنتجات
class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # علاقات
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'

# جدول المنتجات
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    product_type = db.Column(db.String(20), nullable=False)  # raw (خام) أو finished (جاهز)
    unit = db.Column(db.String(20), nullable=False)  # متر، قطعة، كيلو، إلخ
    current_stock = db.Column(db.Float, default=0.0)
    min_stock_level = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    manufacturing_cost = db.Column(db.Float, default=0.0)  # تكلفة التصنيع للمنتجات الجاهزة
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'

# جدول فواتير البيع
class SalesInvoice(db.Model):
    __tablename__ = 'sales_invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    discount_percentage = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, paid, partial, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # معلومات الشحن
    shipping_company = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    shipping_status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered
    collection_status = db.Column(db.String(20), default='pending')  # pending, collected, failed
    shipping_cost = db.Column(db.Float, default=0.0)

    # علاقات
    items = db.relationship('SalesInvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('SalesReturn', backref='original_invoice', lazy=True)

    def __repr__(self):
        return f'<SalesInvoice {self.invoice_number}>'

# جدول عناصر فاتورة البيع
class SalesInvoiceItem(db.Model):
    __tablename__ = 'sales_invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('sales_invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)

    # علاقات
    product = db.relationship('Product', backref='sales_items')

    def __repr__(self):
        return f'<SalesInvoiceItem {self.product.name}>'

# جدول فواتير الشراء
class PurchaseInvoice(db.Model):
    __tablename__ = 'purchase_invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    discount_percentage = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    remaining_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, paid, partial, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات
    items = db.relationship('PurchaseInvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('PurchaseReturn', backref='original_invoice', lazy=True)

    def __repr__(self):
        return f'<PurchaseInvoice {self.invoice_number}>'

# جدول عناصر فاتورة الشراء
class PurchaseInvoiceItem(db.Model):
    __tablename__ = 'purchase_invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('purchase_invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)

    # علاقات
    product = db.relationship('Product', backref='purchase_items')

    def __repr__(self):
        return f'<PurchaseInvoiceItem {self.product.name}>'

# جدول مرتجعات البيع
class SalesReturn(db.Model):
    __tablename__ = 'sales_returns'

    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_invoice_id = db.Column(db.Integer, db.ForeignKey('sales_invoices.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    total_amount = db.Column(db.Float, default=0.0)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات
    items = db.relationship('SalesReturnItem', backref='return_invoice', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SalesReturn {self.return_number}>'

# جدول عناصر مرتجعات البيع
class SalesReturnItem(db.Model):
    __tablename__ = 'sales_return_items'

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('sales_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # علاقات
    product = db.relationship('Product', backref='sales_return_items')

    def __repr__(self):
        return f'<SalesReturnItem {self.product.name}>'

# جدول مرتجعات الشراء
class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_returns'

    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False)
    original_invoice_id = db.Column(db.Integer, db.ForeignKey('purchase_invoices.id'), nullable=False)
    return_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    total_amount = db.Column(db.Float, default=0.0)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات
    items = db.relationship('PurchaseReturnItem', backref='return_invoice', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PurchaseReturn {self.return_number}>'

# جدول عناصر مرتجعات الشراء
class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_items'

    id = db.Column(db.Integer, primary_key=True)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_returns.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # علاقات
    product = db.relationship('Product', backref='purchase_return_items')

    def __repr__(self):
        return f'<PurchaseReturnItem {self.product.name}>'

# جدول الخزينة
class Treasury(db.Model):
    __tablename__ = 'treasury'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # الخزينة الرئيسية، خزينة الشحن
    current_balance = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات
    transactions = db.relationship('TreasuryTransaction', backref='treasury', lazy=True)

    def __repr__(self):
        return f'<Treasury {self.name}>'

# جدول حركات الخزينة
class TreasuryTransaction(db.Model):
    __tablename__ = 'treasury_transactions'

    id = db.Column(db.Integer, primary_key=True)
    treasury_id = db.Column(db.Integer, db.ForeignKey('treasury.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    reference_type = db.Column(db.String(50))  # sales_invoice, purchase_invoice, sales_return, etc.
    reference_id = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TreasuryTransaction {self.transaction_type}: {self.amount}>'

# جدول حركة المخزون
class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # in, out
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    reference_type = db.Column(db.String(50))  # sales_invoice, purchase_invoice, return, adjustment
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # علاقات
    product = db.relationship('Product', backref='movements')

    def __repr__(self):
        return f'<InventoryMovement {self.product.name}: {self.movement_type} {self.quantity}>'

# جدول النسخ الاحتياطي
class BackupLog(db.Model):
    __tablename__ = 'backup_logs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # بالبايت
    backup_type = db.Column(db.String(20), default='auto')  # auto, manual
    status = db.Column(db.String(20), default='success')  # success, failed
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BackupLog {self.filename}>'

# جدول إعدادات النظام
class SystemSettings(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SystemSettings {self.key}: {self.value}>'
