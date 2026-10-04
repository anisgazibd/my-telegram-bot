import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ================= ⚙️ কনফিগারেশন =================
BOT_TOKEN = '8919161117:AAEFTcbYlxbgduHDmKdcRKeszSY9-szepQ8'
ADMIN_ID = 2132743108  # আপনার টেলিগ্রাম আইডি

bot = telebot.TeleBot(BOT_TOKEN)

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ================= ⚙️ কনফিগারেশন =================
BOT_TOKEN = '8919161117:AAEFTcbYlxbgduHDmKdcRKeszSY9-szepQ8'
ADMIN_ID = 2132743108  # আপনার টেলিগ্রাম আইডি

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = 'pro_subscription.db'

# ================= 🗄️ থ্রেড-সেফ ডাটাবেস হেল্পার =================
def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """প্রতিটি রিকোয়েস্টে পৃথক ডাটাবেস কানেকশন তৈরি করে থ্রেড-লক মুক্ত রাখে"""
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
    cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('sub_mode', 'ON')")
    conn.commit()
    conn.close()

init_db()

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

# ================= 🎛️ এডমিন কিবোর্ড ও ড্যাশবোর্ড =================
def get_admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        InlineKeyboardButton("🔄 ড্যাশবোর্ড রিফ্রেশ", callback_data="adm_refresh"),
        InlineKeyboardButton("📋 চ্যানেল তালিকা", callback_data="adm_list_channels")
    )
    markup.add(
        InlineKeyboardButton("🔴 গ্লোবাল পেইড (ON)", callback_data="adm_sub_on"),
        InlineKeyboardButton("🟢 গ্লোবাল ফ্রি (OFF)", callback_data="adm_sub_off")
    )
    markup.add(
        InlineKeyboardButton("👤 ইউজার যোগ করুন", callback_data="adm_add_user"),
        InlineKeyboardButton("❌ ইউজার ব্যান/রিমুভ", callback_data="adm_del_user")
    )
    markup.add(
        InlineKeyboardButton("🔴 চ্যানেল পেইড মোড", callback_data="adm_set_paid"),
        InlineKeyboardButton("🟢 চ্যানেল ফ্রি মোড", callback_data="adm_set_free"),
        InlineKeyboardButton("⚙️ মোড রিসেট", callback_data="adm_reset_chan")
    )
    markup.add(
        InlineKeyboardButton("🔒 চ্যানেল টাইমার সেট", callback_data="adm_set_timer"),
        InlineKeyboardButton("🔓 চ্যানেল আনলক", callback_data="adm_unlock_chan")
    )
    markup.add(
        InlineKeyboardButton("💬 ইউজার রিপ্লাই", callback_data="adm_reply"),
        InlineKeyboardButton("📁 ব্যাকআপ ডাটাবেস", callback_data="adm_backup")
    )
    return markup

def render_dashboard_text():
    res = db_query("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'", fetchone=True)
    sub_mode = res[0] if res else 'ON'
    
    total_users = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    total_timers = db_query("SELECT COUNT(*) FROM channel_timers", fetchone=True)[0]
    paid_channels = db_query("SELECT COUNT(*) FROM channel_modes WHERE mode = 'PAID'", fetchone=True)[0]
    free_channels = db_query("SELECT COUNT(*) FROM channel_modes WHERE mode = 'FREE'", fetchone=True)[0]
    
    return f"<b>👑 প্রফেশনাল ভিআইপি সাবস্ক্রিপশন কন্ট্রোল প্যানেল</b>\n" \
           f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
           f"⚙️ <b>বর্তমান সিস্টেম স্ট্যাটাস:</b>\n" \
           f"• গ্লোবাল সাবস্ক্রিপশন মোড: <b>{'🟢 পেইড (ON)' if sub_mode == 'ON' else '🔴 ফ্রি (OFF)'}</b>\n" \
           f"• মোট অ্যাক্টিভ ভিআইপি ইউজার: <b>{total_users} জন</b>\n" \
           f"• নির্দিষ্ট পেইড চ্যানেল: <b>{paid_channels} টি</b>\n" \
           f"• নির্দিষ্ট ফ্রি চ্যানেল: <b>{free_channels} টি</b>\n" \
           f"• নিবন্ধিত টাইমার চ্যানেল: <b>{total_timers} টি</b>\n\n" \
           f"👇 <i>সহজে পরিচালনা করতে নিচের ইনটারেক্টিভ বাটনে ক্লিক করুন:</i>"

# ================= 🟢 স্টার্ট ও হেল্প কমান্ড =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        msg = render_dashboard_text()
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=get_admin_keyboard())
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
                  f"✅ <b>স্ট্যাটাস:</b> আপনার প্রিমিয়াম ভিআইপি সাবস্ক্রিপশন সফলভাবে সক্রিয় রয়েছে। 💎"
        else:
            msg = f"<b>👋 স্বাগতম, {message.from_user.first_name}!</b>\n" \
                  f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
                  f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                  f"📊 <b>বর্তমান স্ট্যাটাস:</b> 🔴 কোনো অ্যাক্টিভ সাবস্ক্রিপশন নেই\n\n" \
                  f"✨ আমাদের প্রিমিয়াম ভিআইপি চ্যানেলে যুক্ত হতে একটি অ্যাক্টিভ সাবস্ক্রিপশন প্রয়োজন।\n\n" \
                  f"💬 সাবস্ক্রিপশন নিতে নিচে বটের চ্যাটে সরাসরি মেসেজ পাঠান।"
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=markup)

# ================= 🛡 চ্যানেল ও সিস্টেম টেক্সট কমান্ডসমূহ =================
@bot.message_handler(commands=['list_channels', 'channels'])
def list_channels(message):
    if message.from_user.id != ADMIN_ID: return
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
        
        bot.reply_to(message, msg, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ সমস্যা হয়েছে: {e}")

@bot.message_handler(commands=['del_channel', 'reset_channel'])
def delete_channel_config(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        db_query("DELETE FROM channel_modes WHERE chat_id = ?", (chat_id,), commit=True)
        db_query("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,), commit=True)
        bot.reply_to(message, f"⚙️ <b>চ্যানেল রিসেট সফল!</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/del_channel [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_paid'])
def set_channel_paid(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        db_query("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'PAID')", (chat_id,), commit=True)
        bot.reply_to(message, f"🔴 <b>চ্যানেল মোড সেট: PAID</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_paid [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_free'])
def set_channel_free(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        db_query("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'FREE')", (chat_id,), commit=True)
        bot.reply_to(message, f"🟢 <b>চ্যানেল মোড সেট: FREE</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_free [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['sub_on'])
def sub_mode_on(message):
    if message.from_user.id != ADMIN_ID: return
    db_query("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'", commit=True)
    bot.reply_to(message, "✅ <b>গ্লোবাল সাবস্ক্রিপশন মোড ON!</b>", parse_mode='HTML')

@bot.message_handler(commands=['sub_off'])
def sub_mode_off(message):
    if message.from_user.id != ADMIN_ID: return
    db_query("UPDATE settings SET setting_value = 'OFF' WHERE setting_key = 'sub_mode'", commit=True)
    bot.reply_to(message, "🔓 <b>গ্লোবাল সাবস্ক্রিপশন মোড OFF! (ফ্রি মোড)</b>", parse_mode='HTML')

@bot.message_handler(commands=['add_user'])
def add_user_time(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        db_query("INSERT OR REPLACE INTO users (user_id, expire_date) VALUES (?, ?)", (user_id, expire_date), commit=True)
        bot.reply_to(message, f"✅ <b>ইউজার সাবস্ক্রিপশন যোগ করা হয়েছে!</b>\n👤 আইডি: <code>{user_id}</code>\n⏳ মেয়াদ: <b>{days} দিন</b>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/add_user [User_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['del_user'])
def delete_user(message):
    if message.from_user.id != ADMIN_ID: return
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

        bot.reply_to(message, f"🗑️ <b>ইউজার সাবস্ক্রিপশন বাতিল ও ব্যান সফল!</b>\n👤 আইডি: <code>{user_id}</code>\n📢 রিমুভ চ্যানেল: <b>{removed_count} টি</b>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/del_user [User_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_channel_timer'])
def set_channel_timer(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        chat_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        db_query("INSERT OR REPLACE INTO channel_timers (chat_id, expire_date) VALUES (?, ?)", (chat_id, expire_date), commit=True)
        bot.reply_to(message, f"🚨 <b>চ্যানেল টাইমার সেট!</b>\n📢 চ্যানেল: <code>{chat_id}</code>\n⏳ সময়: <b>{days} দিন</b>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/set_channel_timer [Channel_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['unlock_channel'])
def unlock_channel(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        db_query("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,), commit=True)
        bot.reply_to(message, f"🔓 <b>চ্যানেল আনলক সফল!</b>\n📢 চ্যানেল: <code>{chat_id}</code>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/unlock_channel [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['reply'])
def admin_manual_reply(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split(maxsplit=2)
        target_id = int(parts[1])
        text_to_send = parts[2]
        bot.send_message(target_id, f"<b>💬 এডমিন থেকে বার্তা:</b>\n\n{text_to_send}", parse_mode='HTML')
        bot.reply_to(message, f"✅ ইউজার <code>{target_id}</code> এর কাছে মেসেজ পাঠানো হয়েছে।", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল নিয়ম!</b> ব্যবহার: <code>/reply [User_ID] [মেসেজ]</code>", parse_mode='HTML')

@bot.message_handler(commands=['backup'])
def send_backup(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as doc:
                bot.send_document(ADMIN_ID, doc, caption=f"📁 ডাটাবেস ব্যাকআপ\nসময়: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        else:
            bot.reply_to(message, "⚠️ ডাটাবেস ফাইল পাওয়া যায়নি।")
    except Exception as e:
        bot.reply_to(message, f"⚠ ব্যাকআপ নিতে সমস্যা: {e}")

# ================= 🔘 বাটন ক্লিক হ্যাণ্ডেলার =================
@bot.callback_query_handler(func=lambda call: call.from_user.id == ADMIN_ID)
def handle_admin_callbacks(call):
    if call.data == "adm_refresh":
        msg = render_dashboard_text()
        try:
            bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=get_admin_keyboard())
            bot.answer_callback_query(call.id, "🔄 রিফ্রেশ করা হয়েছে!")
        except Exception:
            bot.answer_callback_query(call.id, "আপডেটেড আছে!")

    elif call.data == "adm_list_channels":
        bot.answer_callback_query(call.id)
        list_channels(call.message)

    elif call.data == "adm_sub_on":
        db_query("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'", commit=True)
        bot.answer_callback_query(call.id, "✅ গ্লোবাল পেইড ON!")
        msg = render_dashboard_text()
        try: bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=get_admin_keyboard())
        except Exception: pass

    elif call.data == "adm_sub_off":
        db_query("UPDATE settings SET setting_value = 'OFF' WHERE setting_key = 'sub_mode'", commit=True)
        bot.answer_callback_query(call.id, "🔓 গ্লোবাল ফ্রি OFF!")
        msg = render_dashboard_text()
        try: bot.edit_message_text(msg, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML', reply_markup=get_admin_keyboard())
        except Exception: pass

    elif call.data == "adm_backup":
        bot.answer_callback_query(call.id, "📁 ব্যাকআপ তৈরি হচ্ছে...")
        send_backup(call.message)

    elif call.data == "adm_add_user":
        msg = bot.send_message(call.message.chat.id, "👤 <b>ইউজার আইডি এবং দিন লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789 30</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/add_user {m.text}"), add_user_time(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_del_user":
        msg = bot.send_message(call.message.chat.id, "❌ <b>ব্যান/বাতিল করতে চাওয়া আইডি লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/del_user {m.text}"), delete_user(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_set_paid":
        msg = bot.send_message(call.message.chat.id, "🔴 <b>পেইড চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_paid {m.text}"), set_channel_paid(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_set_free":
        msg = bot.send_message(call.message.chat.id, "🟢 <b>ফ্রি চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_free {m.text}"), set_channel_free(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_reset_chan":
        msg = bot.send_message(call.message.chat.id, "⚙️ <b>রিসেট চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/del_channel {m.text}"), delete_channel_config(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_set_timer":
        msg = bot.send_message(call.message.chat.id, "🔒 <b>চ্যানেল আইডি ও দিন লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890 7</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/set_channel_timer {m.text}"), set_channel_timer(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_unlock_chan":
        msg = bot.send_message(call.message.chat.id, "🔓 <b>আনলক চ্যানেল আইডি দিন:</b>\n\n<i>উদাহরণ:</i> <code>-1001234567890</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/unlock_channel {m.text}"), unlock_channel(m)])
        bot.answer_callback_query(call.id)

    elif call.data == "adm_reply":
        msg = bot.send_message(call.message.chat.id, "💬 <b>ইউজার আইডি ও মেসেজ লিখুন:</b>\n\n<i>উদাহরণ:</i> <code>123456789 হ্যালো</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, lambda m: [setattr(m, 'text', f"/reply {m.text}"), admin_manual_reply(m)])
        bot.answer_callback_query(call.id)

# ================= 🚪 জয়েন রিকোয়েস্ট হ্যান্ডেলার =================
@bot.chat_join_request_handler()
def handle_join_request(message: telebot.types.ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_name = message.chat.title or "প্রাইভেট চ্যানেল"
    now = datetime.now()
    
    chan_timer = db_query("SELECT expire_date FROM channel_timers WHERE chat_id = ?", (chat_id,), fetchone=True)
    if chan_timer:
        chan_expire_date = parse_date(chan_timer[0])
        if now >= chan_expire_date:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, f"🚫 <b>{chat_name}</b> চ্যানেলটি সাময়িকভাবে লক রাখা হয়েছে।", parse_mode='HTML')
            except Exception: pass
            return

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

    try:
        bot.decline_chat_join_request(chat_id, user_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 সাবস্ক্রিপশন নিতে ক্লিক করুন", url="https://t.me/anisgazibd"))
        
        notice_msg = f"<b>✨ স্বাগতম! প্রাইভেট ভিআইপি চ্যানেল ✨</b>\n" \
                     f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                     f"📢 <b>চ্যানেল:</b> <b>{chat_name}</b>\n\n" \
                     f"⚠️ এই এক্সক্লুসিভ চ্যানেলে যুক্ত হতে একটি সক্রিয় VIP প্রিমিয়াম সাবস্ক্রিপশন প্রয়োজন।\n\n" \
                     f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>"
        
        bot.send_message(user_id, notice_msg, parse_mode='HTML', reply_markup=markup)
    except Exception: pass

# ================= 💬 সাপোর্ট মেসেজ হ্যান্ডেলার =================
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID, content_types=['text', 'photo', 'voice', 'document'])
def handle_user_messages(message):
    user = message.from_user
    user_id = user.id
    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "নাই"

    header = f"<b>📩 নতুন ইনকামিং মেসেজ!</b>\n" \
             f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
             f"👤 <b>ইউজার:</b> {name} ({username})\n" \
             f"🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>"

    try:
        bot.send_message(ADMIN_ID, header, parse_mode='HTML')
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ <b>আপনার মেসেজটি এডমিনের নিকট পাঠানো হয়েছে!</b>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ এডমিনের সাথে যোগাযোগ করতে সমস্যা হয়েছে।")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.reply_to_message is not None)
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
            bot.reply_to(message, f"✅ ইউজার <code>{target_user_id}</code> এর কাছে উত্তর চলে গেছে!", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"❌ মেসেজ পাঠানো যায়নি: {e}")
    else:
        bot.reply_to(message, "⚠️ ইউজারের আইডি চেনা যায়নি। কাস্টম কমান্ড ব্যবহার করুন: <code>/reply [User_ID] [মেসেজ]</code>", parse_mode='HTML')

# ================= ⏱️ ব্যাকগ্রাউন্ড চেকার =================
def check_timers():
    now = datetime.now()
    
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

def auto_backup():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as doc:
                bot.send_document(ADMIN_ID, doc, caption=f"🔄 অটো ব্যাকআপ\nসময়: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e: print(f"Backup Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_timers, 'interval', minutes=1)
scheduler.add_job(auto_backup, 'interval', hours=24)
scheduler.start()

# ================= 🚀 বট রান =================
print("✅ বট সফলভাবে চালু হয়েছে এবং নতুন মেসেজ গ্রহণ করছে...!")
bot.infinity_polling(skip_pending=True)
