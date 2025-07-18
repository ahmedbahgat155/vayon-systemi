from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

def init_models(db):
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
        
        def __repr__(self):
            return f'<Supplier {self.name}>'

    # جدول فئات المنتجات
    class ProductCategory(db.Model):
        __tablename__ = 'product_categories'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        description = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
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

    # جدول الخزينة
    class Treasury(db.Model):
        __tablename__ = 'treasury'
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)  # الخزينة الرئيسية، خزينة الشحن
        current_balance = db.Column(db.Float, default=0.0)
        description = db.Column(db.Text)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        
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
        
        def __repr__(self):
            return f'<SalesInvoiceItem {self.id}>'

    # إضافة النماذج الأخرى بنفس الطريقة...
    # (سأضيف باقي النماذج في الجزء التالي)
    
    return {
        'User': User,
        'Customer': Customer,
        'Supplier': Supplier,
        'ProductCategory': ProductCategory,
        'Product': Product,
        'Treasury': Treasury,
        'TreasuryTransaction': TreasuryTransaction,
        'SalesInvoice': SalesInvoice,
        'SalesInvoiceItem': SalesInvoiceItem
    }
