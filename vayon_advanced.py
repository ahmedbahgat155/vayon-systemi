import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from advanced_database import *
from datetime import datetime, timedelta
import json
from decimal import Decimal

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vayon-advanced-secret-key-2024')

# إعدادات قاعدة البيانات - PostgreSQL للإنتاج، SQLite للتطوير
if os.environ.get('DATABASE_URL'):
    # إنتاج - Render PostgreSQL
    database_url = os.environ.get('DATABASE_URL')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # تطوير - SQLite محلي
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vayon_advanced.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# دالة مساعدة لتوليد رقم فاتورة
def generate_invoice_number(prefix='INV'):
    from datetime import datetime
    now = datetime.now()
    # تنسيق: INV-2024-001
    year = now.year
    # البحث عن آخر فاتورة في السنة الحالية
    last_invoice = Sale.query.filter(
        Sale.invoice_number.like(f'{prefix}-{year}-%')
    ).order_by(Sale.invoice_number.desc()).first()
    
    if last_invoice:
        # استخراج الرقم التسلسلي
        parts = last_invoice.invoice_number.split('-')
        if len(parts) == 3:
            try:
                last_number = int(parts[2])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
    else:
        new_number = 1
    
    return f'{prefix}-{year}-{new_number:03d}'

# دالة مساعدة لتحديث المخزون
def update_inventory(product_id, quantity_change, movement_type, reference_type=None, reference_id=None, unit_price=None):
    product = Product.query.get(product_id)
    if not product:
        return False
    
    # حفظ الكمية السابقة
    quantity_before = product.current_stock
    
    # تحديث الكمية
    product.current_stock += quantity_change
    quantity_after = product.current_stock
    
    # إنشاء حركة مخزون
    movement = InventoryMovement(
        product_id=product_id,
        user_id=current_user.id,
        movement_type=movement_type,
        reference_type=reference_type,
        reference_id=reference_id,
        quantity_before=quantity_before,
        quantity_change=quantity_change,
        quantity_after=quantity_after,
        unit_price=unit_price
    )
    
    db.session.add(movement)
    return True

# دالة مساعدة لتحديث الخزينة
def update_treasury(treasury_id, amount, transaction_type, reference_type=None, reference_id=None, description=None):
    treasury = Treasury.query.get(treasury_id)
    if not treasury:
        return False
    
    # حفظ الرصيد السابق
    balance_before = treasury.current_balance
    
    # تحديث الرصيد
    if transaction_type == 'إيداع':
        treasury.current_balance += amount
    else:  # سحب
        treasury.current_balance -= amount
    
    balance_after = treasury.current_balance
    
    # إنشاء حركة خزينة
    transaction = TreasuryTransaction(
        treasury_id=treasury_id,
        user_id=current_user.id,
        transaction_type=transaction_type,
        reference_type=reference_type,
        reference_id=reference_id,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        description=description
    )
    
    db.session.add(transaction)
    return True

# الصفحة الرئيسية
@app.route('/')
def index():
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('setup_first_admin'))
    except Exception as e:
        db.create_all()
        return redirect(url_for('setup_first_admin'))
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return redirect(url_for('dashboard'))

# صفحة إعداد أول مدير
@app.route('/setup-first-admin', methods=['GET', 'POST'])
def setup_first_admin():
    try:
        db.create_all()
        admin_exists = User.query.filter_by(role='admin').first()
        if admin_exists:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"خطأ: {e}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من البيانات
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
            # إنشاء المدير
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
            main_treasury = Treasury(
                name='الخزينة الرئيسية',
                description='الخزينة الرئيسية للمتجر',
                current_balance=0
            )
            
            shipping_treasury = Treasury(
                name='خزينة الشحن',
                description='خزينة خاصة بأموال الشحن والتحصيل',
                current_balance=0
            )
            
            db.session.add(main_treasury)
            db.session.add(shipping_treasury)
            
            # إنشاء تصنيف افتراضي
            default_category = Category(
                name='عام',
                description='التصنيف الافتراضي للمنتجات'
            )
            
            db.session.add(default_category)
            db.session.flush()  # للحصول على ID التصنيف

            # إضافة منتجات تجريبية
            sample_products = [
                {
                    'name': 'قميص رجالي كلاسيكي أبيض',
                    'sku': 'SHIRT-001',
                    'barcode': '1234567890123',
                    'selling_price': 250.00,
                    'cost_price': 150.00,
                    'current_stock': 50,
                    'min_stock': 10,
                    'unit': 'قطعة',
                    'brand': 'VAYON',
                    'color': 'أبيض',
                    'size': 'L'
                },
                {
                    'name': 'بنطلون جينز رجالي أزرق',
                    'sku': 'JEANS-001',
                    'barcode': '1234567890124',
                    'selling_price': 350.00,
                    'cost_price': 200.00,
                    'current_stock': 30,
                    'min_stock': 5,
                    'unit': 'قطعة',
                    'brand': 'VAYON',
                    'color': 'أزرق',
                    'size': 'L'
                },
                {
                    'name': 'جاكيت رسمي أسود',
                    'sku': 'JACKET-001',
                    'barcode': '1234567890125',
                    'selling_price': 800.00,
                    'cost_price': 500.00,
                    'current_stock': 15,
                    'min_stock': 3,
                    'unit': 'قطعة',
                    'brand': 'VAYON',
                    'color': 'أسود',
                    'size': 'L'
                },
                {
                    'name': 'حذاء رجالي جلد بني',
                    'sku': 'SHOES-001',
                    'barcode': '1234567890126',
                    'selling_price': 450.00,
                    'cost_price': 280.00,
                    'current_stock': 25,
                    'min_stock': 5,
                    'unit': 'زوج',
                    'brand': 'VAYON',
                    'color': 'بني',
                    'size': '42'
                },
                {
                    'name': 'ربطة عنق حريرية',
                    'sku': 'TIE-001',
                    'barcode': '1234567890127',
                    'selling_price': 120.00,
                    'cost_price': 70.00,
                    'current_stock': 100,
                    'min_stock': 20,
                    'unit': 'قطعة',
                    'brand': 'VAYON',
                    'color': 'أحمر'
                }
            ]

            for product_data in sample_products:
                product = Product(
                    name=product_data['name'],
                    sku=product_data['sku'],
                    barcode=product_data['barcode'],
                    category_id=default_category.id,
                    selling_price=product_data['selling_price'],
                    cost_price=product_data['cost_price'],
                    current_stock=product_data['current_stock'],
                    min_stock=product_data['min_stock'],
                    unit=product_data['unit'],
                    brand=product_data['brand'],
                    color=product_data.get('color'),
                    size=product_data.get('size'),
                    is_active=True
                )
                db.session.add(product)

            # إضافة عملاء تجريبيين
            sample_customers = [
                {
                    'name': 'أحمد محمد علي',
                    'phone': '01012345678',
                    'email': 'ahmed.mohamed@example.com',
                    'address': 'شارع النيل، المعادي',
                    'city': 'المعادي',
                    'governorate': 'القاهرة'
                },
                {
                    'name': 'فاطمة أحمد حسن',
                    'phone': '01098765432',
                    'email': 'fatma.ahmed@example.com',
                    'address': 'شارع الجامعة، الدقي',
                    'city': 'الدقي',
                    'governorate': 'الجيزة'
                },
                {
                    'name': 'محمود سعد إبراهيم',
                    'phone': '01155667788',
                    'address': 'شارع الكورنيش، الإسكندرية',
                    'city': 'الإسكندرية',
                    'governorate': 'الإسكندرية'
                },
                {
                    'name': 'مريم خالد محمد',
                    'phone': '01244556677',
                    'email': 'mariam.khaled@example.com',
                    'address': 'شارع الثورة، المنصورة',
                    'city': 'المنصورة',
                    'governorate': 'الدقهلية'
                },
                {
                    'name': 'عمر حسام الدين',
                    'phone': '01033445566',
                    'address': 'شارع الجيش، الزقازيق',
                    'city': 'الزقازيق',
                    'governorate': 'الشرقية'
                }
            ]

            for customer_data in sample_customers:
                customer = Customer(
                    name=customer_data['name'],
                    phone=customer_data['phone'],
                    email=customer_data.get('email'),
                    address=customer_data['address'],
                    city=customer_data['city'],
                    governorate=customer_data['governorate'],
                    is_active=True
                )
                db.session.add(customer)

            # إضافة شركات الشحن التجريبية
            sample_shipping_companies = [
                {
                    'name': 'أرامكس مصر',
                    'code': 'ARAMEX',
                    'phone': '19033',
                    'email': 'info@aramex.com.eg',
                    'website': 'www.aramex.com',
                    'base_price': 25.00,
                    'price_per_kg': 5.00,
                    'collection_commission': 2.5,
                    'delivery_time': '2-3 أيام عمل',
                    'coverage_areas': 'جميع المحافظات'
                },
                {
                    'name': 'فيدكس مصر',
                    'code': 'FEDEX',
                    'phone': '16333',
                    'email': 'customerservice@fedex.com',
                    'website': 'www.fedex.com/eg',
                    'base_price': 30.00,
                    'price_per_kg': 6.00,
                    'collection_commission': 3.0,
                    'delivery_time': '1-2 أيام عمل',
                    'coverage_areas': 'المدن الرئيسية'
                },
                {
                    'name': 'بوستا مصر',
                    'code': 'POSTA',
                    'phone': '16789',
                    'email': 'info@egyptpost.org',
                    'website': 'www.egyptpost.org',
                    'base_price': 15.00,
                    'price_per_kg': 3.00,
                    'collection_commission': 2.0,
                    'delivery_time': '3-5 أيام عمل',
                    'coverage_areas': 'جميع المحافظات والقرى'
                },
                {
                    'name': 'سبيدي',
                    'code': 'SPEEDY',
                    'phone': '19911',
                    'email': 'info@speedy.com.eg',
                    'website': 'www.speedy.com.eg',
                    'base_price': 20.00,
                    'price_per_kg': 4.00,
                    'collection_commission': 2.0,
                    'delivery_time': '2-4 أيام عمل',
                    'coverage_areas': 'القاهرة الكبرى والإسكندرية'
                },
                {
                    'name': 'إيجل إكسبريس',
                    'code': 'EAGLE',
                    'phone': '19922',
                    'email': 'info@eagle-express.com',
                    'base_price': 18.00,
                    'price_per_kg': 3.50,
                    'collection_commission': 1.5,
                    'delivery_time': '2-3 أيام عمل',
                    'coverage_areas': 'معظم المحافظات'
                }
            ]

            for company_data in sample_shipping_companies:
                company = ShippingCompany(
                    name=company_data['name'],
                    code=company_data['code'],
                    phone=company_data['phone'],
                    email=company_data.get('email'),
                    website=company_data.get('website'),
                    base_price=company_data['base_price'],
                    price_per_kg=company_data['price_per_kg'],
                    collection_commission=company_data['collection_commission'],
                    delivery_time=company_data['delivery_time'],
                    coverage_areas=company_data['coverage_areas'],
                    is_active=True
                )
                db.session.add(company)

            # إضافة إعدادات التحصيل الافتراضية
            collection_settings = CollectionSettings(
                alert_days_before_due=3,
                alert_days_after_due=1,
                auto_create_tasks=True,
                default_task_priority='متوسطة',
                default_due_days=7,
                max_contact_attempts=5,
                follow_up_interval_days=3,
                escalation_enabled=True,
                escalation_days=14,
                escalation_user_id=admin.id
            )
            db.session.add(collection_settings)

            # إضافة مهام تحصيل تجريبية
            sample_collection_tasks = [
                {
                    'customer_name': 'أحمد محمد علي',
                    'title': 'تحصيل مستحقات شهر ديسمبر',
                    'description': 'تحصيل مبلغ 1500 ج.م مستحقات شهر ديسمبر من العميل أحمد محمد علي',
                    'amount_to_collect': 1500.00,
                    'priority': 'عالية',
                    'due_days_ago': 2  # متأخر بيومين
                },
                {
                    'customer_name': 'فاطمة أحمد حسن',
                    'title': 'متابعة دفعة فاتورة رقم INV-2024-001',
                    'description': 'متابعة دفعة متبقية من فاتورة بقيمة 850 ج.م',
                    'amount_to_collect': 850.00,
                    'priority': 'متوسطة',
                    'due_days_ago': 0  # مستحق اليوم
                },
                {
                    'customer_name': 'محمود سعد إبراهيم',
                    'title': 'تحصيل قيمة طلبية نوفمبر',
                    'description': 'تحصيل مبلغ 2200 ج.م قيمة طلبية شهر نوفمبر',
                    'amount_to_collect': 2200.00,
                    'priority': 'عالية',
                    'due_days_ago': 5  # متأخر بـ 5 أيام
                },
                {
                    'customer_name': 'مريم خالد محمد',
                    'title': 'متابعة دفعة أولى',
                    'description': 'متابعة الدفعة الأولى من إجمالي مستحقات 1200 ج.م',
                    'amount_to_collect': 600.00,
                    'priority': 'متوسطة',
                    'due_days_ago': -3  # مستحق بعد 3 أيام
                },
                {
                    'customer_name': 'عمر حسام الدين',
                    'title': 'تحصيل مستحقات أكتوبر',
                    'description': 'تحصيل مبلغ 950 ج.م مستحقات شهر أكتوبر',
                    'amount_to_collect': 950.00,
                    'priority': 'منخفضة',
                    'due_days_ago': -7  # مستحق بعد أسبوع
                }
            ]

            for task_data in sample_collection_tasks:
                # البحث عن العميل
                customer = Customer.query.filter_by(name=task_data['customer_name']).first()
                if customer:
                    # حساب تاريخ الاستحقاق
                    due_date = datetime.utcnow() - timedelta(days=task_data['due_days_ago'])

                    task = CollectionTask(
                        customer_id=customer.id,
                        assigned_user_id=admin.id,
                        created_by_id=admin.id,
                        title=task_data['title'],
                        description=task_data['description'],
                        amount_to_collect=task_data['amount_to_collect'],
                        priority=task_data['priority'],
                        due_date=due_date,
                        status='جديدة' if task_data['due_days_ago'] <= 0 else 'قيد المعالجة',
                        contact_attempts=0 if task_data['due_days_ago'] <= 0 else 2
                    )

                    if task_data['due_days_ago'] > 0:
                        task.last_contact_date = datetime.utcnow() - timedelta(days=1)
                        task.last_contact_result = 'وعد بالدفع'

                    db.session.add(task)

            db.session.commit()
            
            flash('تم إنشاء حساب المدير الأول بنجاح', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            print(f"خطأ في إنشاء المدير: {e}")
    
    return render_template('setup_first_admin.html')

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('setup_first_admin'))
    except Exception as e:
        db.create_all()
        return redirect(url_for('setup_first_admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('اسم المستخدم وكلمة المرور مطلوبان', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

# لوحة التحكم
@app.route('/dashboard')
@login_required
def dashboard():
    # حساب الإحصائيات
    today = datetime.now().date()
    
    # مبيعات اليوم
    today_sales = Sale.query.filter(
        db.func.date(Sale.sale_date) == today
    ).all()
    
    today_sales_count = len(today_sales)
    today_sales_amount = sum([sale.total_amount for sale in today_sales])
    
    # الخزائن
    treasuries = Treasury.query.all()
    main_treasury_balance = 0
    shipping_treasury_balance = 0
    
    for treasury in treasuries:
        if 'رئيسية' in treasury.name:
            main_treasury_balance = treasury.current_balance
        elif 'شحن' in treasury.name:
            shipping_treasury_balance = treasury.current_balance
    
    # المنتجات منخفضة المخزون
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.min_stock,
        Product.min_stock > 0
    ).count()
    
    # نسبة التحصيل (مبسطة)
    total_sales = Sale.query.all()
    if total_sales:
        total_amount = sum([sale.total_amount for sale in total_sales])
        paid_amount = sum([sale.paid_amount for sale in total_sales])
        collection_rate = (paid_amount / total_amount * 100) if total_amount > 0 else 0
    else:
        collection_rate = 0
    
    stats = {
        'today_sales_count': today_sales_count,
        'today_sales_amount': float(today_sales_amount),
        'pending_shipments': 0,  # سيتم تطويرها لاحقاً
        'delivered_shipments': 0,  # سيتم تطويرها لاحقاً
        'collection_rate': round(collection_rate, 1),
        'low_stock_products': low_stock_products,
        'main_treasury_balance': float(main_treasury_balance),
        'shipping_treasury_balance': float(shipping_treasury_balance)
    }
    
    return render_template('dashboard.html', stats=stats)

# ==================== نظام فواتير البيع المتقدم ====================

# قائمة فواتير البيع
@app.route('/sales')
@login_required
def sales_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # البحث والفلترة
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Sale.query

    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                Sale.invoice_number.contains(search),
                Sale.customer.has(Customer.name.contains(search))
            )
        )

    if status_filter:
        query = query.filter(Sale.status == status_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Sale.sale_date) >= date_from_obj)
        except:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Sale.sale_date) <= date_to_obj)
        except:
            pass

    # ترتيب النتائج
    query = query.order_by(Sale.sale_date.desc())

    # تقسيم الصفحات
    sales = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('sales_list.html', sales=sales,
                         search=search, status_filter=status_filter,
                         date_from=date_from, date_to=date_to)

# إنشاء فاتورة بيع جديدة
@app.route('/sales/create', methods=['GET', 'POST'])
@login_required
def create_sale():
    if request.method == 'POST':
        try:
            # استلام البيانات
            data = request.get_json()

            # بيانات العميل
            customer_data = data.get('customer', {})
            customer_id = None

            if customer_data.get('name'):
                # البحث عن العميل أو إنشاء جديد
                customer = Customer.query.filter_by(
                    name=customer_data['name'],
                    phone=customer_data.get('phone', '')
                ).first()

                if not customer:
                    customer = Customer(
                        name=customer_data['name'],
                        phone=customer_data.get('phone', ''),
                        email=customer_data.get('email', ''),
                        address=customer_data.get('address', ''),
                        city=customer_data.get('city', ''),
                        governorate=customer_data.get('governorate', '')
                    )
                    db.session.add(customer)
                    db.session.flush()  # للحصول على ID

                customer_id = customer.id

            # إنشاء الفاتورة
            sale = Sale(
                invoice_number=generate_invoice_number('INV'),
                customer_id=customer_id,
                user_id=current_user.id,
                sale_date=datetime.now(),
                subtotal=Decimal(str(data.get('subtotal', 0))),
                discount_amount=Decimal(str(data.get('discount_amount', 0))),
                discount_percentage=Decimal(str(data.get('discount_percentage', 0))),
                tax_amount=Decimal(str(data.get('tax_amount', 0))),
                tax_percentage=Decimal(str(data.get('tax_percentage', 0))),
                shipping_cost=Decimal(str(data.get('shipping_cost', 0))),
                total_amount=Decimal(str(data.get('total_amount', 0))),
                paid_amount=Decimal(str(data.get('paid_amount', 0))),
                remaining_amount=Decimal(str(data.get('remaining_amount', 0))),
                payment_method=data.get('payment_method', 'نقدي'),
                payment_status=data.get('payment_status', 'مدفوع كاملاً'),
                shipping_address=data.get('shipping_address', ''),
                shipping_city=data.get('shipping_city', ''),
                shipping_governorate=data.get('shipping_governorate', ''),
                shipping_phone=data.get('shipping_phone', ''),
                notes=data.get('notes', ''),
                status='مكتملة'
            )

            db.session.add(sale)
            db.session.flush()  # للحصول على ID

            # إضافة عناصر الفاتورة
            items_data = data.get('items', [])
            for item_data in items_data:
                product = Product.query.get(item_data['product_id'])
                if not product:
                    continue

                quantity = Decimal(str(item_data['quantity']))
                unit_price = Decimal(str(item_data['unit_price']))
                discount_amount = Decimal(str(item_data.get('discount_amount', 0)))
                total_price = (quantity * unit_price) - discount_amount

                # إنشاء عنصر الفاتورة
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_amount=discount_amount,
                    total_price=total_price,
                    notes=item_data.get('notes', '')
                )

                db.session.add(sale_item)

                # تحديث المخزون (خصم الكمية)
                update_inventory(
                    product_id=product.id,
                    quantity_change=-quantity,  # خصم من المخزون
                    movement_type='بيع',
                    reference_type='فاتورة بيع',
                    reference_id=sale.id,
                    unit_price=unit_price
                )

            # تحديث الخزينة (إضافة المبلغ المدفوع)
            if sale.paid_amount > 0:
                main_treasury = Treasury.query.filter(
                    Treasury.name.contains('رئيسية')
                ).first()

                if main_treasury:
                    update_treasury(
                        treasury_id=main_treasury.id,
                        amount=sale.paid_amount,
                        transaction_type='إيداع',
                        reference_type='فاتورة بيع',
                        reference_id=sale.id,
                        description=f'دفعة من فاتورة بيع رقم {sale.invoice_number}'
                    )

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'تم إنشاء الفاتورة بنجاح',
                'invoice_id': sale.id,
                'invoice_number': sale.invoice_number
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'حدث خطأ: {str(e)}'
            }), 400

    # GET request - عرض صفحة إنشاء الفاتورة
    products = Product.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).limit(100).all()

    return render_template('create_sale.html', products=products, customers=customers)

# عرض تفاصيل فاتورة بيع
@app.route('/sales/<sale_id>')
@login_required
def view_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('view_sale.html', sale=sale)



# تعديل فاتورة بيع
@app.route('/sales/<sale_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    if request.method == 'POST':
        # سيتم تطوير التعديل لاحقاً
        flash('سيتم إضافة وظيفة التعديل قريباً', 'info')
        return redirect(url_for('view_sale', sale_id=sale_id))

    products = Product.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).limit(100).all()

    return render_template('edit_sale.html', sale=sale, products=products, customers=customers)

# طباعة فاتورة بيع
@app.route('/sales/<sale_id>/print')
@login_required
def print_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('print_sale.html', sale=sale)

# API للبحث عن المنتجات
@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    products = Product.query.filter(
        db.and_(
            Product.is_active == True,
            db.or_(
                Product.name.contains(query),
                Product.sku.contains(query),
                Product.barcode.contains(query)
            )
        )
    ).limit(20).all()

    result = []
    for product in products:
        result.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'selling_price': float(product.selling_price),
            'current_stock': float(product.current_stock),
            'unit': product.unit
        })

    return jsonify(result)

# API للبحث عن العملاء
@app.route('/api/customers/search')
@login_required
def search_customers():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    customers = Customer.query.filter(
        db.and_(
            Customer.is_active == True,
            db.or_(
                Customer.name.contains(query),
                Customer.phone.contains(query)
            )
        )
    ).limit(20).all()

    result = []
    for customer in customers:
        result.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address,
            'city': customer.city,
            'governorate': customer.governorate
        })

    return jsonify(result)

# ==================== نظام إدارة العملاء المتقدم ====================

# قائمة العملاء
@app.route('/customers')
@login_required
def customers_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # البحث والفلترة
    search = request.args.get('search', '')
    governorate_filter = request.args.get('governorate', '')
    status_filter = request.args.get('status', '')

    query = Customer.query

    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                Customer.name.contains(search),
                Customer.phone.contains(search),
                Customer.email.contains(search)
            )
        )

    if governorate_filter:
        query = query.filter(Customer.governorate == governorate_filter)

    if status_filter == 'active':
        query = query.filter(Customer.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(Customer.is_active == False)

    # ترتيب النتائج
    query = query.order_by(Customer.created_at.desc())

    # تقسيم الصفحات
    customers = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # حساب إحصائيات العملاء
    for customer in customers.items:
        # حساب إجمالي المشتريات
        total_purchases = db.session.query(db.func.sum(Sale.total_amount)).filter(
            Sale.customer_id == customer.id
        ).scalar() or 0

        # حساب المبلغ المدفوع
        total_paid = db.session.query(db.func.sum(Sale.paid_amount)).filter(
            Sale.customer_id == customer.id
        ).scalar() or 0

        # حساب المبلغ المتبقي (الدين)
        total_debt = total_purchases - total_paid

        # عدد الفواتير
        invoices_count = Sale.query.filter(Sale.customer_id == customer.id).count()

        # إضافة البيانات للعميل
        customer.total_purchases = float(total_purchases)
        customer.total_paid = float(total_paid)
        customer.total_debt = float(total_debt)
        customer.invoices_count = invoices_count

    return render_template('customers_list.html', customers=customers,
                         search=search, governorate_filter=governorate_filter,
                         status_filter=status_filter)

# إضافة عميل جديد
@app.route('/customers/create', methods=['GET', 'POST'])
@login_required
def create_customer():
    if request.method == 'POST':
        try:
            # استلام البيانات
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            city = request.form.get('city')
            governorate = request.form.get('governorate')
            notes = request.form.get('notes')

            # التحقق من البيانات المطلوبة
            if not name:
                flash('اسم العميل مطلوب', 'error')
                return render_template('create_customer.html')

            # التحقق من عدم تكرار الهاتف
            if phone:
                existing_customer = Customer.query.filter_by(phone=phone).first()
                if existing_customer:
                    flash('رقم الهاتف مستخدم من قبل عميل آخر', 'error')
                    return render_template('create_customer.html')

            # إنشاء العميل
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                governorate=governorate,
                notes=notes,
                is_active=True
            )

            db.session.add(customer)
            db.session.commit()

            flash('تم إضافة العميل بنجاح', 'success')
            return redirect(url_for('customers_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')

    return render_template('create_customer.html')

# عرض تفاصيل العميل
@app.route('/customers/<customer_id>')
@login_required
def view_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    # حساب الإحصائيات
    total_purchases = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.customer_id == customer.id
    ).scalar() or 0

    total_paid = db.session.query(db.func.sum(Sale.paid_amount)).filter(
        Sale.customer_id == customer.id
    ).scalar() or 0

    total_debt = total_purchases - total_paid

    # آخر الفواتير
    recent_sales = Sale.query.filter(
        Sale.customer_id == customer.id
    ).order_by(Sale.sale_date.desc()).limit(10).all()

    # آخر الدفعات
    recent_payments = CustomerPayment.query.filter(
        CustomerPayment.customer_id == customer.id
    ).order_by(CustomerPayment.payment_date.desc()).limit(10).all()

    stats = {
        'total_purchases': float(total_purchases),
        'total_paid': float(total_paid),
        'total_debt': float(total_debt),
        'invoices_count': len(recent_sales)
    }

    return render_template('view_customer.html', customer=customer, stats=stats,
                         recent_sales=recent_sales, recent_payments=recent_payments)

# تعديل العميل
@app.route('/customers/<customer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        try:
            # استلام البيانات
            customer.name = request.form.get('name')
            customer.phone = request.form.get('phone')
            customer.email = request.form.get('email')
            customer.address = request.form.get('address')
            customer.city = request.form.get('city')
            customer.governorate = request.form.get('governorate')
            customer.notes = request.form.get('notes')
            customer.is_active = request.form.get('is_active') == 'on'

            # التحقق من البيانات المطلوبة
            if not customer.name:
                flash('اسم العميل مطلوب', 'error')
                return render_template('edit_customer.html', customer=customer)

            # التحقق من عدم تكرار الهاتف
            if customer.phone:
                existing_customer = Customer.query.filter(
                    Customer.phone == customer.phone,
                    Customer.id != customer.id
                ).first()
                if existing_customer:
                    flash('رقم الهاتف مستخدم من قبل عميل آخر', 'error')
                    return render_template('edit_customer.html', customer=customer)

            db.session.commit()

            flash('تم تحديث بيانات العميل بنجاح', 'success')
            return redirect(url_for('view_customer', customer_id=customer.id))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')

    return render_template('edit_customer.html', customer=customer)

# إضافة دفعة للعميل
@app.route('/customers/<customer_id>/add-payment', methods=['POST'])
@login_required
def add_customer_payment(customer_id):
    try:
        customer = Customer.query.get_or_404(customer_id)

        # استلام البيانات
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method')
        reference_number = request.form.get('reference_number')
        notes = request.form.get('notes')
        sale_id = request.form.get('sale_id') or None

        if amount <= 0:
            flash('مبلغ الدفعة يجب أن يكون أكبر من صفر', 'error')
            return redirect(url_for('view_customer', customer_id=customer_id))

        # إنشاء الدفعة
        payment = CustomerPayment(
            customer_id=customer.id,
            sale_id=sale_id,
            user_id=current_user.id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            status='مؤكد'
        )

        db.session.add(payment)

        # تحديث الفاتورة إذا كانت محددة
        if sale_id:
            sale = Sale.query.get(sale_id)
            if sale:
                sale.paid_amount += amount
                sale.remaining_amount = sale.total_amount - sale.paid_amount

                # تحديث حالة الدفع
                if sale.remaining_amount <= 0:
                    sale.payment_status = 'مدفوع كاملاً'
                elif sale.paid_amount > 0:
                    sale.payment_status = 'مدفوع جزئياً'

        # تحديث الخزينة الرئيسية
        main_treasury = Treasury.query.filter(
            Treasury.name.contains('رئيسية')
        ).first()

        if main_treasury:
            update_treasury(
                treasury_id=main_treasury.id,
                amount=amount,
                transaction_type='إيداع',
                reference_type='دفعة عميل',
                reference_id=payment.id,
                description=f'دفعة من العميل {customer.name}'
            )

        db.session.commit()

        flash('تم إضافة الدفعة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('view_customer', customer_id=customer_id))

# ==================== نظام الشحن والبواليص المتقدم ====================

# دالة مساعدة لتوليد رقم شحنة
def generate_shipment_number():
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.month

    # البحث عن آخر شحنة في الشهر الحالي
    last_shipment = Shipment.query.filter(
        Shipment.shipment_number.like(f'SH-{year}{month:02d}-%')
    ).order_by(Shipment.shipment_number.desc()).first()

    if last_shipment:
        # استخراج الرقم التسلسلي
        parts = last_shipment.shipment_number.split('-')
        if len(parts) == 3:
            try:
                last_number = int(parts[2])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
    else:
        new_number = 1

    return f'SH-{year}{month:02d}-{new_number:04d}'

# قائمة الشحنات
@app.route('/shipments')
@login_required
def shipments_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # البحث والفلترة
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    company_filter = request.args.get('company', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Shipment.query

    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                Shipment.shipment_number.contains(search),
                Shipment.recipient_name.contains(search),
                Shipment.recipient_phone.contains(search),
                Shipment.tracking_number.contains(search)
            )
        )

    if status_filter:
        query = query.filter(Shipment.status == status_filter)

    if company_filter:
        query = query.filter(Shipment.shipping_company_id == company_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Shipment.created_date) >= date_from_obj)
        except:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Shipment.created_date) <= date_to_obj)
        except:
            pass

    # ترتيب النتائج
    query = query.order_by(Shipment.created_date.desc())

    # تقسيم الصفحات
    shipments = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # شركات الشحن للفلتر
    shipping_companies = ShippingCompany.query.filter_by(is_active=True).all()

    return render_template('shipments_list.html', shipments=shipments,
                         shipping_companies=shipping_companies,
                         search=search, status_filter=status_filter,
                         company_filter=company_filter,
                         date_from=date_from, date_to=date_to)

# إنشاء شحنة جديدة
@app.route('/shipments/create', methods=['GET', 'POST'])
@login_required
def create_shipment():
    if request.method == 'POST':
        try:
            # استلام البيانات
            sale_id = request.form.get('sale_id')
            shipping_company_id = request.form.get('shipping_company_id')
            recipient_name = request.form.get('recipient_name')
            recipient_phone = request.form.get('recipient_phone')
            recipient_address = request.form.get('recipient_address')
            recipient_city = request.form.get('recipient_city')
            recipient_governorate = request.form.get('recipient_governorate')
            weight = float(request.form.get('weight', 0))
            pieces_count = int(request.form.get('pieces_count', 1))
            content_description = request.form.get('content_description')
            cod_amount = float(request.form.get('cod_amount', 0))
            shipping_cost = float(request.form.get('shipping_cost', 0))
            notes = request.form.get('notes')

            # التحقق من البيانات المطلوبة
            if not all([recipient_name, recipient_phone, recipient_address, recipient_city, recipient_governorate]):
                flash('جميع بيانات المرسل إليه مطلوبة', 'error')
                return render_template('create_shipment.html')

            # حساب عمولة التحصيل
            collection_commission = 0
            if cod_amount > 0 and shipping_company_id:
                company = ShippingCompany.query.get(shipping_company_id)
                if company and company.collection_commission > 0:
                    collection_commission = cod_amount * (company.collection_commission / 100)

            # إنشاء الشحنة
            shipment = Shipment(
                shipment_number=generate_shipment_number(),
                sale_id=sale_id if sale_id else None,
                shipping_company_id=shipping_company_id,
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                recipient_address=recipient_address,
                recipient_city=recipient_city,
                recipient_governorate=recipient_governorate,
                weight=weight,
                pieces_count=pieces_count,
                content_description=content_description,
                cod_amount=cod_amount,
                shipping_cost=shipping_cost,
                collection_commission=collection_commission,
                notes=notes,
                status='قيد التحضير'
            )

            db.session.add(shipment)
            db.session.flush()  # للحصول على ID

            # إنشاء أول حالة في التاريخ
            status_history = ShipmentStatusHistory(
                shipment_id=shipment.id,
                user_id=current_user.id,
                old_status=None,
                new_status='قيد التحضير',
                notes='تم إنشاء الشحنة'
            )

            db.session.add(status_history)

            # تحديث حالة الفاتورة إذا كانت مرتبطة
            if sale_id:
                sale = Sale.query.get(sale_id)
                if sale:
                    sale.shipping_status = 'قيد التحضير'

            db.session.commit()

            flash('تم إنشاء الشحنة بنجاح', 'success')
            return redirect(url_for('view_shipment', shipment_id=shipment.id))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')

    # GET request - عرض صفحة إنشاء الشحنة
    shipping_companies = ShippingCompany.query.filter_by(is_active=True).all()

    # الفواتير التي تحتاج شحن
    pending_sales = Sale.query.filter(
        db.or_(
            Sale.shipping_status == 'قيد التحضير',
            Sale.shipping_status == None
        )
    ).order_by(Sale.sale_date.desc()).limit(50).all()

    return render_template('create_shipment.html',
                         shipping_companies=shipping_companies,
                         pending_sales=pending_sales)

# عرض تفاصيل الشحنة
@app.route('/shipments/<shipment_id>')
@login_required
def view_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)

    # تاريخ الحالات
    status_history = ShipmentStatusHistory.query.filter(
        ShipmentStatusHistory.shipment_id == shipment.id
    ).order_by(ShipmentStatusHistory.created_at.desc()).all()

    return render_template('view_shipment.html', shipment=shipment, status_history=status_history)

# تحديث حالة الشحنة
@app.route('/shipments/<shipment_id>/update-status', methods=['POST'])
@login_required
def update_shipment_status(shipment_id):
    try:
        shipment = Shipment.query.get_or_404(shipment_id)

        new_status = request.form.get('status')
        notes = request.form.get('notes')
        tracking_number = request.form.get('tracking_number')

        if not new_status:
            flash('الحالة الجديدة مطلوبة', 'error')
            return redirect(url_for('view_shipment', shipment_id=shipment_id))

        # حفظ الحالة القديمة
        old_status = shipment.status

        # تحديث الشحنة
        shipment.status = new_status
        if tracking_number:
            shipment.tracking_number = tracking_number

        # تحديث التواريخ حسب الحالة
        if new_status == 'تم الاستلام':
            shipment.pickup_date = datetime.utcnow()
        elif new_status == 'تم التسليم':
            shipment.delivery_date = datetime.utcnow()

        # إنشاء سجل في تاريخ الحالات
        status_history = ShipmentStatusHistory(
            shipment_id=shipment.id,
            user_id=current_user.id,
            old_status=old_status,
            new_status=new_status,
            notes=notes
        )

        db.session.add(status_history)

        # تحديث حالة الفاتورة المرتبطة
        if shipment.sale:
            shipment.sale.shipping_status = new_status

        # إذا تم التسليم وهناك مبلغ تحصيل، تحديث الخزينة
        if new_status == 'تم التسليم' and shipment.cod_amount > 0:
            # تحديث حالة التحصيل
            shipment.collection_status = 'تم كاملاً'
            shipment.collected_amount = shipment.cod_amount
            shipment.collection_date = datetime.utcnow()

            # تحديث خزينة الشحن
            shipping_treasury = Treasury.query.filter(
                Treasury.name.contains('شحن')
            ).first()

            if shipping_treasury:
                # إضافة المبلغ المحصل
                update_treasury(
                    treasury_id=shipping_treasury.id,
                    amount=shipment.cod_amount,
                    transaction_type='إيداع',
                    reference_type='تحصيل شحنة',
                    reference_id=shipment.id,
                    description=f'تحصيل شحنة رقم {shipment.shipment_number}'
                )

                # خصم عمولة التحصيل
                if shipment.collection_commission > 0:
                    update_treasury(
                        treasury_id=shipping_treasury.id,
                        amount=shipment.collection_commission,
                        transaction_type='سحب',
                        reference_type='عمولة تحصيل',
                        reference_id=shipment.id,
                        description=f'عمولة تحصيل شحنة رقم {shipment.shipment_number}'
                    )

        db.session.commit()

        flash('تم تحديث حالة الشحنة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('view_shipment', shipment_id=shipment_id))

# ==================== نظام التحصيل والمتابعة المتقدم ====================

# دالة مساعدة لإنشاء مهام التحصيل التلقائية
def create_collection_task_for_sale(sale):
    """إنشاء مهمة تحصيل تلقائية للفاتورة"""
    if sale.remaining_amount <= 0:
        return None

    # التحقق من وجود مهمة سابقة
    existing_task = CollectionTask.query.filter_by(
        sale_id=sale.id,
        status='جديدة'
    ).first()

    if existing_task:
        return existing_task

    # إنشاء مهمة جديدة
    task = CollectionTask(
        customer_id=sale.customer_id,
        sale_id=sale.id,
        assigned_user_id=current_user.id,
        created_by_id=current_user.id,
        title=f'تحصيل فاتورة رقم {sale.invoice_number}',
        description=f'تحصيل مبلغ {sale.remaining_amount} ج.م من العميل {sale.customer.name if sale.customer else "غير محدد"}',
        amount_to_collect=sale.remaining_amount,
        priority='متوسطة' if sale.remaining_amount < 1000 else 'عالية',
        due_date=datetime.utcnow() + timedelta(days=7)
    )

    db.session.add(task)
    return task

# لوحة التحصيل الرئيسية
@app.route('/collections')
@login_required
def collections_dashboard():
    # إحصائيات التحصيل
    today = datetime.now().date()

    # المهام المستحقة اليوم
    due_today = CollectionTask.query.filter(
        db.func.date(CollectionTask.due_date) == today,
        CollectionTask.status.in_(['جديدة', 'قيد المعالجة'])
    ).count()

    # المهام المتأخرة
    overdue = CollectionTask.query.filter(
        CollectionTask.due_date < datetime.utcnow(),
        CollectionTask.status.in_(['جديدة', 'قيد المعالجة'])
    ).count()

    # إجمالي المبالغ المطلوب تحصيلها
    total_to_collect = db.session.query(db.func.sum(CollectionTask.amount_to_collect)).filter(
        CollectionTask.status.in_(['جديدة', 'قيد المعالجة'])
    ).scalar() or 0

    # المبالغ المحصلة هذا الشهر
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    collected_this_month = db.session.query(db.func.sum(CustomerPayment.amount)).filter(
        CustomerPayment.payment_date >= start_of_month
    ).scalar() or 0

    # أحدث المهام
    recent_tasks = CollectionTask.query.filter(
        CollectionTask.assigned_user_id == current_user.id
    ).order_by(CollectionTask.created_at.desc()).limit(10).all()

    # التنبيهات غير المقروءة
    unread_alerts = CollectionAlert.query.filter(
        CollectionAlert.user_id == current_user.id,
        CollectionAlert.is_read == False
    ).count()

    stats = {
        'due_today': due_today,
        'overdue': overdue,
        'total_to_collect': float(total_to_collect),
        'collected_this_month': float(collected_this_month),
        'unread_alerts': unread_alerts
    }

    return render_template('collections_dashboard.html', stats=stats, recent_tasks=recent_tasks)

# قائمة مهام التحصيل
@app.route('/collections/tasks')
@login_required
def collection_tasks_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # البحث والفلترة
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    assigned_filter = request.args.get('assigned', '')
    due_filter = request.args.get('due', '')

    query = CollectionTask.query

    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                CollectionTask.title.contains(search),
                CollectionTask.customer.has(Customer.name.contains(search))
            )
        )

    if status_filter:
        query = query.filter(CollectionTask.status == status_filter)

    if priority_filter:
        query = query.filter(CollectionTask.priority == priority_filter)

    if assigned_filter:
        if assigned_filter == 'me':
            query = query.filter(CollectionTask.assigned_user_id == current_user.id)
        else:
            query = query.filter(CollectionTask.assigned_user_id == assigned_filter)

    if due_filter:
        today = datetime.now().date()
        if due_filter == 'today':
            query = query.filter(db.func.date(CollectionTask.due_date) == today)
        elif due_filter == 'overdue':
            query = query.filter(CollectionTask.due_date < datetime.utcnow())
        elif due_filter == 'week':
            week_end = today + timedelta(days=7)
            query = query.filter(
                db.func.date(CollectionTask.due_date) >= today,
                db.func.date(CollectionTask.due_date) <= week_end
            )

    # ترتيب النتائج
    query = query.order_by(CollectionTask.due_date.asc())

    # تقسيم الصفحات
    tasks = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # قائمة المستخدمين للفلتر
    users = User.query.filter_by(is_active=True).all()

    return render_template('collection_tasks_list.html', tasks=tasks, users=users,
                         search=search, status_filter=status_filter,
                         priority_filter=priority_filter, assigned_filter=assigned_filter,
                         due_filter=due_filter)

# إنشاء مهمة تحصيل جديدة
@app.route('/collections/tasks/create', methods=['GET', 'POST'])
@login_required
def create_collection_task():
    if request.method == 'POST':
        try:
            # استلام البيانات
            customer_id = request.form.get('customer_id')
            sale_id = request.form.get('sale_id') or None
            title = request.form.get('title')
            description = request.form.get('description')
            amount_to_collect = float(request.form.get('amount_to_collect', 0))
            priority = request.form.get('priority')
            assigned_user_id = request.form.get('assigned_user_id')
            due_date_str = request.form.get('due_date')

            # التحقق من البيانات المطلوبة
            if not all([customer_id, title, amount_to_collect, priority, assigned_user_id, due_date_str]):
                flash('جميع الحقول المطلوبة يجب ملؤها', 'error')
                return render_template('create_collection_task.html')

            # تحويل التاريخ
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

            # إنشاء المهمة
            task = CollectionTask(
                customer_id=customer_id,
                sale_id=sale_id,
                assigned_user_id=assigned_user_id,
                created_by_id=current_user.id,
                title=title,
                description=description,
                amount_to_collect=amount_to_collect,
                priority=priority,
                due_date=due_date,
                status='جديدة'
            )

            db.session.add(task)
            db.session.commit()

            flash('تم إنشاء مهمة التحصيل بنجاح', 'success')
            return redirect(url_for('view_collection_task', task_id=task.id))

        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')

    # GET request - عرض صفحة إنشاء المهمة
    customers = Customer.query.filter_by(is_active=True).all()
    users = User.query.filter_by(is_active=True).all()

    # الفواتير غير المدفوعة
    unpaid_sales = Sale.query.filter(Sale.remaining_amount > 0).order_by(Sale.sale_date.desc()).limit(50).all()

    return render_template('create_collection_task.html',
                         customers=customers, users=users, unpaid_sales=unpaid_sales)

# عرض تفاصيل مهمة التحصيل
@app.route('/collections/tasks/<task_id>')
@login_required
def view_collection_task(task_id):
    task = CollectionTask.query.get_or_404(task_id)

    # متابعات المهمة
    follow_ups = CollectionFollowUp.query.filter(
        CollectionFollowUp.task_id == task.id
    ).order_by(CollectionFollowUp.created_at.desc()).all()

    return render_template('view_collection_task.html', task=task, follow_ups=follow_ups)

# إضافة متابعة لمهمة التحصيل
@app.route('/collections/tasks/<task_id>/follow-up', methods=['POST'])
@login_required
def add_collection_follow_up(task_id):
    try:
        task = CollectionTask.query.get_or_404(task_id)

        # استلام البيانات
        contact_type = request.form.get('contact_type')
        contact_result = request.form.get('contact_result')
        description = request.form.get('description')
        promised_payment_date_str = request.form.get('promised_payment_date')
        promised_amount = request.form.get('promised_amount')
        next_follow_up_date_str = request.form.get('next_follow_up_date')
        next_follow_up_notes = request.form.get('next_follow_up_notes')

        if not all([contact_type, contact_result, description]):
            flash('نوع التواصل ونتيجته والوصف مطلوبة', 'error')
            return redirect(url_for('view_collection_task', task_id=task_id))

        # تحويل التواريخ
        promised_payment_date = None
        if promised_payment_date_str:
            promised_payment_date = datetime.strptime(promised_payment_date_str, '%Y-%m-%d')

        next_follow_up_date = None
        if next_follow_up_date_str:
            next_follow_up_date = datetime.strptime(next_follow_up_date_str, '%Y-%m-%d')

        # إنشاء المتابعة
        follow_up = CollectionFollowUp(
            task_id=task.id,
            user_id=current_user.id,
            contact_type=contact_type,
            contact_result=contact_result,
            description=description,
            promised_payment_date=promised_payment_date,
            promised_amount=float(promised_amount) if promised_amount else None,
            next_follow_up_date=next_follow_up_date,
            next_follow_up_notes=next_follow_up_notes
        )

        db.session.add(follow_up)

        # تحديث المهمة
        task.contact_attempts += 1
        task.last_contact_date = datetime.utcnow()
        task.last_contact_result = contact_result

        # تحديث حالة المهمة حسب النتيجة
        if contact_result in ['وعد بالدفع', 'دفع جزئي']:
            task.status = 'قيد المعالجة'
        elif contact_result == 'دفع كامل':
            task.status = 'مكتملة'
            task.completed_date = datetime.utcnow()

        db.session.commit()

        flash('تم إضافة المتابعة بنجاح', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {str(e)}', 'error')

    return redirect(url_for('view_collection_task', task_id=task_id))

# ==================== نظام التقارير المالية الشاملة ====================

# لوحة التقارير المالية
@app.route('/reports')
@login_required
def financial_reports():
    # إحصائيات سريعة
    today = datetime.now().date()
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_year = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # مبيعات الشهر
    monthly_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= start_of_month
    ).scalar() or 0

    # مبيعات السنة
    yearly_sales = db.session.query(db.func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= start_of_year
    ).scalar() or 0

    # المحصل هذا الشهر
    monthly_collected = db.session.query(db.func.sum(CustomerPayment.amount)).filter(
        CustomerPayment.payment_date >= start_of_month
    ).scalar() or 0

    # إجمالي الديون
    total_debt = db.session.query(db.func.sum(Sale.remaining_amount)).filter(
        Sale.remaining_amount > 0
    ).scalar() or 0

    # رصيد الخزائن
    treasuries_balance = db.session.query(db.func.sum(Treasury.current_balance)).scalar() or 0

    # تكاليف الشحن هذا الشهر
    monthly_shipping_costs = db.session.query(db.func.sum(Shipment.shipping_cost)).filter(
        Shipment.created_date >= start_of_month
    ).scalar() or 0

    # مبالغ التحصيل المعلقة
    pending_collections = db.session.query(db.func.sum(CollectionTask.amount_to_collect)).filter(
        CollectionTask.status.in_(['جديدة', 'قيد المعالجة'])
    ).scalar() or 0

    stats = {
        'monthly_sales': float(monthly_sales),
        'yearly_sales': float(yearly_sales),
        'monthly_collected': float(monthly_collected),
        'total_debt': float(total_debt),
        'treasuries_balance': float(treasuries_balance),
        'monthly_shipping_costs': float(monthly_shipping_costs),
        'pending_collections': float(pending_collections)
    }

    return render_template('financial_reports.html', stats=stats)

# تقرير المبيعات التفصيلي
@app.route('/reports/sales')
@login_required
def sales_report():
    # فلاتر التقرير
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    customer_id = request.args.get('customer_id', '')

    # تحديد الفترة الافتراضية (آخر 30 يوم)
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')

    # بناء الاستعلام
    query = Sale.query

    # تطبيق الفلاتر
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()

        query = query.filter(
            db.func.date(Sale.sale_date) >= date_from_obj,
            db.func.date(Sale.sale_date) <= date_to_obj
        )
    except:
        pass

    if customer_id:
        query = query.filter(Sale.customer_id == customer_id)

    # الحصول على البيانات
    sales = query.order_by(Sale.sale_date.desc()).all()

    # حساب الإجماليات
    total_sales = sum([sale.total_amount for sale in sales])
    total_paid = sum([sale.paid_amount for sale in sales])
    total_remaining = sum([sale.remaining_amount for sale in sales])

    # العملاء للفلتر
    customers = Customer.query.filter_by(is_active=True).all()

    report_data = {
        'sales': sales,
        'total_sales': float(total_sales),
        'total_paid': float(total_paid),
        'total_remaining': float(total_remaining),
        'count': len(sales)
    }

    return render_template('sales_report.html',
                         report_data=report_data, customers=customers,
                         date_from=date_from, date_to=date_to, customer_id=customer_id)

# تقرير التحصيل
@app.route('/reports/collections')
@login_required
def collections_report():
    # فلاتر التقرير
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status_filter = request.args.get('status', '')

    # تحديد الفترة الافتراضية (آخر 30 يوم)
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')

    # بناء الاستعلام للمهام
    tasks_query = CollectionTask.query

    # تطبيق الفلاتر
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()

        tasks_query = tasks_query.filter(
            db.func.date(CollectionTask.created_at) >= date_from_obj,
            db.func.date(CollectionTask.created_at) <= date_to_obj
        )
    except:
        pass

    if status_filter:
        tasks_query = tasks_query.filter(CollectionTask.status == status_filter)

    # الحصول على البيانات
    tasks = tasks_query.order_by(CollectionTask.created_at.desc()).all()

    # حساب الإجماليات
    total_to_collect = sum([task.amount_to_collect for task in tasks])
    completed_tasks = [task for task in tasks if task.status == 'مكتملة']
    total_collected = sum([task.amount_to_collect for task in completed_tasks])

    # معدل النجاح
    success_rate = (len(completed_tasks) / len(tasks) * 100) if tasks else 0

    # الدفعات في نفس الفترة
    payments_query = CustomerPayment.query
    try:
        payments_query = payments_query.filter(
            db.func.date(CustomerPayment.payment_date) >= date_from_obj,
            db.func.date(CustomerPayment.payment_date) <= date_to_obj
        )
    except:
        pass

    payments = payments_query.order_by(CustomerPayment.payment_date.desc()).all()
    total_payments = sum([payment.amount for payment in payments])

    report_data = {
        'tasks': tasks,
        'payments': payments,
        'total_to_collect': float(total_to_collect),
        'total_collected': float(total_collected),
        'total_payments': float(total_payments),
        'success_rate': round(success_rate, 1),
        'tasks_count': len(tasks),
        'payments_count': len(payments)
    }

    return render_template('collections_report.html',
                         report_data=report_data,
                         date_from=date_from, date_to=date_to, status_filter=status_filter)

# تقرير الخزينة
@app.route('/reports/treasury')
@login_required
def treasury_report():
    # فلاتر التقرير
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    treasury_id = request.args.get('treasury_id', '')

    # تحديد الفترة الافتراضية (آخر 30 يوم)
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')

    # بناء الاستعلام
    query = TreasuryTransaction.query

    # تطبيق الفلاتر
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()

        query = query.filter(
            db.func.date(TreasuryTransaction.created_at) >= date_from_obj,
            db.func.date(TreasuryTransaction.created_at) <= date_to_obj
        )
    except:
        pass

    if treasury_id:
        query = query.filter(TreasuryTransaction.treasury_id == treasury_id)

    # الحصول على البيانات
    transactions = query.order_by(TreasuryTransaction.created_at.desc()).all()

    # حساب الإجماليات
    total_deposits = sum([t.amount for t in transactions if t.transaction_type == 'إيداع'])
    total_withdrawals = sum([t.amount for t in transactions if t.transaction_type == 'سحب'])
    net_change = total_deposits - total_withdrawals

    # الخزائن للفلتر
    treasuries = Treasury.query.filter_by(is_active=True).all()

    # الأرصدة الحالية
    current_balances = {}
    for treasury in treasuries:
        current_balances[treasury.id] = float(treasury.current_balance)

    report_data = {
        'transactions': transactions,
        'total_deposits': float(total_deposits),
        'total_withdrawals': float(total_withdrawals),
        'net_change': float(net_change),
        'transactions_count': len(transactions),
        'current_balances': current_balances
    }

    return render_template('treasury_report.html',
                         report_data=report_data, treasuries=treasuries,
                         date_from=date_from, date_to=date_to, treasury_id=treasury_id)

# ==================== Routes مؤقتة ====================

@app.route('/profile')
@login_required
def profile():
    return "<h1>صفحة الملف الشخصي - قيد التطوير</h1>"

@app.route('/change-password')
@login_required
def change_password():
    return "<h1>صفحة تغيير كلمة المرور - قيد التطوير</h1>"

@app.route('/purchases')
@login_required
def purchases_list():
    return "<h1>فواتير الشراء - قيد التطوير</h1>"

@app.route('/purchases/create')
@login_required
def create_purchase():
    return "<h1>إنشاء فاتورة شراء - قيد التطوير</h1>"

@app.route('/products')
@login_required
def products_list():
    return "<h1>إدارة المنتجات - قيد التطوير</h1>"

@app.route('/inventory')
@login_required
def inventory_movements():
    return "<h1>حركة المخزون - قيد التطوير</h1>"

@app.route('/treasury')
@login_required
def treasury():
    return "<h1>الخزينة - قيد التطوير</h1>"





@app.route('/users')
@login_required
def users_management():
    return "<h1>إدارة المستخدمين - قيد التطوير</h1>"

@app.route('/backup')
@login_required
def backup_management():
    return "<h1>النسخ الاحتياطي - قيد التطوير</h1>"

# تهيئة قاعدة البيانات
with app.app_context():
    try:
        db.create_all()
        print("🎉 تم إنشاء قاعدة البيانات المتقدمة بنجاح!")
        print("💎 نظام VAYON المتقدم جاهز للعمل")
        if os.environ.get('DATABASE_URL'):
            print("🌐 النظام يعمل على Render")
        else:
            print("🌐 يمكنك الوصول للنظام على: http://localhost:5000")
        print("💰 العملة: الجنيه المصري (ج.م)")
        print("🚀 المميزات: فواتير بيع متقدمة، إدارة مخزون، خزائن متعددة")
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not os.environ.get('DATABASE_URL')  # Debug فقط في التطوير
    app.run(debug=debug, host='0.0.0.0', port=port)
