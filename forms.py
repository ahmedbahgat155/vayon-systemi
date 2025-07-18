from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, TextAreaField, DateField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional, EqualTo
from wtforms.widgets import TextArea

# نموذج تسجيل الدخول
class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')

# نموذج إنشاء المدير الأول
class FirstAdminForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', 
                                   validators=[DataRequired(), EqualTo('password', message='كلمات المرور غير متطابقة')])

# نموذج إنشاء/تعديل المستخدم
class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    full_name = StringField('الاسم الكامل', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('كلمة المرور', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', 
                                   validators=[Optional(), EqualTo('password', message='كلمات المرور غير متطابقة')])
    role = SelectField('الدور', choices=[('user', 'مستخدم'), ('manager', 'مدير'), ('admin', 'مدير عام')])
    is_active = BooleanField('نشط')
    
    # صلاحيات المخزون
    can_view_inventory = BooleanField('عرض المخزون')
    can_edit_inventory = BooleanField('تعديل المخزون')
    can_delete_inventory = BooleanField('حذف من المخزون')
    
    # صلاحيات الفواتير
    can_view_invoices = BooleanField('عرض الفواتير')
    can_edit_invoices = BooleanField('تعديل الفواتير')
    can_delete_invoices = BooleanField('حذف الفواتير')
    
    # صلاحيات المرتجعات
    can_view_returns = BooleanField('عرض المرتجعات')
    can_edit_returns = BooleanField('تعديل المرتجعات')
    can_delete_returns = BooleanField('حذف المرتجعات')
    
    # صلاحيات الخزينة
    can_view_treasury = BooleanField('عرض الخزينة')
    can_edit_treasury = BooleanField('تعديل الخزينة')
    
    # صلاحيات الشحن
    can_view_shipping = BooleanField('عرض الشحن')
    can_edit_shipping = BooleanField('تعديل الشحن')
    
    # صلاحيات أخرى
    can_view_reports = BooleanField('عرض التقارير')
    can_manage_users = BooleanField('إدارة المستخدمين')
    can_backup = BooleanField('النسخ الاحتياطي')

# نموذج العميل
class CustomerForm(FlaskForm):
    name = StringField('اسم العميل', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)])
    email = StringField('البريد الإلكتروني', validators=[Optional(), Email()])
    address = TextAreaField('العنوان', validators=[Optional()])
    city = StringField('المدينة', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('ملاحظات', validators=[Optional()])

# نموذج المورد
class SupplierForm(FlaskForm):
    name = StringField('اسم المورد', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)])
    email = StringField('البريد الإلكتروني', validators=[Optional(), Email()])
    address = TextAreaField('العنوان', validators=[Optional()])
    city = StringField('المدينة', validators=[Optional(), Length(max=50)])
    notes = TextAreaField('ملاحظات', validators=[Optional()])

# نموذج فئة المنتج
class ProductCategoryForm(FlaskForm):
    name = StringField('اسم الفئة', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('الوصف', validators=[Optional()])

# نموذج المنتج
class ProductForm(FlaskForm):
    name = StringField('اسم المنتج', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('كود المنتج', validators=[DataRequired(), Length(min=1, max=50)])
    category_id = SelectField('الفئة', coerce=int, validators=[Optional()])
    product_type = SelectField('نوع المنتج', choices=[('raw', 'خام'), ('finished', 'جاهز')], validators=[DataRequired()])
    unit = StringField('الوحدة', validators=[DataRequired(), Length(min=1, max=20)])
    min_stock_level = FloatField('الحد الأدنى للمخزون', validators=[Optional(), NumberRange(min=0)])
    cost_price = FloatField('سعر التكلفة', validators=[Optional(), NumberRange(min=0)])
    selling_price = FloatField('سعر البيع', validators=[Optional(), NumberRange(min=0)])
    manufacturing_cost = FloatField('تكلفة التصنيع', validators=[Optional(), NumberRange(min=0)])
    description = TextAreaField('الوصف', validators=[Optional()])
    is_active = BooleanField('نشط', default=True)

# نموذج تغيير كلمة المرور
class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', 
                                   validators=[DataRequired(), EqualTo('new_password', message='كلمات المرور غير متطابقة')])
