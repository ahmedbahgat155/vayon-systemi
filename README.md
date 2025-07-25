# 💎 VAYON - نظام إدارة الأزياء الرجالية الفاخرة

## 🎯 **نظام ERP احترافي باللغة العربية**

نظام إدارة أعمال متكامل مصمم خصيصاً لشركات الأزياء الرجالية الفاخرة، يوفر جميع الأدوات اللازمة لإدارة المبيعات، المشتريات، المخزون، والتقارير المالية.

---

## 🚀 **التشغيل السريع:**

### **1. التشغيل المحلي:**
```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# تشغيل النظام
python app.py
```

### **2. الوصول للنظام:**
- **الرابط:** http://localhost:5000
- **الإعداد الأولي:** http://localhost:5000/setup-first-admin

---

## 🎨 **المميزات الرئيسية:**

### **🔐 نظام المستخدمين والصلاحيات:**
- **مدير (Admin):** صلاحيات كاملة
- **بائع (Seller):** مبيعات وعملاء وعرض المخزون
- **مشاهد (Viewer):** عرض التقارير والمخزون فقط
- تسجيل دخول آمن مع تشفير كلمات المرور

### **📦 إدارة المخزون الذكية:**
- **منتجات خام:** أقمشة، خيوط، إكسسوارات
- **منتجات جاهزة:** ملابس مصنعة
- تتبع الكميات بدقة (دعم الأرقام العشرية)
- تنبيهات المخزون المنخفض
- تسجيل حركات المخزون التفصيلية

### **🧾 نظام الفواتير المتطور:**
- **فواتير البيع:** مع ربط العملاء والمنتجات
- **فواتير الشراء:** مع ربط الموردين
- حساب الضرائب والخصومات
- ربط تلقائي بالمخزون والخزنة
- طباعة وتصدير PDF

### **🔄 نظام المرتجعات الشامل:**
- **مرتجعات البيع:** مرتبطة بالفواتير الأصلية
- **مرتجعات الشراء:** للموردين
- تحديث تلقائي للمخزون والخزنة
- تسجيل أسباب المرتجع

### **💰 إدارة الخزائن المتعددة:**
- **الخزنة الرئيسية:** للمعاملات العامة
- **خزنة شركة الشحن:** لأموال الشحن
- تتبع جميع الحركات المالية
- تقارير يومية وشهرية

### **🚚 نظام تتبع الشحنات:**
- إدخال رقم البوليصة
- حالة الشحن: (قيد الشحن / تم التسليم)
- حالة التحصيل: (تم التحصيل / لم يتم)
- متابعة شركات الشحن

### **📊 التقارير المفصلة:**
- تقارير المبيعات والمشتريات
- تقارير الأرباح (صافي الربح = سعر البيع - التكلفة - التصنيع)
- تقارير حركة المخزون
- تقارير الخزنة والتدفق النقدي
- تصدير جميع التقارير كـ PDF عربي

### **📈 لوحة التحكم الذكية:**
- إحصائيات يومية وشهرية
- مؤشرات الأداء الرئيسية
- تنبيهات ملونة للمشاكل
- الأنشطة الأخيرة
- إجراءات سريعة

### **💾 النسخ الاحتياطي التلقائي:**
- نسخ احتياطية كل 3 دقائق
- حفظ تلقائي في مجلد `/backups`
- إدارة النسخ الاحتياطية
- تنزيل واستعادة النسخ

### **🎨 التصميم الفاخر:**
- ألوان VAYON الرسمية:
  - **الأساسي:** #1B222A (أزرق داكن)
  - **الثانوي:** #DBC7A5 (بيج)
  - **المساعد:** #916138 (جملي)
- واجهة عربية كاملة RTL
- خط Cairo الأنيق
- تصميم متجاوب للهواتف

---

## 🏗️ **البنية التقنية:**

### **قاعدة البيانات:**
- **المحلي:** SQLite للتطوير
- **الإنتاج:** PostgreSQL على Render
- **الجداول:** 15+ جدول متخصص
- **العلاقات:** مترابطة ومحسنة

### **الأمان:**
- **تشفير كلمات المرور:** Werkzeug
- **حماية الجلسات:** Flask-Login
- **صلاحيات متدرجة:** نظام مخصص
- **فحص صحة النظام:** `/health`

### **الأداء:**
- **النسخ الاحتياطي:** خيط منفصل
- **قاعدة البيانات:** محسنة للسرعة
- **الذاكرة:** إدارة فعالة
- **الاستجابة:** سريعة ومتجاوبة

---

## 📁 **هيكل المشروع:**

```
VAYON_ERP/
├── app.py                 # التطبيق الرئيسي
├── requirements.txt       # المتطلبات
├── render.yaml           # إعدادات النشر
├── Procfile              # إعدادات Heroku
├── templates/
│   ├── base.html         # القالب الأساسي
│   ├── setup_first_admin.html  # إعداد المدير
│   ├── login.html        # تسجيل الدخول
│   └── dashboard.html    # لوحة التحكم
├── static/
│   ├── css/             # ملفات CSS
│   ├── js/              # ملفات JavaScript
│   └── images/          # الصور
├── backups/             # النسخ الاحتياطية
├── uploads/             # الملفات المرفوعة
└── reports/             # التقارير
```

---

## 🎯 **الاستخدام:**

### **1. الإعداد الأولي:**
1. تشغيل التطبيق لأول مرة
2. الذهاب إلى `/setup-first-admin`
3. إنشاء حساب المدير الأول
4. تسجيل الدخول للنظام

### **2. إدارة المستخدمين:**
- إضافة مستخدمين جدد
- تحديد الأدوار والصلاحيات
- مراقبة النشاط

### **3. إدارة المخزون:**
- إضافة المنتجات (خام وجاهزة)
- تحديد الكميات والأسعار
- متابعة حركات المخزون

### **4. إدارة المبيعات:**
- إنشاء فواتير البيع
- ربط بالعملاء والمنتجات
- متابعة الشحن والتحصيل

### **5. إدارة المشتريات:**
- إنشاء فواتير الشراء
- ربط بالموردين
- تحديث المخزون تلقائياً

### **6. المتابعة والتقارير:**
- مراجعة لوحة التحكم
- تصدير التقارير
- متابعة الأداء

---

## 🌐 **النشر على Render:**

### **1. إعداد المستودع:**
```bash
git init
git add .
git commit -m "VAYON ERP System"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

### **2. النشر:**
1. إنشاء حساب على Render.com
2. ربط المستودع
3. اختيار `render.yaml` للإعدادات
4. النشر التلقائي

### **3. إعداد قاعدة البيانات:**
- سيتم إنشاء PostgreSQL تلقائياً
- ربط تلقائي بالتطبيق
- نسخ احتياطية يومية

---

## 🔧 **الصيانة:**

### **النسخ الاحتياطي:**
- تلقائي كل 3 دقائق
- يدوي عند الحاجة
- تنزيل النسخ المحفوظة

### **المراقبة:**
- فحص صحة النظام: `/health`
- مراقبة الأداء
- تتبع الأخطاء

### **التحديثات:**
- تحديث النظام
- إضافة مميزات جديدة
- تحسين الأداء

---

## 📞 **الدعم الفني:**

### **في حالة المشاكل:**
1. تحقق من logs النظام
2. راجع النسخ الاحتياطية
3. تأكد من اتصال قاعدة البيانات
4. اختبر النظام محلياً

### **التطوير:**
- إضافة وظائف جديدة
- تخصيص التقارير
- تحسين الواجهة
- دمج أنظمة خارجية

---

## 🎊 **النظام جاهز للاستخدام الاحترافي!**

**تاريخ الإنجاز:** 2024-07-18  
**الحالة:** ✅ نظام ERP احترافي كامل  
**المطور:** Augment Agent  

© 2024 VAYON - نظام إدارة الأزياء الفاخرة
