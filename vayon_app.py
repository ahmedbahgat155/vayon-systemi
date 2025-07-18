from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
from database import *

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vayon-secret-key-2024-fashion-brand'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vayon_complete.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# دالة مساعدة لتسجيل العمليات
def log_action(action, table_name=None, record_id=None, old_values=None, new_values=None):
    if current_user.is_authenticated:
        log = Log(
            user_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log)

# دالة مساعدة للتحقق من الصلاحيات
def check_permission(permission_name):
    if not current_user.is_authenticated:
        return False
    
    if current_user.role == 'admin':
        return True
    
    user_permissions = Permission.query.filter_by(user_id=current_user.id).first()
    if not user_permissions:
        return False
    
    return getattr(user_permissions, permission_name, False)

# الصفحة الرئيسية
@app.route('/')
def index():
    # التحقق من وجود مدير في النظام
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('setup_first_admin'))
    except Exception as e:
        # إذا لم تكن الجداول موجودة، أنشئها
        db.create_all()
        return redirect(url_for('setup_first_admin'))
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return redirect(url_for('dashboard'))

# صفحة إعداد أول مدير
@app.route('/setup-first-admin', methods=['GET', 'POST'])
def setup_first_admin():
    # التأكد من إنشاء الجداول
    try:
        db.create_all()
    except Exception as e:
        print(f"خطأ في إنشاء الجداول: {e}")
    
    # التحقق من عدم وجود مدير بالفعل
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if admin_exists:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"خطأ في البحث عن المدير: {e}")
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # التحقق من صحة البيانات
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
            # إنشاء المدير الأول
            admin = User(
                username=username,
                email=email,
                full_name=full_name,
                role='admin',
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            
            # إنشاء صلاحيات المدير (جميع الصلاحيات)
            admin_permissions = Permission(
                user_id=admin.id,
                can_view_sales=True,
                can_create_sales=True,
                can_edit_sales=True,
                can_delete_sales=True,
                can_view_purchases=True,
                can_create_purchases=True,
                can_edit_purchases=True,
                can_delete_purchases=True,
                can_view_returns=True,
                can_create_returns=True,
                can_edit_returns=True,
                can_delete_returns=True,
                can_view_inventory=True,
                can_edit_inventory=True,
                can_delete_inventory=True,
                can_view_treasury=True,
                can_edit_treasury=True,
                can_view_shipments=True,
                can_edit_shipments=True,
                can_view_reports=True,
                can_view_profit_reports=True,
                can_manage_users=True,
                can_manage_permissions=True,
                can_backup=True,
                created_by=admin.id
            )
            db.session.add(admin_permissions)
            
            # إنشاء الخزائن الافتراضية
            main_treasury = Treasury(
                name='الخزينة الرئيسية',
                treasury_type='main',
                current_balance=0.0,
                description='الخزينة الرئيسية للشركة'
            )
            
            shipping_treasury = Treasury(
                name='خزينة شركة الشحن',
                treasury_type='shipping',
                current_balance=0.0,
                description='خزينة خاصة بأموال شركة الشحن'
            )
            
            db.session.add(main_treasury)
            db.session.add(shipping_treasury)
            
            db.session.commit()
            
            flash('تم إنشاء حساب المدير الأول بنجاح', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'error')
            return render_template('setup_first_admin.html')
    
    return render_template('setup_first_admin.html')

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # التحقق من وجود مدير في النظام
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
        remember = bool(request.form.get('remember'))
        
        if not username or not password:
            flash('اسم المستخدم وكلمة المرور مطلوبان', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # تسجيل عملية تسجيل الدخول
            log_action('login')
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('login.html')

# صفحة تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    log_action('logout')
    db.session.commit()
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

# لوحة التحكم الرئيسية
@app.route('/dashboard')
@login_required
def dashboard():
    # جمع الإحصائيات
    try:
        # إحصائيات اليوم
        today = datetime.utcnow().date()
        
        # مبيعات اليوم
        today_sales = Sale.query.filter(Sale.invoice_date == today).all()
        today_sales_count = len(today_sales)
        today_sales_amount = sum(sale.total_amount for sale in today_sales)
        
        # الشحنات
        pending_shipments = Shipment.query.filter_by(shipping_status='pending').count()
        delivered_shipments = Shipment.query.filter_by(shipping_status='delivered').count()
        
        # نسبة التحصيل
        collected_shipments = Shipment.query.filter_by(collection_status='collected').count()
        total_shipments = Shipment.query.count()
        collection_rate = (collected_shipments / total_shipments * 100) if total_shipments > 0 else 0
        
        # المخزون المنخفض
        low_stock_products = Product.query.filter(Product.current_stock <= Product.min_stock_level).count()
        
        # رصيد الخزائن
        main_treasury = Treasury.query.filter_by(treasury_type='main').first()
        shipping_treasury = Treasury.query.filter_by(treasury_type='shipping').first()
        
        stats = {
            'today_sales_count': today_sales_count,
            'today_sales_amount': today_sales_amount,
            'pending_shipments': pending_shipments,
            'delivered_shipments': delivered_shipments,
            'collection_rate': round(collection_rate, 1),
            'low_stock_products': low_stock_products,
            'main_treasury_balance': main_treasury.current_balance if main_treasury else 0,
            'shipping_treasury_balance': shipping_treasury.current_balance if shipping_treasury else 0
        }
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        flash(f'خطأ في تحميل البيانات: {str(e)}', 'error')
        return render_template('dashboard.html', stats={})

# Routes مؤقتة للصفحات
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/change-password')
@login_required
def change_password():
    return render_template('change_password.html')

@app.route('/sales')
@login_required
def sales_list():
    return render_template('sales_list.html')

@app.route('/sales/create')
@login_required
def create_sale():
    return render_template('create_sale.html')

@app.route('/sales-returns')
@login_required
def sales_returns_list():
    return render_template('sales_returns_list.html')

@app.route('/purchases')
@login_required
def purchases_list():
    return render_template('purchases_list.html')

@app.route('/purchases/create')
@login_required
def create_purchase():
    return render_template('create_purchase.html')

@app.route('/purchase-returns')
@login_required
def purchase_returns_list():
    return render_template('purchase_returns_list.html')

@app.route('/products')
@login_required
def products_list():
    return render_template('products_list.html')

@app.route('/inventory')
@login_required
def inventory_movements():
    return render_template('inventory_movements.html')

@app.route('/treasury')
@login_required
def treasury():
    return render_template('treasury.html')

@app.route('/shipments')
@login_required
def shipments_list():
    return render_template('shipments_list.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/users')
@login_required
def users_management():
    return render_template('users_management.html')

@app.route('/backup')
@login_required
def backup_management():
    return render_template('backup_management.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("تم إنشاء قاعدة البيانات بنجاح!")
        print("يمكنك الآن الوصول للنظام على: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
