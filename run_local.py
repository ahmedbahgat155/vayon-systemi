#!/usr/bin/env python3
"""
تشغيل النظام محلياً للاختبار
"""

from vayon_advanced import app

if __name__ == "__main__":
    print("🚀 تشغيل نظام VAYON محلياً...")
    print("="*40)
    print("🌐 الرابط: http://localhost:5000")
    print("🔑 اسم المستخدم: admin")
    print("🔐 كلمة المرور: admin123")
    print("="*40)
    print("اضغط Ctrl+C للإيقاف")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
