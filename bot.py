import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ================= ⚙️ কনফিগারেশন =================
BOT_TOKEN = '8919161117:AAEFTcbYlxbgduHDmKdcRKeszSY9-szepQ8'
PRIMARY_ADMIN_ID = 2132743108  # প্রাথমিক এডমিন আইডি
MASTER_PASSWORD = 'Anis@2026'   # 🔑 আপনার সিক্রেট মাস্টার পাসওয়ার্ড

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = 'pro_subscription.db'

# ================= 🗄️ থ্রেড-সেফ ডাটাবেস হেল্পার =================
def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return result

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expire_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_channels (user_id INTEGER, chat_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS channel_timers (chat_id INTEGER PRIMARY KEY, expire_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (setting_key TEXT PRIMARY KEY, setting_value TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS channel_modes (chat_id INTEGER PRIMARY KEY, mode TEXT)''')
    
    # 📌 ফোর্স জয়েন টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        target_chat_id INTEGER, 
        req_chat_id INTEGER, 
        req_link TEXT, 
        req_title TEXT, 
        PRIMARY KEY (target_chat_id, req_chat_id)
    )''')
    
    # ডিফল্ট সেটিংস সেটআপ
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('sub_mode', 'ON')")
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('admin_id', ?)", (str(PRIMARY_ADMIN_ID),))
    conn.commit()
    conn.close()

init_db()

def get_current_admin_id():
    """ডাইনামিক এডমিন আইডি রিড করে"""
    res = db_query("SELECT setting_value FROM settings WHERE setting_key = 'admin_id'", fetchone=True)
    if res and res[0]:
        try:
            return int(res[0])
        except ValueError:
            pass
    return PRIMARY_ADMIN_ID

def parse_date(date_str):
    if not date_str:
        return datetime.now()
    try:
        return datetime.fromisoformat(str(date_str))
    except Exception:
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                pass
    return datetime.now()

# ================= 🎛️ এডমিন স্থায়ী রিপ্লাই কীবোর্ড =================
def get_admin_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    markup.add(KeyboardButton("🔄 ড্যাশবোর্ড"), KeyboardButton("📋 চ্যানেল তালিকা"))
    markup.add(KeyboardButton("🔴 গ্লোবাল পেইড (ON)"), KeyboardButton("🟢 গ্লোবাল ফ্রি (OFF)"))
    markup.add(KeyboardButton("👤 ইউজার যোগ"), KeyboardButton("❌ ইউজার ব্যান"))
    markup.add(KeyboardButton("🔴 চ্যানেল পেইড"), KeyboardButton("🟢 চ্যানেল ফ্রি"), KeyboardButton("⚙️ মোড রিসেট"))
    markup.add(KeyboardButton("🔒 চ্যানেল টাইমার"), KeyboardButton("🔓 চ্যানেল আনলক"))
    markup.add(KeyboardButton("🔗 ফোর্স চ্যানেল যোগ"), KeyboardButton("🗑 ফোর্স চ্যানেল মুছুন"))
    markup.add(KeyboardButton("📋 ফোর্স চ্যানেল তালিকা"), KeyboardButton("💬 ইউজার রিপ্লাই"))
    markup.add(KeyboardButton("📁 ব্যাকআপ ডাটাবেস"), KeyboardButton("🚨 ইমার্জেন্সি লকডাউন"))
    
    return markup

def render_dashboard_text():
    admin_id = get_current_admin_id()
    res = db_query("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'", fetchone=True)
    sub_mode = res[0] if res else 'ON'
    
    total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    total_timers = db_query("SELECT COUNT(*) FROM channel_timers", fetchone=True)[0]
    paid_channels = db_query("SELECT COUNT(*) FROM channel_modes WHERE mode = 'PAID'", fetchone=True)[0]
    free_channels = db_query("SELECT COUNT(*) FROM channel_modes WHERE mode = 'FREE'", fetchone=True)[0]
    force_count = db_query("SELECT COUNT(DISTINCT target_chat_id) FROM force_channels", fetchone=True)[0]
    
    return f"<b>👑 প্রফেশনাল ভিআইপি সাবস্ক্রিপশন কন্ট্রোল প্যানেল</b>\n" \
           f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
           f"🆔 <b>সক্রিয় এডমিন আইডি:</b> <code>{admin_id}</code>\n" \
           f"⚙️ <b>বর্তমান সিস্টেম স্ট্যাটাস:</b>\n" \
           f"• গ্লোবাল সাবস্ক্রিপশন মোড: <b>{'🟢 পেইড (ON)' if sub_mode == 'ON' else '🔴 ফ্রি (OFF)'}</b>\n" \
           f"• মোট অ্যাক্টিভ ভিআইপি ইউজার: <b>{total_users} জন</b>\n" \
           f"• নির্দিষ্ট পেইড চ্যানেল: <b>{paid_channels} টি</b>\n" \
           f"• নির্দিষ্ট ফ্রি চ্যানেল: <b>{free_channels} টি</b>\n" \
           f"• ফোর্স অফার চ্যানেল: <b>{force_count} টি</b>\n" \
           f"• নিবন্ধিত টাইমার চ্যানেল: <b>{total_timers} টি</b>\n\n" \
           f"👇 <i>নিচের স্থায়ী বাটন থেকে অপশন বেছে নিন:</i>"

# ================= 🔐 ইমার্জেন্সি মাস্টার লগইন =================
@bot.message_handler(commands=['master_login', 'emergency_login'])
def process_master_login_command(message):
    msg = bot.send_message(message.chat.id, "🔐 <b>ইমার্জেন্সি মাস্টার প্রবেশাধিকার!</b>\n\nঅনুগ্রহ করে সিক্রেট মাস্টার পাসওয়ার্ডটি লিখুন:", parse_mode='HTML')
    bot.register_next_step_handler(msg, verify_master_password)

def verify_master_password(message):
    entered_pass = message.text.strip()
    if entered_pass == MASTER_PASSWORD:
        new_admin_id = message.from_user.id
        db_query("UPDATE settings SET setting_value = ? WHERE setting_key = 'admin_id'", (str(new_admin_id),), commit=True)
        bot.reply_to(message, f"🎉 <b>অভিনন্দন! এডমিন অ্যাক্সেস সফলভাবে স্থানান্তরিত হয়েছে।</b>\n\n🆔 <b>নতুন এডমিন আইডি:</b> <code>{new_admin_id}</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    else:
        bot.reply_to(message, "❌ <b>ভুল পাসওয়ার্ড!</b> এক্সেস দেওয়া সম্ভব হয়নি।", parse_mode='HTML')

# ================= 🟢 স্টার্ট ও হেল্প কমান্ড =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    current_admin = get_current_admin_id()
    
    if user_id == current_admin:
        msg = render_dashboard_text()
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    else:
        result = db_query("SELECT expire_date FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📩 এডমিনের সাথে যোগাযোগ করুন", url="https://t.me/anisgazibd"))

        if result:
            exp = parse_date(result[0])
            msg = f"<b>👑 স্বাগতম, সম্মানিত VIP মেম্বার!</b>\n" \
                  f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
                  f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                  f"⏳ <b>মেয়াদের শেষ সময়:</b> <code>{exp.strftime('%Y-%m-%d %I:%M %p')}</code>\n\n" \
                  f"✅ <b>স্ট্যাটাস:</b> আপনার প্রিমিয়াম ভিআইপি সাবস্ক্রিপশন সক্রিয় রয়েছে। 💎"
        else:
            msg = f"<b>👋 স্বাগতম, {message.from_user.first_name}!</b>\n" \
                  f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
                  f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                  f"📊 <b>বর্তমান স্ট্যাটাস:</b> 🔴 কোনো অ্যাক্টিভ সাবস্ক্রিপশন নেই\n\n" \
                  f"✨ আমাদের প্রিমিয়াম ভিআইপি চ্যানেলে যুক্ত হতে একটি অ্যাক্টিভ সাবস্ক্রিপশন প্রয়োজন।\n\n" \
                  f"💬 সাবস্ক্রিপশন নিতে বা এডমিনের সাথে কথা বলতে নিচে সরাসরি মেসেজ পাঠান।"
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=markup)

# ================= 🛡 এডমিন বাটন প্রসেসর =================
@bot.message_handler(func=lambda message: message.from_user.id == get_current_admin_id() and message.text in [
    "🔄 ড্যাশবোর্ড", "📋 চ্যানেল তালিকা", "🔴 গ্লোবাল পেইড (ON)", "🟢 গ্লোবাল ফ্রি (OFF)",
    "👤 ইউজার যোগ", "❌ ইউজার ব্যান", "🔴 চ্যানেল পেইড", "🟢 চ্যানেল ফ্রি", "⚙️ মোড রিসেট",
    "🔒 চ্যানেল টাইমার", "🔓 চ্যানেল আনলক", "💬 ইউজার রিপ্লাই", "📁 ব্যাকআপ ডাটাবেস", "🚨 ইমার্জেন্সি লকডাউন",
    "🔗 ফোর্স চ্যানেল যোগ", "🗑 ফোর্স চ্যানেল মুছুন", "📋 ফোর্স চ্যানেল তালিকা"
])
def handle_admin_buttons(message):
    text = message.text
    
    if text == "🔄 ড্যাশবোর্ড":
        bot.reply_to(message, render_dashboard_text(), parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
        
    elif text == "📋 চ্যানেল তালিকা":
        list_channels(message)
        
    elif text == "🔴 গ্লোবাল পেইড (ON)":
        db_query("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'", commit=True)
        bot.reply_to(message, "✅ <b>গ্লোবাল সাবস্ক্রিপশন মোড ON করা হয়েছে!</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
        
    elif text == "🟢 গ্লোবাল ফ্রি (OFF)":
        db_query("UPDATE settings SET setting_value = 'OFF' WHERE setting_key = 'sub_mode'", commit=True)
        bot.reply_to(message, "🔓 <b>গ্লোবাল সাবস্ক্রিপশন মোড OFF (ফ্রি মোড) করা হয়েছে!</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
        
    elif text == "📁 ব্যাকআপ ডাটাবেস":
        send_backup(message)
        
    elif text == "🚨 ইমার্জেন্সি লকডাউন":
        msg = bot.send_message(message.chat.id, "⚠️ <b>সতর্কতা! আপনি কি সমস্ত চ্যানেলের সকল মেম্বারকে ব্যান এবং চ্যানেল লক করতে চান?</b>\n\nনিশ্চিত করতে আপনার সিক্রেট মাস্টার পাসওয়ার্ড লিখুন:", parse_mode='HTML')
        bot.register_next_step_handler(msg, execute_emergency_lockdown)

    elif text == "👤 ইউজার যোগ":
        msg = bot.send_message(message.chat.id, "👤 <b>ইউজার আইডি এবং দিন লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789 30</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/add_user {m.text}"), add_user_time(m)])
        
    elif text == "❌ ইউজার ব্যান":
        msg = bot.send_message(message.chat.id, "❌ <b>ব্যান/বাতিল করতে চাওয়া ইউজার আইডি লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/del_user {m.text}"), delete_user(m)])
        
    elif text == "🔴 চ্যানেল পেইড":
        msg = bot.send_message(message.chat.id, "🔴 <b>পেইড করতে চাওয়া চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_paid {m.text}"), set_channel_paid(m)])
        
    elif text == "🟢 চ্যানেল ফ্রি":
        msg = bot.send_message(message.chat.id, "🟢 <b>ফ্রি করতে চাওয়া চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_free {m.text}"), set_channel_free(m)])
        
    elif text == "⚙️ মোড রিসেট":
        msg = bot.send_message(message.chat.id, "⚙️ <b>রিসেট করতে চাওয়া চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/del_channel {m.text}"), delete_channel_config(m)])
        
    elif text == "🔒 চ্যানেল টাইমার":
        msg = bot.send_message(message.chat.id, "🔒 <b>চ্যানেল আইডি এবং লকিং এর দিন লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890 7</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_channel_timer {m.text}"), set_channel_timer(m)])
        
    elif text == "🔓 চ্যানেল আনলক":
        msg = bot.send_message(message.chat.id, "🔓 <b>আনলক করতে চাওয়া চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/unlock_channel {m.text}"), unlock_channel(m)])
        
    elif text == "💬 ইউজার রিপ্লাই":
        msg = bot.send_message(message.chat.id, "💬 <b>ইউজার আইডি এবং মেসেজ লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789 আপনার মেসেজ</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/reply {m.text}"), admin_manual_reply(m)])

    elif text == "🔗 ফোর্স চ্যানেল যোগ":
        msg = bot.send_message(message.chat.id, "🔗 <b>ফোর্স চ্যানেল সেটআপ করুন:</b>\n\nফরম্যাট: <code>[অফার_চ্যানেল_আইডি] [প্রয়োজনীয়_চ্যানেল_আইডি] [ইনভাইট_লিংক] [চ্যানেলের_নাম]</code>\n\n<i>উদাহরণ:</i>\n<code>-1001234567890 -1009876543210 https://t.me/mychannel প্রমো চ্যানেল ১</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_add_force_channel)

    elif text == "🗑 ফোর্স চ্যানেল মুছুন":
        msg = bot.send_message(message.chat.id, "🗑 <b>ফোর্স চ্যানেল রিমুভ করুন:</b>\n\nফরম্যাট: <code>[অফার_চ্যানেল_আইডি] [প্রয়োজনীয়_চ্যানেল_আইডি]</code>\n\n<i>উদাহরণ:</i>\n<code>-1001234567890 -1009876543210</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_del_force_channel)

    elif text == "📋 ফোর্স চ্যানেল তালিকা":
        list_force_channels(message)

# ================= 🔗 ফোর্স চ্যানেল ফাংশনস =================
def process_add_force_channel(message):
    try:
        parts = message.text.strip().split(maxsplit=3)
        target_id = int(parts[0])
        req_id = int(parts[1])
        req_link = parts[2]
        req_title = parts[3]
        
        db_query("INSERT OR REPLACE INTO force_channels (target_chat_id, req_chat_id, req_link, req_title) VALUES (?, ?, ?, ?)", 
                 (target_id, req_id, req_link, req_title), commit=True)
                 
        bot.reply_to(message, f"✅ <b>ফোর্স জয়েন চ্যানেল সফলভাবে যোগ করা হয়েছে!</b>\n\n📢 <b>অফার চ্যানেল:</b> <code>{target_id}</code>\n🔗 <b>প্রয়োজনীয় চ্যানেল:</b> <code>{req_id}</code> ({req_title})", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>ভুল ফরম্যাট!</b> সঠিক ফর্মে লিখুন:\n<code>[অফার_আইডি] [প্রয়োজনীয়_আইডি] [লিংক] [নাম]</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())

def process_del_force_channel(message):
    try:
        parts = message.text.strip().split()
        target_id = int(parts[0])
        req_id = int(parts[1])
        
        db_query("DELETE FROM force_channels WHERE target_chat_id = ? AND req_chat_id = ?", (target_id, req_id), commit=True)
        bot.reply_to(message, f"🗑️ <b>ফোর্স চ্যানেল রিমুভ সফল!</b>\n📢 অফার চ্যানেল <code>{target_id}</code> থেকে <code>{req_id}</code> রিমুভ করা হয়েছে।", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল ফরম্যাট!</b> ব্যবহার: <code>[অফার_আইডি] [প্রয়োজনীয়_আইডি]</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())

def list_force_channels(message):
    rows = db_query("SELECT target_chat_id, req_chat_id, req_link, req_title FROM force_channels", fetchall=True) or []
    if not rows:
        bot.reply_to(message, "📋 <b>কোনো ফোর্স জয়েন চ্যানেল যুক্ত করা নেই।</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
        return

    text = "<b>📋 রেজিস্টার্ড ফোর্স জয়েন অফার চ্যানেলসমূহ:</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    grouped = {}
    for r in rows:
        t_id, r_id, link, title = r[0], r[1], r[2], r[3]
        if t_id not in grouped: grouped[t_id] = []
        grouped[t_id].append(f"• <a href='{link}'>{title}</a> (<code>{r_id}</code>)")

    for t_id, reqs in grouped.items():
        text += f"📢 <b>অফার চ্যানেল (<code>{t_id}</code>):</b>\n" + "\n".join(reqs) + "\n\n"

    bot.reply_to(message, text, parse_mode='HTML', reply_markup=get_admin_reply_keyboard())

# ================= 🚨 ইমার্জেন্সি এক্সিকিউশন =================
def execute_emergency_lockdown(message):
    if message.text.strip() != MASTER_PASSWORD:
        bot.reply_to(message, "❌ <b>ভুল পাসওয়ার্ড!</b> ইমার্জেন্সি বাতিল করা হয়েছে।", parse_mode='HTML')
        return

    bot.reply_to(message, "⏳ <b>জরুরি ইমার্জেন্সি প্রসেস শুরু হয়েছে... সব মেম্বারদের ব্যান করা হচ্ছে।</b>", parse_mode='HTML')
    
    all_user_channels = db_query("SELECT user_id, chat_id FROM user_channels", fetchall=True) or []
    banned_count = 0
    
    for row in all_user_channels:
        u_id, c_id = row[0], row[1]
        try:
            bot.ban_chat_member(c_id, u_id)
            banned_count += 1
        except Exception: pass

    db_query("DELETE FROM users", commit=True)
    db_query("DELETE FROM user_channels", commit=True)
    db_query("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'", commit=True)
    
    bot.send_message(message.chat.id, f"🚨 <b>ইমার্জেন্সি লকডাউন সম্পন্ন!</b>\n\n• মোট রিমুভ/ব্যান মেম্বার: <b>{banned_count} জন</b>\n• সকল সাবস্ক্রিপশন ডাটা রিসেট করা হয়েছে।\n• সমস্ত চ্যানেল পেইড লকডাউনে নেওয়া হয়েছে।", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())

# ================= 🛡 চ্যানেল ও সিস্টেম ফাংশনসমূহ =================
@bot.message_handler(commands=['list_channels', 'channels'])
def list_channels(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        modes = db_query("SELECT chat_id, mode FROM channel_modes", fetchall=True) or []
        timers = db_query("SELECT chat_id, expire_date FROM channel_timers", fetchall=True) or []
        
        paid_list = [f"• <code>{row[0]}</code>" for row in modes if row[1] == 'PAID']
        free_list = [f"• <code>{row[0]}</code>" for row in modes if row[1] == 'FREE']
        
        timer_list = []
        for row in timers:
            exp = parse_date(row[1])
            timer_list.append(f"• <code>{row[0]}</code> (মেয়াদ: {exp.strftime('%Y-%m-%d %H:%M')})")
        
        paid_str = "\n".join(paid_list) if paid_list else "<i>কোনো চ্যানেল নির্দিষ্ট করা নেই</i>"
        free_str = "\n".join(free_list) if free_list else "<i>কোনো চ্যানেল নির্দিষ্ট করা নেই</i>"
        timer_str = "\n".join(timer_list) if timer_list else "<i>কোনো টাইমার সেট করা নেই</i>"
        
        msg = f"<b>📋 রেজিস্টার্ড চ্যানেলসমূহ ও বর্তমান স্ট্যাটাস</b>\n" \
              f"━━━━━━━━━━━━━━━━━━━━━━━\n\n" \
              f"🔴 <b>পেইড চ্যানেলসমূহ ({len(paid_list)}টি):</b>\n{paid_str}\n\n" \
              f"🟢 <b>ফ্রি চ্যানেলসমূহ ({len(free_list)}টি):</b>\n{free_str}\n\n" \
              f"⏳ <b>টাইমার/অটো-লক চ্যানেলসমূহ ({len(timer_list)}টি):</b>\n{timer_str}\n\n" \
              f"💡 <i>মোড সরাতে লিখুন:</i> <code>/del_channel [Channel_ID]</code>"
        
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception as e:
        bot.reply_to(message, f"⚠️ সমস্যা হয়েছে: {e}")

@bot.message_handler(commands=['del_channel', 'reset_channel'])
def delete_channel_config(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        chat_id = int(message.text.split()[1])
        db_query("DELETE FROM channel_modes WHERE chat_id = ?", (chat_id,), commit=True)
        db_query("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,), commit=True)
        bot.reply_to(message, f"⚙️ <b>চ্যানেল রিসেট সফল!</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/del_channel [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_paid'])
def set_channel_paid(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        chat_id = int(message.text.split()[1])
        db_query("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'PAID')", (chat_id,), commit=True)
        bot.reply_to(message, f"🔴 <b>চ্যানেল মোড সেট: PAID</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_paid [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_free'])
def set_channel_free(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        chat_id = int(message.text.split()[1])
        db_query("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'FREE')", (chat_id,), commit=True)
        bot.reply_to(message, f"🟢 <b>চ্যানেল মোড সেট: FREE</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_free [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['add_user'])
def add_user_time(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        db_query("INSERT OR REPLACE INTO users (user_id, expire_date) VALUES (?, ?)", (user_id, expire_date), commit=True)
        bot.reply_to(message, f"✅ <b>ইউজার সাবস্ক্রিপশন যোগ করা হয়েছে!</b>\n👤 আইডি: <code>{user_id}</code>\n⏳ মেয়াদ: <b>{days} দিন</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/add_user [User_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['del_user'])
def delete_user(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        user_id = int(message.text.split()[1])
        user_chats = db_query("SELECT chat_id FROM user_channels WHERE user_id = ?", (user_id,), fetchall=True) or []
        
        removed_count = 0
        for chat in user_chats:
            try:
                bot.ban_chat_member(chat[0], user_id)
                removed_count += 1
            except Exception: pass
            
        db_query("DELETE FROM users WHERE user_id = ?", (user_id,), commit=True)
        db_query("DELETE FROM user_channels WHERE user_id = ?", (user_id,), commit=True)
        
        try:
            bot.send_message(user_id, "⚠ <b>আপনার প্রিমিয়াম সাবস্ক্রিপশন বাতিল করা হয়েছে এবং আপনাকে চ্যানেল থেকে রিমুভ করা হয়েছে।</b>", parse_mode='HTML')
        except Exception: pass

        bot.reply_to(message, f"🗑️ <b>ইউজার সাবস্ক্রিপশন বাতিল ও ব্যান সফল!</b>\n👤 আইডি: <code>{user_id}</code>\n📢 রিমুভ চ্যানেল: <b>{removed_count} টি</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/del_user [User_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_channel_timer'])
def set_channel_timer(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        parts = message.text.split()
        chat_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        db_query("INSERT OR REPLACE INTO channel_timers (chat_id, expire_date) VALUES (?, ?)", (chat_id, expire_date), commit=True)
        bot.reply_to(message, f"🚨 <b>চ্যানেল টাইমার সেট!</b>\n📢 চ্যানেল: <code>{chat_id}</code>\n⏳ সময়: <b>{days} দিন</b>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_channel_timer [Channel_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['unlock_channel'])
def unlock_channel(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        chat_id = int(message.text.split()[1])
        db_query("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,), commit=True)
        bot.reply_to(message, f"🔓 <b>চ্যানেল আনলক সফল!</b>\n📢 চ্যানেল: <code>{chat_id}</code>", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/unlock_channel [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['reply'])
def admin_manual_reply(message):
    if message.from_user.id != get_current_admin_id(): return
    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        text_to_send = parts[2]
        bot.send_message(target_id, f"<b>💬 এডমিন থেকে বার্তা:</b>\n\n{text_to_send}", parse_mode='HTML')
        bot.reply_to(message, f"✅ ইউজার <code>{target_id}</code> এর কাছে মেসেজ পাঠানো হয়েছে।", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/reply [User_ID] [মেসেজ]</code>", parse_mode='HTML')

@bot.message_handler(commands=['backup'])
def send_backup(message):
    current_admin = get_current_admin_id()
    if message.from_user.id != current_admin: return
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as doc:
                bot.send_document(current_admin, doc, caption=f"📁 ডাটাবেস ব্যাকআপ\nসময়: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        else:
            bot.reply_to(message, "⚠️ ডাটাবেস ফাইল পাওয়া যায়নি।")
    except Exception as e:
        bot.reply_to(message, f"⚠ ব্যাকআপ নিতে সমস্যা: {e}")

# ================= 🔘 ইউজার ভেরিফাই কলব্যাক হ্যান্ডেলার =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_fj_"))
def handle_force_join_verify(call):
    target_chat_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    
    req_channels = db_query("SELECT req_chat_id, req_link, req_title FROM force_channels WHERE target_chat_id = ?", (target_chat_id,), fetchall=True) or []
    
    missing = []
    for rc in req_channels:
        r_id, r_link, r_title = rc[0], rc[1], rc[2]
        try:
            cm = bot.get_chat_member(r_id, user_id)
            if cm.status not in ['creator', 'administrator', 'member']:
                missing.append(rc)
        except Exception:
            missing.append(rc)

    if not missing:
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল হয়েছে!", show_alert=True)
        bot.send_message(
            user_id, 
            f"🎉 <b>ভেরিফিকেশন সফল হয়েছে!</b>\n\nআপনি সবগুলো প্রয়োজনীয় চ্যানেলে জয়েন করেছেন। এখন আবার অফার চ্যানেলের জয়েন লিংকে চাপ দিয়ে জয়েন রিকোয়েস্ট পাঠান, সাথে সাথে এক্সেপ্ট করা হবে! 🚀", 
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলোতে জয়েন করেননি!", show_alert=True)
        missing_titles = "\n".join([f"• {m[3]}" for m in missing])
        bot.send_message(
            user_id, 
            f"⚠️ <b>ভেরিফিকেশন অসম্পূর্ণ!</b>\n\nআপনি এখনো নিচের চ্যানেলগুলোতে জয়েন করেননি:\n{missing_titles}\n\nসবগুলোতে জয়েন করে পুনরায় '🔄 ভেরিফাই করুন' বাটনে চাপ দিন।", 
            parse_mode='HTML'
        )

# ================= 🚪 জয়েন রিকোয়েস্ট হ্যান্ডেলার =================
@bot.chat_join_request_handler()
def handle_join_request(message: telebot.types.ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_name = message.chat.title or "প্রাইভেট চ্যানেল"
    now = datetime.now()
    
    # ১. টাইমার লকডাউন চেক
    chan_timer = db_query("SELECT expire_date FROM channel_timers WHERE chat_id = ?", (chat_id,), fetchone=True)
    if chan_timer:
        chan_expire_date = parse_date(chan_timer[0])
        if now >= chan_expire_date:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, f"🚫 <b>{chat_name}</b> চ্যানেলটি সাময়িকভাবে পুরোপুরি লক রাখা হয়েছে।", parse_mode='HTML')
            except Exception: pass
            return

    # ২. 🔗 কোর্স/ফোর্স জয়েন চ্যানেল চেক (অফার চ্যানেল কি না)
    req_channels = db_query("SELECT req_chat_id, req_link, req_title FROM force_channels WHERE target_chat_id = ?", (chat_id,), fetchall=True) or []
    if req_channels:
        all_joined = True
        missing_list = []
        for rc in req_channels:
            r_id = rc[0]
            try:
                cm = bot.get_chat_member(r_id, user_id)
                if cm.status not in ['creator', 'administrator', 'member']:
                    all_joined = False
                    missing_list.append(rc)
            except Exception:
                all_joined = False
                missing_list.append(rc)

        if all_joined:
            try:
                bot.approve_chat_join_request(chat_id, user_id)
                db_query("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id), commit=True)
                bot.send_message(user_id, f"🎉 <b>অভিনন্দন!</b>\n\nআপনি সকল প্রমোশনাল চ্যানেলে যুক্ত থাকায় <b>{chat_name}</b> চ্যানেলে আপনার এক্সেস এক্সেপ্ট করা হয়েছে।", parse_mode='HTML')
                return
            except Exception as e: print(f"Error approving: {e}")
        else:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                markup = InlineKeyboardMarkup()
                for rc in req_channels:
                    markup.add(InlineKeyboardButton(f"📢 {rc[2]}", url=rc[1]))
                markup.add(InlineKeyboardButton("🔄 ভেরিফাই করুন", callback_data=f"verify_fj_{chat_id}"))
                markup.add(InlineKeyboardButton("💳 সরাসরি এডমিনকে মেসেজ দিন", url="https://t.me/anisgazibd"))
                
                notice_msg = f"<b>🎁 বিশেষ অফার! ফ্রি প্রিমিয়াম এক্সেস 🎁</b>\n" \
                             f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                             f"📢 <b>অফার চ্যানেল:</b> <b>{chat_name}</b>\n\n" \
                             f"⚠️ <b>শর্তাবলি:</b> এই চ্যানেলে ফ্রিতে যুক্ত হতে হলে আগে নিচের প্রমোশনাল চ্যানেলগুলোতে জয়েন করতে হবে:\n\n" \
                             f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                             f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                             f"👉 <b>সহজ উপায়:</b>\n" \
                             f"১. নিচের প্রতিটি প্রমোশনাল চ্যানেলে ক্লিক করে জয়েন করুন।\n" \
                             f"২. জয়েন শেষে <b>'🔄 ভেরিফাই করুন'</b> বাটনে চাপ দিন।\n" \
                             f"৩. ভেরিফাই সফল হলে পুনরায় জয়েন লিংকে ক্লিক করে রিকোয়েস্ট পাঠান।"
                
                bot.send_message(user_id, notice_msg, parse_mode='HTML', reply_markup=markup)
                return
            except Exception as e: print(f"Error force join notice: {e}")

    # ৩. নরমাল চ্যানেল ফ্রি/পেইড মোড চেক
    mode_res = db_query("SELECT mode FROM channel_modes WHERE chat_id = ?", (chat_id,), fetchone=True)
    is_paid_channel = True
    if mode_res:
        if mode_res[0] == 'FREE': is_paid_channel = False
        elif mode_res[0] == 'PAID': is_paid_channel = True
    else:
        res = db_query("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'", fetchone=True)
        if res and res[0] == 'OFF': is_paid_channel = False

    if not is_paid_channel:
        try:
            bot.approve_chat_join_request(chat_id, user_id)
            db_query("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id), commit=True)
            bot.send_message(user_id, f"🎉 <b>অভিনন্দন!</b>\n\n<b>{chat_name}</b> চ্যানেলে ফ্রিতে যুক্ত করা হয়েছে।", parse_mode='HTML')
        except Exception as e: print(f"Error: {e}")
        return

    # ৪. সাবস্ক্রিপশন চেক
    result = db_query("SELECT expire_date FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if result:
        expire_date = parse_date(result[0])
        if now < expire_date:
            try:
                bot.approve_chat_join_request(chat_id, user_id)
                db_query("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id), commit=True)
                bot.send_message(user_id, f"🎉 <b>অভিনন্দন VIP মেম্বার!</b>\n\n✨ <b>{chat_name}</b> চ্যানেলে আপনার জয়েন রিকোয়েস্ট অনুমোদন করা হয়েছে।", parse_mode='HTML')
            except Exception as e: print(f"Error: {e}")
            return

    # সাবস্ক্রিপশন না থাকলে বার্তা
    try:
        bot.decline_chat_join_request(chat_id, user_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 সরাসরি এডমিনকে মেসেজ দিন", url="https://t.me/anisgazibd"))
        
        notice_msg = f"<b>✨ স্বাগতম! প্রিমিয়াম প্রাইভেট ভিআইপি চ্যানেল ✨</b>\n" \
                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                     f"📢 <b>চ্যানেল:</b> <b>{chat_name}</b>\n\n" \
                     f"⚠️ <b>বিশেষ বিজ্ঞপ্তি:</b> এই এক্সক্লুসিভ চ্যানেলে যুক্ত হতে একটি সক্রিয় VIP প্রিমিয়াম সাবস্ক্রিপশন প্রয়োজন।\n\n" \
                     f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                     f"💬 <b>এডমিনের সাথে কথা বলতে বা সাবস্ক্রিপশন নিতে:</b>\n\n" \
                     f"১. সরাসরি <b>এই বটের চ্যাটবক্সে যেকোনো বার্তা লিখে পাঠিয়ে দিন</b>, এডমিন আপনার উত্তর দেবেন।\n" \
                     f"২. অথবা সরাসরি টেলিগ্রামে কথা বলতে নিচের <b>'💳 সরাসরি এডমিনকে মেসেজ দিন'</b> বাটনে ক্লিক করুন।"
        
        bot.send_message(user_id, notice_msg, parse_mode='HTML', reply_markup=markup)
    except Exception: pass

# ================= 💬 সাপোর্ট মেসেজ হ্যান্ডেলার =================
@bot.message_handler(func=lambda message: message.from_user.id != get_current_admin_id(), content_types=['text', 'photo', 'voice', 'document'])
def handle_user_messages(message):
    user = message.from_user
    user_id = user.id
    current_admin = get_current_admin_id()
    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "নাই"

    header = f"<b>📩 নতুন ইনকামিং সাপোর্ট মেসেজ!</b>\n" \
             f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
             f"👤 <b>ইউজার:</b> {name} ({username})\n" \
             f"🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>"

    try:
        bot.send_message(current_admin, header, parse_mode='HTML')
        bot.forward_message(current_admin, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ <b>আপনার মেসেজটি এডমিনের নিকট পাঠানো হয়েছে!</b>\nঅনুগ্রহ করে এডমিন উত্তর দেওয়া পর্যন্ত অপেক্ষা করুন।", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ এডমিনের সাথে যোগাযোগ করতে সমস্যা হয়েছে।")

@bot.message_handler(func=lambda message: message.from_user.id == get_current_admin_id() and message.reply_to_message is not None)
def handle_admin_reply(message):
    replied_msg = message.reply_to_message
    target_user_id = None
    
    if replied_msg.forward_from:
        target_user_id = replied_msg.forward_from.id
    elif replied_msg.text and "ইউজার আইডি:" in replied_msg.text:
        try:
            line = [l for l in replied_msg.text.split('\n') if "ইউজার আইডি:" in l][0]
            target_user_id = int(line.split('<code>')[1].split('</code>')[0])
        except Exception: pass

    if target_user_id:
        try:
            bot.send_message(target_user_id, f"<b>💬 এডমিন থেকে উত্তর:</b>\n\n{message.text}", parse_mode='HTML')
            bot.reply_to(message, f"✅ ইউজার <code>{target_user_id}</code> এর কাছে উত্তর চলে গেছে!", parse_mode='HTML', reply_markup=get_admin_reply_keyboard())
        except Exception as e:
            bot.reply_to(message, f"❌ মেসেজ পাঠানো যায়নি: {e}")
    else:
        bot.reply_to(message, "⚠️ ইউজারের আইডি চেনা যায়নি। কাস্টম বাটন ব্যবহার করুন।", parse_mode='HTML')

# ================= ⏱️ ফাস্ট টাইমার চেকার ও অটো-ক্লিনআপ =================
def check_timers():
    now = datetime.now()
    
    # ১. চ্যানেল টাইমার টেস্ট ও অটো-কিক
    channel_timers = db_query("SELECT chat_id, expire_date FROM channel_timers", fetchall=True) or []
    for ct in channel_timers:
        chat_id = ct[0]
        expire_date = parse_date(ct[1])
        if now >= expire_date:
            users_in_chat = db_query("SELECT user_id FROM user_channels WHERE chat_id = ?", (chat_id,), fetchall=True) or []
            for u in users_in_chat:
                try: bot.ban_chat_member(chat_id, u[0])
                except Exception: pass
            
            db_query("DELETE FROM user_channels WHERE chat_id = ?", (chat_id,), commit=True)
            db_query("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,), commit=True)
            db_query("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'PAID')", (chat_id,), commit=True)

    # ২. ইউজার সাবস্ক্রিপশন টাইম টেস্ট
    users = db_query("SELECT user_id, expire_date FROM users", fetchall=True) or []
    for u in users:
        user_id = u[0]
        expire_date = parse_date(u[1])
        if now >= expire_date:
            user_chats = db_query("SELECT chat_id FROM user_channels WHERE user_id = ?", (user_id,), fetchall=True) or []
            for chat in user_chats:
                try: bot.ban_chat_member(chat[0], user_id)
                except Exception: pass
            db_query("DELETE FROM user_channels WHERE user_id = ?", (user_id,), commit=True)
            db_query("DELETE FROM users WHERE user_id = ?", (user_id,), commit=True)
            try: bot.send_message(user_id, "⚠️ আপনার সাবস্ক্রিপশনের মেয়াদ শেষ হওয়ায় আপনাকে চ্যানেল থেকে রিমুভ করা হয়েছে।")
            except Exception: pass

    # ৩. 🔄 ফোর্স জয়েন লিভ ট্র্যাকার (মেম্বার প্রমোশনাল চ্যানেল থেকে লিভ নিলে মূল চ্যানেল থেকে রিমুভ করা)
    user_entries = db_query("SELECT user_id, chat_id FROM user_channels", fetchall=True) or []
    for entry in user_entries:
        u_id, target_c_id = entry[0], entry[1]
        reqs = db_query("SELECT req_chat_id FROM force_channels WHERE target_chat_id = ?", (target_c_id,), fetchall=True) or []
        if reqs:
            for r in reqs:
                req_c_id = r[0]
                try:
                    cm = bot.get_chat_member(req_c_id, u_id)
                    if cm.status in ['left', 'kicked']:
                        try:
                            bot.ban_chat_member(target_c_id, u_id)
                        except Exception: pass
                        db_query("DELETE FROM user_channels WHERE user_id = ? AND chat_id = ?", (u_id, target_c_id), commit=True)
                        try:
                            bot.send_message(u_id, "⚠️ <b>মেম্বারশিপ বাতিল!</b>\n\nপ্রমোশনাল চ্যানেল থেকে লিভ নেওয়ায় আপনাকে অফার চ্যানেল থেকে রিমুভ করা হয়েছে।", parse_mode='HTML')
                        except Exception: pass
                        break
                except Exception: pass

def auto_backup():
    try:
        current_admin = get_current_admin_id()
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as doc:
                bot.send_document(current_admin, doc, caption=f"🔄 অটো ব্যাকআপ\nসময়: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e: print(f"Backup Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_timers, 'interval', minutes=1)
scheduler.add_job(auto_backup, 'interval', hours=24)
scheduler.start()

# ================= 🚀 বট রান =================
print("✅ আপডেট করা বটের সিস্টেম সফলভাবে চালু হয়েছে...!")
bot.infinity_polling(skip_pending=True)
