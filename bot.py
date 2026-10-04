import telebot
import sqlite3
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# ================= ⚙️ কনফিগারেশন =================
BOT_TOKEN = '8919161117:AAEFTcbYlxbgduHDmKdcRKeszSY9-szepQ8'
ADMIN_ID = 2132743108  # আপনার টেলিগ্রাম আইডি

bot = telebot.TeleBot(BOT_TOKEN)

# ================= 🗄️ ডাটাবেস সেটআপ =================
DB_FILE = 'pro_subscription.db'
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

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

# টেবিল তৈরি
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expire_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS user_channels (user_id INTEGER, chat_id INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS channel_timers (chat_id INTEGER PRIMARY KEY, expire_date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS settings (setting_key TEXT PRIMARY KEY, setting_value TEXT)''')

cursor.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('sub_mode', 'ON')")
conn.commit()

# ================= 🟢 স্টার্ট ও হেল্প কমান্ড (প্রফেশনাল ড্যাশবোর্ড) =================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'")
        res = cursor.fetchone()
        sub_mode = res[0] if res else 'ON'
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM channel_timers")
        total_channels = cursor.fetchone()[0]
        
        msg = f"<b>👑 প্রফেশনাল ভিআইপি সাবস্ক্রিপশন প্যানেল</b>\n" \
              f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
              f"⚙️ <b>বর্তমান সিস্টেম স্ট্যাটাস:</b>\n" \
              f"• সাবস্ক্রিপশন মোড: <b>{'🟢 পেইড (ON)' if sub_mode == 'ON' else '🔴 ফ্রি (OFF)'}</b>\n" \
              f"• মোট অ্যাক্টিভ ইউজার: <b>{total_users} জন</b>\n" \
              f"• নিবন্ধিত টাইমার চ্যানেল: <b>{total_channels} টি</b>\n\n" \
              f"<b>🛠️ এডমিন কমান্ডসমূহ:</b>\n" \
              f"• 🟢 <code>/sub_on</code> - পেইড সাবস্ক্রিপশন মোড চালু করুন\n" \
              f"• 🔴 <code>/sub_off</code> - ফ্রি মোড চালু করুন (অটো জয়েন)\n" \
              f"• 👤 <code>/add_user [User_ID] [দিন]</code> - ইউজার সাবস্ক্রিপশন যোগ করুন\n" \
              f"• 🔒 <code>/set_channel_timer [Channel_ID] [দিন]</code> - চ্যানেল অটো-লক টাইমার সেট করুন\n" \
              f"• 🔓 <code>/unlock_channel [Channel_ID]</code> - লক হওয়া চ্যানেল আনলক করুন\n" \
              f"• 📁 <code>/backup</code> - ডাটাবেসের সেফটি ব্যাকআপ ফাইল সংগ্রহ করুন\n\n" \
              f"<b>📖 প্র্যাক্টিক্যাল গাইডলাইন:</b>\n" \
              f"১. প্রাইভেট চ্যানেলে বটকে <b>Admin</b> করে 'Ban Users' & 'Invite Users' পারমিশন দিন।\n" \
              f"২. চ্যানেলের Invite Link সেটিংসে <b>Request Admin Approval</b> চালু রাখুন।\n" \
              f"৩. ইউজার এড করতে <code>/add_user 12345678 30</code> লিখে সেন্ড করুন।"
        bot.reply_to(message, msg, parse_mode='HTML')
    else:
        cursor.execute("SELECT expire_date FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            exp = parse_date(result[0])
            msg = f"<b>👋 স্বাগতম!</b>\n\n" \
                  f"🆔 আপনার ইউজার আইডি: <code>{user_id}</code>\n" \
                  f"⏳ সাবস্ক্রিপশনের মেয়াদ: <b>{exp.strftime('%Y-%m-%d %H:%M:%S')}</b>\n\n" \
                  f"✅ আপনার অ্যাক্টিভ সাবস্ক্রিপশন রয়েছে। চ্যানেলের প্রাইভেট লিংকে ক্লিক করে যুক্ত হন।"
        else:
            msg = f"<b>👋 স্বাগতম!</b>\n\n" \
                  f"🆔 আপনার ইউজার আইডি: <code>{user_id}</code>\n" \
                  f"⚠️ <b>অবস্থা:</b> আপনার কোনো সক্রিয় সাবস্ক্রিপশন নেই।\n\n" \
                  f"চ্যানেলে প্রবেশ করার জন্য এডমিনের সাথে যোগাযোগ করে সাবস্ক্রিপশন নিশ্চিত করুন।"
        bot.reply_to(message, msg, parse_mode='HTML')

# ================= 🛡️ এডমিন কমান্ডস =================
@bot.message_handler(commands=['sub_on'])
def sub_mode_on(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'")
    conn.commit()
    bot.reply_to(message, "✅ <b>সাবস্ক্রিপশন মোড ON!</b>\nএখন থেকে শুধু মেয়াদ থাকা ইউজাররাই চ্যানেলে ঢুকতে পারবে।", parse_mode='HTML')

@bot.message_handler(commands=['sub_off'])
def sub_mode_off(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("UPDATE settings SET setting_value = 'OFF' WHERE setting_key = 'sub_mode'")
    conn.commit()
    bot.reply_to(message, "🔓 <b>সাবস্ক্রিপশন মোড OFF! (ফ্রি মোড)</b>\nএখন থেকে যে কেউ রিকোয়েস্ট দিলে বট স্বয়ংক্রিয়ভাবে তাকে ফ্রিতে এক্সেপ্ট করে নেবে।", parse_mode='HTML')

@bot.message_handler(commands=['add_user'])
def add_user_time(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        user_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, expire_date) VALUES (?, ?)", (user_id, expire_date))
        conn.commit()
        bot.reply_to(message, f"✅ <b>ইউজার সাবস্ক্রিপশন আপডেট!</b>\n👤 আইডি: <code>{user_id}</code>\n⏳ মেয়াদ: {days} দিন", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/add_user [User_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_channel_timer'])
def set_channel_timer(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        chat_id = int(parts[1])
        days = int(parts[2])
        expire_date = (datetime.now() + timedelta(days=days)).isoformat()
        cursor.execute("INSERT OR REPLACE INTO channel_timers (chat_id, expire_date) VALUES (?, ?)", (chat_id, expire_date))
        conn.commit()
        bot.reply_to(message, f"🚨 <b>চ্যানেল টাইমার সেট!</b>\n📢 চ্যানেল: <code>{chat_id}</code>\n⏳ সময়: {days} দিন পর চ্যানেলটি পুরোপুরি লক হয়ে যাবে।", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/set_channel_timer [Channel_ID] [দিন]</code>", parse_mode='HTML')

# 📌 নতুন সংযুক্ত: লক চ্যানেল আনলক কমান্ড
@bot.message_handler(commands=['unlock_channel'])
def unlock_channel(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        chat_id = int(parts[1])
        cursor.execute("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        bot.reply_to(message, f"🔓 <b>চ্যানেল আনলক সফল!</b>\n📢 চ্যানেল: <code>{chat_id}</code>\nটাইমার মুছে ফেলা হয়েছে এবং চ্যানেলটি এখন সম্পূর্ণ সচল।", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/unlock_channel [Channel_ID]</code>", parse_mode='HTML')

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
        bot.reply_to(message, f"⚠️ ব্যাকআপ নিতে সমস্যা হয়েছে: {e}")

# ================= 🚪 জয়েন রিকোয়েস্ট হ্যান্ডেলার =================
@bot.chat_join_request_handler()
def handle_join_request(message: telebot.types.ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_name = message.chat.title or "চ্যানেল"
    now = datetime.now()
    
    cursor.execute("SELECT expire_date FROM channel_timers WHERE chat_id = ?", (chat_id,))
    chan_timer = cursor.fetchone()
    if chan_timer:
        chan_expire_date = parse_date(chan_timer[0])
        if now >= chan_expire_date:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, f"🚫 <b>{chat_name}</b> চ্যানেলটির মেয়াদ শেষ এবং এটি স্থায়ীভাবে বন্ধ করে দেওয়া হয়েছে।", parse_mode='HTML')
            except Exception: pass
            return

    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'")
    res = cursor.fetchone()
    sub_mode = res[0] if res else 'ON'

    if sub_mode == 'OFF':
        try:
            bot.approve_chat_join_request(chat_id, user_id)
            cursor.execute("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
            conn.commit()
            bot.send_message(user_id, f"🎉 <b>{chat_name}</b> চ্যানেলে আপনাকে ফ্রিতে স্বাগতম!", parse_mode='HTML')
        except Exception as e: print(f"Error: {e}")
        return

    cursor.execute("SELECT expire_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        expire_date = parse_date(result[0])
        if now < expire_date:
            try:
                bot.approve_chat_join_request(chat_id, user_id)
                cursor.execute("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
                conn.commit()
                bot.send_message(user_id, f"✅ <b>{chat_name}</b> চ্যানেলে আপনার জয়েন রিকোয়েস্ট এক্সেপ্ট করা হয়েছে!", parse_mode='HTML')
            except Exception as e: print(f"Error: {e}")
        else:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, "❌ আপনার সাবস্ক্রিপশনের মেয়াদ শেষ হয়ে গেছে।")
            except Exception: pass
    else:
        try:
            bot.decline_chat_join_request(chat_id, user_id)
            bot.send_message(user_id, "❌ আপনার কোনো অ্যাক্টিভ সাবস্ক্রিপশন নেই।")
        except Exception: pass

# ================= ⏱️ টাইমার চেকার ও অটো-ব্যান =================
def check_timers():
    now = datetime.now()
    
    cursor.execute("SELECT chat_id, expire_date FROM channel_timers")
    channel_timers = cursor.fetchall()
    for ct in channel_timers:
        chat_id = ct[0]
        expire_date = parse_date(ct[1])
        if now >= expire_date:
            cursor.execute("SELECT user_id FROM user_channels WHERE chat_id = ?", (chat_id,))
            users_in_chat = cursor.fetchall()
            
            for u in users_in_chat:
                try: bot.ban_chat_member(chat_id, u[0])
                except Exception: pass
            
            cursor.execute("DELETE FROM user_channels WHERE chat_id = ?", (chat_id,))
            conn.commit()

    cursor.execute("SELECT user_id, expire_date FROM users")
    users = cursor.fetchall()
    for u in users:
        user_id = u[0]
        expire_date = parse_date(u[1])
        if now >= expire_date:
            cursor.execute("SELECT chat_id FROM user_channels WHERE user_id = ?", (user_id,))
            for chat in cursor.fetchall():
                try: bot.ban_chat_member(chat[0], user_id)
                except Exception: pass
            cursor.execute("DELETE FROM user_channels WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            try: bot.send_message(user_id, "⚠️ মেয়াদ শেষ হওয়ায় আপনাকে চ্যানেল থেকে রিমুভ করা হয়েছে।")
            except Exception: pass
            try: bot.send_message(ADMIN_ID, f"🔔 ইউজার <code>{user_id}</code> এর মেয়াদ শেষ হওয়ায় রিমুভ করা হয়েছে।", parse_mode='HTML')
            except Exception: pass

# ================= 🔄 অটোমেটিক ব্যাকআপ সিস্টেম =================
def auto_backup():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'rb') as doc:
                bot.send_document(ADMIN_ID, doc, caption=f"🔄 অটো ডেইলি ব্যাকআপ\nসময়: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e: print(f"Backup Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_timers, 'interval', minutes=1)
scheduler.add_job(auto_backup, 'interval', hours=24)
scheduler.start()

# ================= 🚀 বট চালু =================
print("✅ প্রো-সাবস্ক্রিপশন বট সফলভাবে চালু হয়েছে...!")
bot.infinity_polling()
