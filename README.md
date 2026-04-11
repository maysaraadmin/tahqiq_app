# نظام تحقيق الكتب وتتبع الأسانيد

تطبيق PyQt6 لإدارة الكتب والمؤلفين وتتبع علاقات الشيوخ والطلاب في مجال التحقيق العلمي.

## هيكل المشروع

```
tahqiq_app/
├── main.py                     # نقطة بدء التطبيق
├── requirements.txt            # تبعيات المشروع
├── database/
│   ├── __init__.py
│   ├── db_manager.py           # مدير الاتصال والجلسات
│   └── models.py               # نماذج SQLAlchemy
├── controllers/
│   ├── __init__.py
│   ├── author_controller.py    # منطق التعامل مع المؤلفين
│   ├── book_controller.py      # منطق التعامل مع الكتب
│   └── relation_controller.py  # منطق التعامل مع العلاقات
├── views/
│   ├── __init__.py
│   ├── main_window.py          # النافذة الرئيسية
│   ├── author_dialog.py        # نافذة إضافة/تعديل مؤلف
│   ├── book_dialog.py          # نافذة إضافة/تعديل كتاب
│   ├── manuscript_dialog.py    # نافذة إضافة مخطوط
│   ├── relations_widget.py     # ودجت عرض العلاقات (شيوخ/طلاب)
│   ├── sheikh_student_dialog.py# نافذة إضافة علاقة شيخ/طالب
│   └── resources/
│       ├── styles.qss          # تنسيقات الواجهة
│       └── icons/              # (اختياري)
└── README.md
```

## المتطلبات

- Python 3.8+
- PyQt6
- SQLAlchemy
- arabic-reshaper (لدعم النصوص العربية)
- python-bidi (لترتيب النصوص العربية)

## التثبيت والتشغيل

1. **إنشاء بيئة افتراضية:**
   ```bash
# Tahqiq Book Verification and Isnad Tracking System

A secure, robust PyQt6 application for managing books, authors, and tracking sheikh/student relationships in academic research.

## Security & Performance Features

### Security Improvements
- **SQL Injection Protection**: All database queries use parameterized statements
- **Input Validation**: Comprehensive validation for all user inputs
- **Path Traversal Prevention**: Secure file loading with path validation
- **XSS Protection**: Sanitization of text inputs to prevent script injection
- **Data Integrity**: Database constraints prevent duplicate and invalid data

### Performance Optimizations
- **Singleton Database Manager**: Prevents memory leaks and connection exhaustion
- **Pagination Support**: Efficient handling of large datasets
- **Connection Pooling**: Optimized database connection management
- **Resource Cleanup**: Proper cleanup of database sessions and resources

### Error Handling
- **Global Exception Handler**: Catches and logs all unhandled exceptions
- **User-Friendly Messages**: Clear error messages in Arabic
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Graceful Degradation**: Application continues running even if optional features fail

1. **إنشاء بيئة افتراضية:**
   ```bash
   python -m venv venv
   # على Windows:
   venv\Scripts\activate
   # على Linux/Mac:
   source venv/bin/activate
   ```

2. **تثبيت التبعيات:**
   ```bash
   pip install -r requirements.txt
   ```

3. **تشغيل التطبيق:**
   ```bash
   python main.py
   ```

## الميزات

### إدارة المؤلفين
- إضافة مؤلفين جدد مع معلوماتهم الشخصية
- عرض قائمة المؤلفين في جدول منظم
- حذف المؤلفين مع جميع بياناتهم المرتبطة

### إدارة الكتب والمخطوطات
- إضافة كتب جديدة وربطها بمؤلفيها
- إدارة المخطوطات ومعلومات النسخ
- تنظيم البيانات في واجهة سهلة الاستخدام

### تتبع الأسانيد
- إضافة علاقات الشيوخ والطلاب
- تحديد نوع التلقي (سماع، إجازة، قراءة، ...)
- عرض شبكة العلاقات بين المؤلفين

## قاعدة البيانات

يستخدم التطبيق SQLite مع SQLAlchemy لتخزين البيانات محلياً. يتم إنشاء قاعدة البيانات تلقائياً عند أول تشغيل للتطبيق باسم `tahqiq_data.db`.

## التطوير المستقبلي

- إضافة تقارير متقدمة عن الأسانيد
- دعم استيراد/تصدير البيانات
- إضافة واجهة للمقارنة بين المخطوطات
- تحسين دعم النصوص العربية والخطوط
- إضافة صور للمخطوطات

## المشاكل المعروفة

- قد تحتاج النصوص العربية إلى ضبط إضافي لعرضها بشكل صحيح
- الواجهة تحتاج إلى تحسين لدعم الشاشات عالية الدقة

## المساهمة

يمكنك المساهمة في تطوير التطبيق عبر:
- الإبلاغ عن المشاكل
- اقتراح ميزات جديدة
- تحسين الكود المصدري
