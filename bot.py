import pandas as pd
from datetime import datetime, timedelta
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8755097566:AAH3VXDwvajPc_FtfiRKvmz9NhyqQ7eQX6A'
STORE_URL = 'https://salla.sa/yourstore' 
WEB_APP_URL = 'https://fahhad1408-ctrl.github.io/security-check/'
EXCEL_FILE = 'codThqq.xlsx'

def check_and_activate(user_code, user_id):
    try:
        if not os.path.exists(EXCEL_FILE): 
            print("⚠️ ملف الإكسل غير موجود في مجلد المشروع!")
            return "error", None
        
        # قراءة الأعمدة كنصوص صريحة
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        
        # تنظيف الفراغات
        df['code'] = df['code'].fillna('').str.strip()
        df['status'] = df['status'].fillna('').str.strip()
        df['user_id'] = df['user_id'].fillna('').str.strip()
        df['expiry'] = df['expiry'].fillna('').str.strip()
        
        user_code = str(user_code).strip()
        user_id = str(user_id).strip()
        
        # البحث عن الكود باستخدام البحث السريع في المصفوفة
        match = df[df['code'] == user_code]
        if match.empty:
            return "not_found", None
        
        idx = match.index[0]
        current_status = df.at[idx, 'status']
        saved_user_id = df.at[idx, 'user_id']
        
        # إذا كان الكود مستخدماً مسبقاً
        if current_status == 'مستخدم':
            if saved_user_id == user_id:
                return "success", df.at[idx, 'expiry']
            return "used", None
        
        # تفعيل الكود لأول مرة
        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        df.loc[idx, 'status'] = 'مستخدم'
        df.loc[idx, 'expiry'] = expiry
        df.loc[idx, 'user_id'] = user_id
        
        # حفظ التعديلات مع الحفاظ على صيغة الملف الأضخم
        df.to_excel(EXCEL_FILE, index=False)
        return "success", expiry
    except Exception as e:
        print(f"❌ خطأ أثناء قراءة أو تحديث الإكسل: {e}")
        return "error", None

def check_user_active(user_id):
    try:
        if not os.path.exists(EXCEL_FILE): return False
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        df['user_id'] = df['user_id'].fillna('').str.strip()
        df['status'] = df['status'].fillna('').str.strip()
        df['expiry'] = df['expiry'].fillna('').str.strip()
        
        user_id = str(user_id).strip()
        user_rows = df[df['user_id'] == user_id]
        
        if not user_rows.empty:
            for _, row in user_rows.iterrows():
                if row['status'] == 'مستخدم' and row['expiry']:
                    try:
                        expiry_date = datetime.strptime(row['expiry'], '%Y-%m-%d')
                        if datetime.now() <= expiry_date:
                            return True
                    except Exception:
                        continue
    except Exception as e:
        print(f"❌ خطأ في التحقق من نشاط المستخدم: {e}")
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
        await update.message.reply_text("❌ حدث خطأ تقني في قراءة ملف الأكواد.")
    else:
        await update.message.reply_text("❌ كود خاطئ! احصل عليه من المتجر.", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("المتجر 🛒", url=STORE_URL)]]) )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    print("🚀 البوت يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()
