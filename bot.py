import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8755097566:AAH3VXDwvajPc_FtfiRKvmz9NhyqQ7eQX6A'
STORE_URL = 'https://salla.sa/yourstore' 
WEB_APP_URL = 'https://fahhad1408-ctrl.github.io/security-check/'
DB_FILE = 'database.db'
EXCEL_FILE = 'codThqq.xlsx'

# دالة التحويل التلقائي من إكسل إلى SQLite فور تشغيل البوت على السيرفر
def init_database():
    if not os.path.exists(DB_FILE):
        print("🔄 جاري إنشاء قاعدة البيانات وتحويل الأكواد من ملف الإكسل لأول مرة...")
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, dtype=str)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                status TEXT,
                expiry TEXT,
                user_id TEXT
            )
            ''')
            
            for _, row in df.iterrows():
                code = str(row['code']).strip() if pd.notna(row['code']) else ""
                status = str(row['status']).strip() if pd.notna(row['status']) else "جديد"
                expiry = str(row['expiry']).strip() if pd.notna(row['expiry']) else ""
                user_id = str(row['user_id']).strip() if pd.notna(row['user_id']) else ""
                
                if code:
                    cursor.execute('''
                    INSERT OR IGNORE INTO codes (code, status, expiry, user_id) 
                    VALUES (?, ?, ?, ?)
                    ''', (code, status, expiry, user_id))
            
            conn.commit()
            conn.close()
            print("✅ تم إنشاء وتعبئة قاعدة البيانات SQLite بنجاح تام!")
        else:
            print("⚠️ تنبيه: لم يتم العثور على ملف الإكسل!")

def check_and_activate(user_code, user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        user_code = str(user_code).strip()
        user_id = str(user_id).strip()
        
        cursor.execute("SELECT status, expiry, user_id FROM codes WHERE code = ?", (user_code,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "not_found", None
            
        current_status, expiry_val, saved_user_id = row
        
        if current_status == 'مستخدم':
            if saved_user_id == user_id:
                conn.close()
                return "success", expiry_val
            conn.close()
            return "used", None
            
        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE codes 
            SET status = 'مستخدم', expiry = ?, user_id = ? 
            WHERE code = ?
        """, (expiry, user_id, user_code))
        
        conn.commit()
        conn.close()
        return "success", expiry
        
    except Exception as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return "error", None

def check_user_active(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        user_id = str(user_id).strip()
        
        cursor.execute("SELECT expiry FROM codes WHERE user_id = ? AND status = 'مستخدم'", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            expiry_str = row[0]
            try:
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
                if datetime.now() <= expiry_date:
                    return True
            except:
                continue
        return False
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if check_user_active(user_id):
        personalized_url = f"{WEB_APP_URL}?user={user_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("افتح فحص الأمان 🔍", web_app=WebAppInfo(url=personalized_url))]])
        await update.message.reply_text("👋 أهلاً بك مجدداً! حسابك مفعل ولديك صلاحية الوصول.", reply_markup=markup)
    else:
        text = "🛡️ أهلاً بك في بوت الفحص الأمني.\nالرجاء إرسال كود التفعيل الخاص بك للدخول."
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("شراء كود تفعيل 🛒", url=STORE_URL)]])
        await update.message.reply_text(text, reply_markup=markup)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    u_code = update.message.text.strip()
    u_id = update.message.from_user.id
    
    res, exp = check_and_activate(u_code, u_id)
    
    if res == "success":
        personalized_url = f"{WEB_APP_URL}?user={u_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("إبدأ الفحص الآن 🔍", web_app=WebAppInfo(url=personalized_url))]])
        await update.message.reply_text(f"✅ تم التفعيل بنجاح!\n📅 ينتهي في: {exp}", reply_markup=markup)
    elif res == "used":
        await update.message.reply_text("❌ هذا الكود مستخدم مسبقاً من قِبل شخص آخر!")
    elif res == "error":
        await update.message.reply_text("❌ حدث خطأ تقني في قاعدة البيانات.")
    else:
        await update.message.reply_text("❌ كود خاطئ! احصل عليه من المتجر.", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("المتجر 🛒", url=STORE_URL)]]) )

def main():
    # تشغيل فحص وإنشاء قاعدة البيانات تلقائياً أول ما يشتغل البوت
    init_database()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("🚀 البوت يعمل الآن بقاعدة بيانات SQLite الذكية...")
    app.run_polling()

if __name__ == '__main__':
    main()
