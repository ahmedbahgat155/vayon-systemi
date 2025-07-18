from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, TextAreaField, DateField, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import os
import shutil
import json
from config import config

# إنشاء التطبيق
app = Flask(__name__)
app.config.from_object(config['development'])

# إعداد قاعدة البيانات
db = SQLAlchemy(app)

# استيراد وتهيئة النماذج
from models_new import init_models
models_dict = init_models(db)

# استخراج النماذج
User = models_dict['User']
Customer = models_dict['Customer']
Supplier = models_dict['Supplier']
ProductCategory = models_dict['ProductCategory']
Product = models_dict['Product']
Treasury = models_dict['Treasury']
TreasuryTransaction = models_dict['TreasuryTransaction']
SalesInvoice = models_dict['SalesInvoice']
SalesInvoiceItem = models_dict['SalesInvoiceItem']

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# إنشاء المجلدات المطلوبة
config['development'].init_app(app)

# استيراد النماذج
from forms import LoginForm, FirstAdminForm, UserForm, ChangePasswordForm

# Routes المصادقة
@app.route('/')
def index():
    # التحقق من وجود مدير في النظام أولاً
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('first_admin'))
    except Exception as e:
        # إذا لم تكن الجداول موجودة، أنشئها وانتقل لصفحة المدير الأول
        db.create_all()
        return redirect(url_for('first_admin'))

    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    # التحقق من وجود مدير في النظام
    try:
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            return redirect(url_for('first_admin'))
    except Exception as e:
        # إذا لم تكن الجداول موجودة، أنشئها وانتقل لصفحة المدير الأول
        db.create_all()
        return redirect(url_for('first_admin'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()

            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')

    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/first-admin', methods=['GET', 'POST'])
def first_admin():
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

    form = FirstAdminForm()
    if form.validate_on_submit():
        # إنشاء المدير الأول
        admin = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role='admin',
            is_active=True,
            # منح جميع الصلاحيات للمدير الأول
            can_view_inventory=True,
            can_edit_inventory=True,
            can_delete_inventory=True,
            can_view_invoices=True,
            can_edit_invoices=True,
            can_delete_invoices=True,
            can_view_returns=True,
            can_edit_returns=True,
            can_delete_returns=True,
            can_view_treasury=True,
            can_edit_treasury=True,
            can_view_shipping=True,
            can_edit_shipping=True,
            can_view_reports=True,
            can_manage_users=True,
            can_backup=True
        )
        admin.set_password(form.password.data)

        db.session.add(admin)

        # إنشاء الخزائن الافتراضية
        main_treasury = Treasury(name='الخزينة الرئيسية', current_balance=0.0)
        shipping_treasury = Treasury(name='خزينة الشحن', current_balance=0.0)

        db.session.add(main_treasury)
        db.session.add(shipping_treasury)

        db.session.commit()

        flash('تم إنشاء حساب المدير الأول بنجاح', 'success')
        return redirect(url_for('login'))

    return render_template('auth/first_admin.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Routes مؤقتة للصفحات الأخرى
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/change-password')
@login_required
def change_password():
    return render_template('change_password.html')

@app.route('/inventory')
@login_required
def inventory():
    if not current_user.can_view_inventory:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('inventory.html')

@app.route('/invoices')
@login_required
def invoices():
    if not current_user.can_view_invoices:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('invoices.html')

@app.route('/returns')
@login_required
def returns():
    if not current_user.can_view_returns:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('returns.html')

@app.route('/treasury')
@login_required
def treasury():
    if not current_user.can_view_treasury:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('treasury.html')

@app.route('/shipping')
@login_required
def shipping():
    if not current_user.can_view_shipping:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('shipping.html')

@app.route('/reports')
@login_required
def reports():
    if not current_user.can_view_reports:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('reports.html')

@app.route('/users')
@login_required
def users():
    if not current_user.can_manage_users:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('users.html')

@app.route('/backup')
@login_required
def backup():
    if not current_user.can_backup:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
        return redirect(url_for('dashboard'))
    return render_template('backup.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # إنشاء المدير الأول إذا لم يكن موجوداً
        if not User.query.filter_by(role='admin').first():
            print("لم يتم العثور على مدير. يرجى إنشاء حساب المدير الأول من خلال الواجهة.")

    app.run(debug=True, host='0.0.0.0', port=5000)