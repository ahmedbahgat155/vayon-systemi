from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

# دالة لتوليد UUID
def generate_uuid():
    return str(uuid.uuid4())

# نموذج المستخدمين
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# نموذج العملاء
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    governorate = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    sales = db.relationship('Sale', backref='customer', lazy=True)

# نموذج الموردين
class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    payment_terms = db.Column(db.String(100))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)

# نموذج تصنيفات المنتجات
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy=True)

# نموذج المنتجات المحسن
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True)  # رمز المنتج
    barcode = db.Column(db.String(50), unique=True)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    
    # الأسعار
    cost_price = db.Column(db.Numeric(10, 2), default=0)  # سعر التكلفة
    selling_price = db.Column(db.Numeric(10, 2), nullable=False)  # سعر البيع
    wholesale_price = db.Column(db.Numeric(10, 2))  # سعر الجملة
    
    # المخزون
    current_stock = db.Column(db.Numeric(10, 3), default=0)  # الكمية الحالية (عشرية)
    min_stock = db.Column(db.Numeric(10, 3), default=0)  # الحد الأدنى
    max_stock = db.Column(db.Numeric(10, 3), default=0)  # الحد الأقصى
    
    # الوحدات
    unit = db.Column(db.String(20), default='قطعة')  # الوحدة الأساسية
    
    # معلومات إضافية
    brand = db.Column(db.String(100))  # الماركة
    model = db.Column(db.String(100))  # الموديل
    color = db.Column(db.String(50))   # اللون
    size = db.Column(db.String(50))    # المقاس
    weight = db.Column(db.Numeric(8, 3))  # الوزن
    
    # الصور
    image_url = db.Column(db.String(255))
    
    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    is_service = db.Column(db.Boolean, default=False)  # هل هو خدمة أم منتج
    
    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)
    purchase_items = db.relationship('PurchaseItem', backref='product', lazy=True)
    inventory_movements = db.relationship('InventoryMovement', backref='product', lazy=True)

# نموذج فواتير البيع المحسن
class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # التواريخ
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    
    # المبالغ
    subtotal = db.Column(db.Numeric(12, 2), default=0)  # المجموع الفرعي
    discount_amount = db.Column(db.Numeric(10, 2), default=0)  # قيمة الخصم
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)  # نسبة الخصم
    tax_amount = db.Column(db.Numeric(10, 2), default=0)  # قيمة الضريبة
    tax_percentage = db.Column(db.Numeric(5, 2), default=0)  # نسبة الضريبة
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)  # تكلفة الشحن
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)  # المجموع النهائي
    paid_amount = db.Column(db.Numeric(12, 2), default=0)  # المبلغ المدفوع
    remaining_amount = db.Column(db.Numeric(12, 2), default=0)  # المبلغ المتبقي
    
    # معلومات الدفع
    payment_method = db.Column(db.String(50), default='نقدي')  # طريقة الدفع
    payment_status = db.Column(db.String(20), default='مدفوع جزئياً')  # حالة الدفع
    
    # معلومات الشحن
    shipping_address = db.Column(db.Text)
    shipping_city = db.Column(db.String(50))
    shipping_governorate = db.Column(db.String(50))
    shipping_phone = db.Column(db.String(20))
    shipping_status = db.Column(db.String(20), default='قيد التحضير')
    tracking_number = db.Column(db.String(100))
    
    # ملاحظات
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # ملاحظات داخلية
    
    # الحالة
    status = db.Column(db.String(20), default='مكتملة')  # حالة الفاتورة
    is_returned = db.Column(db.Boolean, default=False)
    
    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='sales')

# نموذج عناصر فاتورة البيع
class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    
    # الكميات والأسعار
    quantity = db.Column(db.Numeric(10, 3), nullable=False)  # الكمية (عشرية)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # سعر الوحدة
    discount_amount = db.Column(db.Numeric(10, 2), default=0)  # خصم العنصر
    total_price = db.Column(db.Numeric(12, 2), nullable=False)  # المجموع
    
    # معلومات إضافية
    notes = db.Column(db.Text)  # ملاحظات على العنصر
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج فواتير الشراء
class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.String(36), db.ForeignKey('suppliers.id'))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # التواريخ
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)

    # المبالغ
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    remaining_amount = db.Column(db.Numeric(12, 2), default=0)

    # معلومات الدفع
    payment_method = db.Column(db.String(50), default='نقدي')
    payment_status = db.Column(db.String(20), default='مدفوع جزئياً')

    # ملاحظات
    notes = db.Column(db.Text)

    # الحالة
    status = db.Column(db.String(20), default='مكتملة')
    is_returned = db.Column(db.Boolean, default=False)

    # التواريخ
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='purchases')

# نموذج عناصر فاتورة الشراء
class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    purchase_id = db.Column(db.String(36), db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)

    # الكميات والأسعار
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False)

    # معلومات إضافية
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج حركة المخزون
class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # نوع الحركة
    movement_type = db.Column(db.String(20), nullable=False)  # بيع، شراء، تسوية، إرجاع
    reference_type = db.Column(db.String(20))  # نوع المرجع (فاتورة بيع، فاتورة شراء، إلخ)
    reference_id = db.Column(db.String(36))  # معرف المرجع

    # الكميات
    quantity_before = db.Column(db.Numeric(10, 3), nullable=False)  # الكمية قبل الحركة
    quantity_change = db.Column(db.Numeric(10, 3), nullable=False)  # التغيير في الكمية
    quantity_after = db.Column(db.Numeric(10, 3), nullable=False)   # الكمية بعد الحركة

    # معلومات إضافية
    unit_price = db.Column(db.Numeric(10, 2))  # سعر الوحدة وقت الحركة
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='inventory_movements')

# نموذج الخزينة
class Treasury(db.Model):
    __tablename__ = 'treasury'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_balance = db.Column(db.Numeric(15, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    transactions = db.relationship('TreasuryTransaction', backref='treasury', lazy=True)

# نموذج حركات الخزينة
class TreasuryTransaction(db.Model):
    __tablename__ = 'treasury_transactions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    treasury_id = db.Column(db.String(36), db.ForeignKey('treasury.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # نوع المعاملة
    transaction_type = db.Column(db.String(20), nullable=False)  # إيداع، سحب
    reference_type = db.Column(db.String(20))  # نوع المرجع
    reference_id = db.Column(db.String(36))   # معرف المرجع

    # المبالغ
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(15, 2), nullable=False)
    balance_after = db.Column(db.Numeric(15, 2), nullable=False)

    # معلومات إضافية
    description = db.Column(db.Text)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='treasury_transactions')

# نموذج عناوين العملاء المتعددة
class CustomerAddress(db.Model):
    __tablename__ = 'customer_addresses'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)

    # نوع العنوان
    address_type = db.Column(db.String(20), default='رئيسي')  # رئيسي، شحن، فوترة، عمل

    # تفاصيل العنوان
    address_line1 = db.Column(db.String(200), nullable=False)
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(50), nullable=False)
    governorate = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10))

    # معلومات الاتصال
    phone = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))

    # الحالة
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    customer = db.relationship('Customer', backref='addresses')

# نموذج شركات الشحن
class ShippingCompany(db.Model):
    __tablename__ = 'shipping_companies'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)  # كود الشركة

    # معلومات الاتصال
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    contact_person = db.Column(db.String(100))

    # الأسعار والخدمات
    base_price = db.Column(db.Numeric(10, 2), default=0)  # السعر الأساسي
    price_per_kg = db.Column(db.Numeric(8, 2), default=0)  # السعر لكل كيلو
    collection_commission = db.Column(db.Numeric(5, 2), default=0)  # عمولة التحصيل %

    # معلومات إضافية
    delivery_time = db.Column(db.String(50))  # مدة التسليم
    coverage_areas = db.Column(db.Text)  # المناطق المغطاة
    notes = db.Column(db.Text)

    # الحالة
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    shipments = db.relationship('Shipment', backref='shipping_company', lazy=True)

# نموذج الشحنات المتقدم
class Shipment(db.Model):
    __tablename__ = 'shipments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_number = db.Column(db.String(50), unique=True, nullable=False)

    # ربط بالفاتورة
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'))

    # شركة الشحن
    shipping_company_id = db.Column(db.String(36), db.ForeignKey('shipping_companies.id'))

    # معلومات المرسل إليه
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_phone = db.Column(db.String(20), nullable=False)
    recipient_address = db.Column(db.Text, nullable=False)
    recipient_city = db.Column(db.String(50), nullable=False)
    recipient_governorate = db.Column(db.String(50), nullable=False)

    # تفاصيل الشحنة
    weight = db.Column(db.Numeric(8, 3))  # الوزن بالكيلو
    pieces_count = db.Column(db.Integer, default=1)  # عدد القطع
    content_description = db.Column(db.Text)  # وصف المحتوى

    # المبالغ
    cod_amount = db.Column(db.Numeric(12, 2), default=0)  # مبلغ التحصيل
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False)  # تكلفة الشحن
    collection_commission = db.Column(db.Numeric(10, 2), default=0)  # عمولة التحصيل

    # التواريخ
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    pickup_date = db.Column(db.DateTime)  # تاريخ الاستلام
    delivery_date = db.Column(db.DateTime)  # تاريخ التسليم
    expected_delivery = db.Column(db.DateTime)  # التسليم المتوقع

    # الحالة
    status = db.Column(db.String(30), default='قيد التحضير')
    # قيد التحضير، جاهز للاستلام، تم الاستلام، في الطريق، تم التسليم، مرتجع، ملغي

    # رقم التتبع من شركة الشحن
    tracking_number = db.Column(db.String(100))

    # ملاحظات
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)

    # معلومات التحصيل
    collection_status = db.Column(db.String(20), default='لم يتم')  # لم يتم، تم جزئياً، تم كاملاً
    collected_amount = db.Column(db.Numeric(12, 2), default=0)  # المبلغ المحصل
    collection_date = db.Column(db.DateTime)  # تاريخ التحصيل

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    sale = db.relationship('Sale', backref='shipments')
    status_history = db.relationship('ShipmentStatusHistory', backref='shipment', lazy=True, cascade='all, delete-orphan')

# نموذج تاريخ حالات الشحنة
class ShipmentStatusHistory(db.Model):
    __tablename__ = 'shipment_status_history'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_id = db.Column(db.String(36), db.ForeignKey('shipments.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # الحالة
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)

    # ملاحظات
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='shipment_status_changes')

# نموذج دفعات العملاء
class CustomerPayment(db.Model):
    __tablename__ = 'customer_payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'))  # اختياري - قد تكون دفعة عامة
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # تفاصيل الدفعة
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    reference_number = db.Column(db.String(100))  # رقم المرجع (شيك، تحويل، إلخ)

    # التواريخ
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)  # للشيكات الآجلة

    # الحالة
    status = db.Column(db.String(20), default='مؤكد')  # مؤكد، معلق، مرتجع

    # ملاحظات
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    customer = db.relationship('Customer', backref='payments')
    sale = db.relationship('Sale', backref='payments')
    user = db.relationship('User', backref='customer_payments')

# نموذج مهام التحصيل
class CollectionTask(db.Model):
    __tablename__ = 'collection_tasks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'))  # اختياري
    assigned_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_by_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # تفاصيل المهمة
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount_to_collect = db.Column(db.Numeric(12, 2), nullable=False)

    # الأولوية والحالة
    priority = db.Column(db.String(20), default='متوسطة')  # عالية، متوسطة، منخفضة
    status = db.Column(db.String(20), default='جديدة')  # جديدة، قيد المعالجة، مكتملة، ملغية، مؤجلة

    # التواريخ
    due_date = db.Column(db.DateTime, nullable=False)  # تاريخ الاستحقاق
    completed_date = db.Column(db.DateTime)  # تاريخ الإنجاز

    # نتائج المتابعة
    contact_attempts = db.Column(db.Integer, default=0)  # عدد محاولات التواصل
    last_contact_date = db.Column(db.DateTime)  # آخر تواصل
    last_contact_result = db.Column(db.String(100))  # نتيجة آخر تواصل

    # ملاحظات
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)  # ملاحظات داخلية

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    customer = db.relationship('Customer', backref='collection_tasks')
    sale = db.relationship('Sale', backref='collection_tasks')
    assigned_user = db.relationship('User', foreign_keys=[assigned_user_id], backref='assigned_collection_tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_collection_tasks')
    follow_ups = db.relationship('CollectionFollowUp', backref='task', lazy=True, cascade='all, delete-orphan')

# نموذج متابعات التحصيل
class CollectionFollowUp(db.Model):
    __tablename__ = 'collection_follow_ups'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = db.Column(db.String(36), db.ForeignKey('collection_tasks.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # نوع المتابعة
    contact_type = db.Column(db.String(30), nullable=False)  # مكالمة، رسالة، زيارة، واتساب، إيميل
    contact_result = db.Column(db.String(50), nullable=False)  # تم الرد، لم يرد، وعد بالدفع، رفض، إلخ

    # تفاصيل المتابعة
    description = db.Column(db.Text, nullable=False)
    promised_payment_date = db.Column(db.DateTime)  # تاريخ الوعد بالدفع
    promised_amount = db.Column(db.Numeric(12, 2))  # المبلغ الموعود

    # المتابعة التالية
    next_follow_up_date = db.Column(db.DateTime)
    next_follow_up_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='collection_follow_ups')

# نموذج تنبيهات التحصيل
class CollectionAlert(db.Model):
    __tablename__ = 'collection_alerts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(36), db.ForeignKey('collection_tasks.id'))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))

    # نوع التنبيه
    alert_type = db.Column(db.String(30), nullable=False)  # استحقاق، تأخير، وعد_دفع، متابعة_مطلوبة

    # محتوى التنبيه
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # الحالة
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)

    # الأولوية
    priority = db.Column(db.String(20), default='متوسطة')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    # العلاقات
    user = db.relationship('User', backref='collection_alerts')
    task = db.relationship('CollectionTask', backref='alerts')
    customer = db.relationship('Customer', backref='alerts')

# نموذج إعدادات التحصيل
class CollectionSettings(db.Model):
    __tablename__ = 'collection_settings'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # إعدادات التنبيهات
    alert_days_before_due = db.Column(db.Integer, default=3)  # تنبيه قبل الاستحقاق بكم يوم
    alert_days_after_due = db.Column(db.Integer, default=1)   # تنبيه بعد التأخير بكم يوم

    # إعدادات المهام التلقائية
    auto_create_tasks = db.Column(db.Boolean, default=True)  # إنشاء مهام تلقائية
    default_task_priority = db.Column(db.String(20), default='متوسطة')
    default_due_days = db.Column(db.Integer, default=7)  # مدة الاستحقاق الافتراضية

    # إعدادات المتابعة
    max_contact_attempts = db.Column(db.Integer, default=5)  # أقصى عدد محاولات
    follow_up_interval_days = db.Column(db.Integer, default=3)  # فترة المتابعة بالأيام

    # إعدادات التصعيد
    escalation_enabled = db.Column(db.Boolean, default=True)
    escalation_days = db.Column(db.Integer, default=14)  # تصعيد بعد كم يوم
    escalation_user_id = db.Column(db.String(36), db.ForeignKey('users.id'))  # المستخدم للتصعيد

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    escalation_user = db.relationship('User', backref='collection_settings')

# نموذج تقارير التحصيل
class CollectionReport(db.Model):
    __tablename__ = 'collection_reports'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # نوع التقرير
    report_type = db.Column(db.String(30), nullable=False)  # يومي، أسبوعي، شهري، مخصص

    # فترة التقرير
    date_from = db.Column(db.DateTime, nullable=False)
    date_to = db.Column(db.DateTime, nullable=False)

    # بيانات التقرير (JSON)
    report_data = db.Column(db.Text)  # JSON data

    # الحالة
    status = db.Column(db.String(20), default='مكتمل')  # قيد الإنشاء، مكتمل، خطأ

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # العلاقات
    user = db.relationship('User', backref='collection_reports')
