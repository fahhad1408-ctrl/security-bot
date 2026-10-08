import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, PreCheckoutQueryHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8870760665:AAGYJUTA0-MW34ivVBeNbYGUeBj1PKsdc90'
WEB_APP_URL = 'https://fahhad1408-ctrl.github.io/security-check/'
DB_FILE = 'database.db'
EXCEL_FILE = 'codThqq.xlsx'

STARS_PRICE = 150  # عدد النجوم المطلوب للاشتراك
TUTORIAL_IMAGE_URL = 'https://example.com/your-tutorial-image.jpg'  # ضع هنا رابط الصورة التوضيحية لشرح الاستخدام

def init_database():
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_users (
        user_id TEXT PRIMARY KEY,
        first_seen TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS broadcast_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        message_id INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()

    if not os.path.exists(DB_FILE) and os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, dtype=str)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for _, row in df.iterrows():
            code = str(row['code']).strip() if pd.notna(row['code']) else ""
            status = str(row['status']).strip() if pd.notna(row['status']) else "جديد"
            expiry = str(row['expiry']).strip() if pd.notna(row['expiry']) else ""
            user_id = str(row['user_id']).strip() if pd.notna(row['user_id']) else ""
            if code:
                cursor.execute('INSERT OR IGNORE INTO codes (code, status, expiry, user_id) VALUES (?, ?, ?, ?)', (code, status, expiry, user_id))
        conn.commit()
        conn.close()

def register_start_user(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        user_id = str(user_id).strip()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT OR IGNORE INTO bot_users (user_id, first_seen) VALUES (?, ?)", (user_id, now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في تسجيل المستخدم: {e}")

def activate_user_directly(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        user_id = str(user_id).strip()
        expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        cursor.execute("INSERT OR REPLACE INTO codes (code, status, expiry, user_id) VALUES (?, 'مستخدم', ?, ?)", 
                       (f"STARS_{user_id}", expiry, user_id))
        conn.commit()
        conn.close()
        return expiry
    except Exception as e:
        print(f"❌ خطأ في تفعيل المستخدم: {e}")
        return None

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
    register_start_user(user_id)
    
    if check_user_active(user_id):
        personalized_url = f"{WEB_APP_URL}?user={user_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("افتح فحص الأمان 🔍", web_app=WebAppInfo(url=personalized_url))]])
        await update.message.reply_text("👋 أهلاً بك مجدداً! حسابك مفعل ولديك صلاحية الوصول.", reply_markup=markup)
    else:
        text = (
            "🛡️ **مرحباً بك في بوت الفحص الأمني المتقدم**\n\n"
            "إذا كنت ترغب بفحص جوالك، فالنتيجة ستظهر لك فوراً وبشكل دقيق.\n"
            "🔒 **نحيطك علماً بأن البوت لا يقوم بحفظ أي بيانات أو معلومات عنك نهائياً**، "
            "حيث يتمتع بخصوصية عالية وموثوقة للمستخدم.\n\n"
            "اضغط على الزر أدناه للبدء:"
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("نعم، أريد فحص الجوال 🔍", callback_data="want_to_scan")]])
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "want_to_scan":
        text = (
            "💳 **رسوم تفعيل الفحص**\n\n"
            f"للاستمرار في استخدام البوت، تبلغ رسوم الاشتراك لمدة 30 يوماً **{STARS_PRICE} ⭐️ نجوم تيليجرام** فقط.\n"
            "💡 هذه الرسوم رمزية لاستمرار تشغيل وصيانة البوت، ولا تكلفك سعر كوب قهوة أو وجبة عشاء!\n\n"
            "اضغط على زر الشراء أدناه لإتمام العملية فوراً:"
        )
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"رسوم الفحص اضغط هنا  بـ {STARS_PRICE} ⭐️", callback_data="buy_stars")]])
        await query.message.edit_text(text, reply_markup=markup, parse_mode="Markdown")
        
    elif query.data == "buy_stars":
        chat_id = query.message.chat_id
        title = " تستطيع فحص جوالك عدد لانهائي مدة (30 يوماً)"
        description = "ستظهر لك بعد الدفع نتيجة كاملة لفحص الجوال وكشف الروت وحالة الجهاز."
        payload = "security_scan_subscription"
        currency = "XTR" 
        prices = [LabeledPrice("اشتراك 30 يوم", STARS_PRICE)]
        
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="", 
            currency=currency,
            prices=prices
        )

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload == "security_scan_subscription":
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="حدث خطأ في عملية الدفع، يرجى المحاولة لاحقاً.")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment.invoice_payload == "security_scan_subscription":
        user_id = update.effective_user.id
        exp = activate_user_directly(user_id)
        
        personalized_url = f"{WEB_APP_URL}?user={user_id}"
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("إبدأ الفحص الآن 🔍", web_app=WebAppInfo(url=personalized_url))]])
        
        caption_text = (
            f"🎉 **تم الدفع بنجاح وتفعيل اشتراكك!**\n"
            f"📅 ينتهي الاشتراك في: `{exp}`\n\n"
            "👇 **طريقة الاستخدام والشرح:**\n"
            "اضغط على زر الفحص أدناه، وتأكد من الموافقة على صلاحية الموقع أو إعدادات الفحص كما هو موضح في الصورة أعلاه للحصول على نتيجة دقيقة."
        )
        
        # إرسال الصورة التوضيحية مع زر الفحص تحتها مباشرة
        try:
            await update.message.reply_photo(
                photo=TUTORIAL_IMAGE_URL,
                caption=caption_text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception:
            # لو لم يعمل رابط الصورة لأي سبب، يتم إرسال النص مع الزر مباشرة بدون توقف
            await update.message.reply_text(caption_text, reply_markup=markup, parse_mode="Markdown")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text_input = update.message.text.strip()
    
    # 1. أمر تحميل قاعدة البيانات (Ather)
    if text_input == "Ather":
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as f:
                await update.message.reply_document(document=f, caption="📊 قاعدة البيانات الحالية.")
        else:
            await update.message.reply_text("❌ قاعدة البيانات غير موجودة بعد.")
        return

    # 2. أمر عرض المشتركين النشطين (foz)
    if text_input == "foz":
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM codes WHERE status = 'مستخدم'")
            count = cursor.fetchone()[0]
            conn.close()
            await update.message.reply_text(f"👥 عدد المشتركين النشطين حالياً هو: {count} مستخدم.")
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ أثناء جلب الإحصائية.")
        return

    # 3. أمر إجمالي من ضغطوا start (fahhad)
    if text_input == "fahhad":
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bot_users")
            count = cursor.fetchone()[0]
            conn.close()
            await update.message.reply_text(f"🚀 إجمالي عدد الأشخاص الذين ضغطوا /start ودخلوا البوت هو: {count} شخص.")
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ أثناء جلب الإحصائية.")
        return

    # 4. أمر الإذاعة (sendfahhad)
    if text_input.startswith("sendfahhad"):
        msg_content = text_input.replace("sendfahhad", "").strip()
        if not msg_content:
            await update.message.reply_text("⚠️ الرجاء كتابة النص المراد إرساله بعد الأمر `sendfahhad`")
            return
            
        await update.message.reply_text("⏳ جاري إرسال الرسالة لجميع المستخدمين...")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM bot_users")
        users = cursor.fetchall()
        
        success_count = 0
        fail_count = 0
        
        for u in users:
            u_id = u[0]
            try:
                sent_msg = await context.bot.send_message(chat_id=int(u_id), text=msg_content)
                cursor.execute("INSERT INTO broadcast_messages (user_id, message_id) VALUES (?, ?)", (u_id, sent_msg.message_id))
                success_count += 1
            except Exception:
                fail_count += 1
                
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ تم الانتهاء من الإذاعة!\n- تم الإرسال بنجاح: {success_count}\n- فشل الإرسال (حظروا البوت): {fail_count}")
        return

    # 5. أمر حذف الإذاعة (delfahhad)
    if text_input == "delfahhad":
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, message_id FROM broadcast_messages")
            messages = cursor.fetchall()
            
            if not messages:
                await update.message.reply_text("⚠️ لا توجد رسائل إذاعة سابقة لحذفها.")
                conn.close()
                return
                
            deleted_count = 0
            for u_id, m_id in messages:
                try:
                    await context.bot.delete_message(chat_id=int(u_id), message_id=int(m_id))
                    deleted_count += 1
                except Exception:
                    pass
                    
            cursor.execute("DELETE FROM broadcast_messages")
            conn.commit()
            conn.close()
            await update.message.reply_text(f"🗑 تم بنجاح حذف رسائل الإذاعة من عند {deleted_count} مستخدم.")
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء الحذف: {e}")
        return

    # 6. أمر التقرير الشامل (Qeth)
    if text_input == "Qeth":
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM bot_users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM codes WHERE status = 'مستخدم'")
            active_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM broadcast_messages")
            broadcast_reached = cursor.fetchone()[0]
            
            conn.close()
            
            report = f"""📊 **تقرير أداء البوت الشامل (Qeth):**
            
🚀 إجمالي من زاروا البوت وضغطوا /start: `{total_users}`
💎 المشتركون النشطون حالياً (لديهم صلاحية): `{active_users}`
📢 آخر حملة إذاعة وصلت إلى: `{broadcast_reached}` مستخدم
"""
            await update.message.reply_text(report, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ حدث خطأ أثناء جلب التقرير: {e}")
        return

def main():
    init_database()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    print("🚀 البوت يعمل الآن بالواجهة التفاعلية والرسائل التطمينية والصورة التوضيحية...")
    app.run_polling()

if __name__ == '__main__':
    main()
