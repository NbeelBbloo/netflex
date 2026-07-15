# استخدام بيئة بايثون جاهزة ومدمج معها متصفحات Playwright رسمياً
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

# تحديد مسار العمل داخل السيرفر
WORKDIR /app

# نسخ ملف المتطلبات وتثبيت مكتبة التيليجرام
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود البوت إلى السيرفر
COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]
