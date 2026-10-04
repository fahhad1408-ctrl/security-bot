import pandas as pd
from datetime import datetime, timedelta
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8755097566:AAH3VXDwvajPc_FtfiRKvmz9NhyqQ7eQX6A'
STORE_URL = 'https://salla.sa/yourstore' 
WEB_APP_URL = 'https://fahhad1408-ctrl.github.io/security-check/' # الرابط الذي رفعته على نتلفاي أو جيت هب
EXCEL_FILE = 'codThqq.xlsx'

def check_and_activate(user_code, user_id):
    if not os.path.exists(EXCEL_FILE): return "error", None
    df = pd.read_excel(EXCEL_FILE)
    
    if user_code not in df['code'].values:
        return "not_found", None
    
    idx = df.index[df['code'] == user_code].tolist()[0]
    
    # التحقق مما إذا كان الكود مستخدماً لنفس المستخدم مسبقاً
    if df.at[idx, 'status'] == 'مستخدم':
        if str(df.at[idx, 'user_id']) == str(user_id):
            return "success", str(df.at[idx, 'expiry'])
        return "used", None
    
    expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    df.at[idx, 'status'] = 'مستخدم'
    df.at[idx, 'expiry'] = expiry
    df.at[idx, 'user_id'] = str(user_id)
    df.to_excel(EXCEL_FILE, index=False)
    return "success", expiry

def check_user_active(user_id):
    """التحقق مما إذا كان المستخدم لديه تفعيل ساري في ملف الإكسل"""
    if not os.path.exists(EXCEL_FILE): return False
    df = pd.read_excel(EXCEL_FILE)
    # البحث عما إذا كان user_id موجود وحالته مستخدم
    user_rows = df[df['user_id'].astype(str) == str(user_id)]
    if not user_rows.empty:
        for _, row in user_rows.iterrows():
            if row['status'] == 'مستخدم':
                expiry_date = datetime.strptime(str(row['expiry']), '%Y-%m-%d')
                if datetime.now() <= expiry_date:
                    return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # التحقق السريع إذا كان المستخدم مفعل مسبقاً
    if check_user_active(user_id):
        personalized_url = f"{WEB_APP_URL}?user={user_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("افتح فحص الأمان 🔍", web_app=WebAppInfo(url=personalized_url))]])
        await update.message.reply_text("👋 أهلاً بك مجدداً! حسابك مفعل ولديك صلاحية الوصول.", reply_markup=markup)
    else:
        text = "🛡️ أهلاً بك في بوت الفحص الأمني.\nالرجاء إرسال كود التفعيل الخاص بك للدخول."
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("شراء كود تفعيل 🛒", url=STORE_URL)]])
        await update.message.reply_text(text, reply_markup=markup)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_code = update.message.text.strip()
    u_id = update.message.from_user.id
    res, exp = check_and_activate(u_code, u_id)
    
    if res == "success":
        personalized_url = f"{WEB_APP_URL}?user={u_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("إبدأ الفحص الآن 🔍", web_app=WebAppInfo(url=personalized_url))]])
        await update.message.reply_text(f"✅ تم التفعيل بنجاح!\n📅 ينتهي في: {exp}", reply_markup=markup)
    elif res == "used":
        # إذا كان الكود مستخدماً لنفس الشخص، نسمح له بالدخول
        if check_user_active(u_id):
            personalized_url = f"{WEB_APP_URL}?user={u_id}"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("إبدأ الفحص الآن 🔍", web_app=WebAppInfo(url=personalized_url))]])
            await update.message.reply_text("✅ حسابك مفعل مسبقاً وجهازك مسجل.", reply_markup=markup)
        else:
            await update.message.reply_text("❌ هذا الكود مستخدم مسبقاً من قِبل شخص آخر!")
    else:
        await update.message.reply_text("❌ كود خاطئ! احصل عليه من المتجر.", 
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("المتجر 🛒", url=STORE_URL)]]))

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
print("🚀 البوت يعمل الآن...")
app.run_polling()