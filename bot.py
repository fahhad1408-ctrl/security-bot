import openpyxl
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
            return "error", None
        
        # استخدام مكتبة openpyxl مباشرة لقراءة وتعديل الملف وحفظه فوراً
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        
        user_code = str(user_code).strip()
        user_id = str(user_id).strip()
        
        row_index = None
        current_status = None
        saved_user_id = None
        expiry_val = None
        
        # البحث عن الكود صفاً بصَف (سريع جداً ومباشر)
        for row in range(2, sheet.max_row + 1):
            code_cell = sheet.cell(row=row, column=1) # العمود الأول: code
            if code_cell.value and str(code_cell.value).strip() == user_code:
                row_index = row
                current_status = str(sheet.cell(row=row, column=2).value).strip() # status
                expiry_val = str(sheet.cell(row=row, column=3).value).strip()     # expiry
                saved_user_id = str(sheet.cell(row=row, column=4).value).strip()  # user_id
                break
                
        if not row_index:
            wb.close()
            return "not_found", None
            
        # إذا كان مستخدماً مسبقاً
        if current_status == 'مستخدم':
            if saved_user_id == user_id:
                wb.close()
                return "success", expiry_val
            wb.close()
            return "used", None
            
        # تفعيل الكود لأول مرة وتحديث الخلايا مباشرة
        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        sheet.cell(row=row_index, column=2, value='مستخدم')
        sheet.cell(row=row_index, column=3, value=expiry)
        sheet.cell(row=row_index, column=4, value=user_id)
        
        # حفظ التعديل مباشرة في الملف
        wb.save(EXCEL_FILE)
        wb.close()
        return "success", expiry
        
    except Exception as e:
        print(f"❌ خطأ أثناء التحديث المباشر للإكسل: {e}")
        return "error", None

def check_user_active(user_id):
    try:
        if not os.path.exists(EXCEL_FILE): return False
        wb = openpyxl.load_workbook(EXCEL_FILE, read_only=True)
        sheet = wb.active
        user_id = str(user_id).strip()
        
        is_active = False
        for row in sheet.iter_rows(min_row=2, values_only=True):
            status = str(row[1]).strip()
            expiry_str = str(row[2]).strip()
            row_user_id = str(row[3]).strip()
            
            if row_user_id == user_id and status == 'مستخدم':
                try:
                    expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
                    if datetime.now() <= expiry_date:
                        is_active = True
                        break
                except:
                    continue
        wb.close()
        return is_active
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
