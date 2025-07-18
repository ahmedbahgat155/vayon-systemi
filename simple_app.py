from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

# إنشاء التطبيق
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vayon-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vayon_simple.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# نموذج المستخدم المبسط
class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    stats = {
        'today_sales_count': 0,
        'today_sales_amount': 0,
        'pending_shipments': 0,
        'delivered_shipments': 0,
        'collection_rate': 0,
        'low_stock_products': 0,
        'main_treasury_balance': 0,
        'shipping_treasury_balance': 0
    }
    return render_template('dashboard.html', stats=stats)

# Routes مؤقتة
@app.route('/profile')
@login_required
def profile():
    return "<h1>صفحة الملف الشخصي - قيد التطوير</h1>"

@app.route('/change-password')
@login_required
def change_password():
    return "<h1>صفحة تغيير كلمة المرور - قيد التطوير</h1>"

@app.route('/sales')
@login_required
def sales_list():
    return "<h1>فواتير البيع - قيد التطوير</h1>"

@app.route('/sales/create')
@login_required
def create_sale():
    return "<h1>إنشاء فاتورة بيع - قيد التطوير</h1>"

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

@app.route('/shipments')
@login_required
def shipments_list():
    return "<h1>تتبع الشحنات - قيد التطوير</h1>"

@app.route('/reports')
@login_required
def reports():
    return "<h1>التقارير - قيد التطوير</h1>"

@app.route('/users')
@login_required
def users_management():
    return "<h1>إدارة المستخدمين - قيد التطوير</h1>"

@app.route('/backup')
@login_required
def backup_management():
    return "<h1>النسخ الاحتياطي - قيد التطوير</h1>"

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("تم إنشاء قاعدة البيانات بنجاح!")
            print("يمكنك الوصول للنظام على: http://localhost:5000")
        except Exception as e:
            print(f"خطأ في إنشاء قاعدة البيانات: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
