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
cursor.execute('''CREATE TABLE IF NOT EXISTS channel_modes (chat_id INTEGER PRIMARY KEY, mode TEXT)''')

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
        total_timers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM channel_modes WHERE mode = 'PAID'")
        paid_channels = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM channel_modes WHERE mode = 'FREE'")
        free_channels = cursor.fetchone()[0]
        
        msg = f"<b>👑 প্রফেশনাল ভিআইপি সাবস্ক্রিপশন প্যানেল</b>\n" \
              f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
              f"⚙️ <b>বর্তমান সিস্টেম স্ট্যাটাস:</b>\n" \
              f"• গ্লোবাল সাবস্ক্রিপশন মোড: <b>{'🟢 পেইড (ON)' if sub_mode == 'ON' else '🔴 ফ্রি (OFF)'}</b>\n" \
              f"• মোট অ্যাক্টিভ ইউজার: <b>{total_users} জন</b>\n" \
              f"• নির্দিষ্ট পেইড চ্যানেল: <b>{paid_channels} টি</b>\n" \
              f"• নির্দিষ্ট ফ্রি চ্যানেল: <b>{free_channels} টি</b>\n" \
              f"• নিবন্ধিত টাইমার চ্যানেল: <b>{total_timers} টি</b>\n\n" \
              f"<b>🛠️ চ্যানেল নির্দিষ্টকরণের কমান্ড:</b>\n" \
              f"• 🔴 <code>/set_paid [Channel_ID]</code> - চ্যানেলকে পেইড হিসেবে সেট করুন\n" \
              f"• 🟢 <code>/set_free [Channel_ID]</code> - চ্যানেলকে ফ্রি হিসেবে সেট করুন\n\n" \
              f"<b>🛠️ সার্বিক এডমিন কমান্ডসমূহ:</b>\n" \
              f"• 🔴 <code>/sub_on</code> - গ্লোবাল পেইড মোড চালু\n" \
              f"• 🟢 <code>/sub_off</code> - গ্লোবাল ফ্রি মোড চালু\n" \
              f"• 👤 <code>/add_user [User_ID] [দিন]</code> - ইউজার সাবস্ক্রিপশন যোগ করুন\n" \
              f"• ❌ <code>/del_user [User_ID]</code> - ইনস্ট্যান্ট ইউজার বাতিল ও চ্যানেল ব্যান\n" \
              f"• 🔒 <code>/set_channel_timer [Channel_ID] [দিন]</code> - চ্যানেল অটো-লক টাইমার\n" \
              f"• 🔓 <code>/unlock_channel [Channel_ID]</code> - লক চ্যানেল আনলক করুন\n" \
              f"• 💬 <code>/reply [User_ID] [মেসেজ]</code> - কাস্টম ইউজারকে মেসেজ পাঠান\n" \
              f"• 📁 <code>/backup</code> - ডাটাবেস ব্যাকআপ ডাউনলোড"
        bot.reply_to(message, msg, parse_mode='HTML')
    else:
        cursor.execute("SELECT expire_date FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📩 এডমিনের সাথে যোগাযোগ করুন", url="https://t.me/anisgazibd"))

        if result:
            exp = parse_date(result[0])
            msg = f"<b>👋 স্বাগতম, VIP মেম্বার!</b>\n\n" \
                  f"🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                  f"⏳ <b>মেয়াদের শেষ সময়:</b> <code>{exp.strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n" \
                  f"✅ আপনার প্রিমিয়াম সাবস্ক্রিপশন সক্রিয় রয়েছে।"
        else:
            msg = f"<b>👋 স্বাগতম!</b>\n\n" \
                  f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n" \
                  f"⚠️ <b>স্ট্যাটাস:</b> আপনার কোনো অ্যাক্টিভ সাবস্ক্রিপশন নেই।\n\n" \
                  f"💬 প্রিমিয়াম সাবস্ক্রিপশন নিতে নিচে যেকোনো তথ্য লিখে আমাদের মেসেজ দিন অথবা এডমিনের সাথে সরাসরি কথা বলুন।"
        bot.reply_to(message, msg, parse_mode='HTML', reply_markup=markup)

# ================= 🛡️ এডমিন কমান্ডস =================
@bot.message_handler(commands=['set_paid'])
def set_channel_paid(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        cursor.execute("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'PAID')", (chat_id,))
        conn.commit()
        bot.reply_to(message, f"🔴 <b>চ্যানেল মোড সেট: PAiD</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>\nএখন থেকে এই চ্যানেলে ঢুকতে সাবস্ক্রিপশন লাগবে।", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> ব্যবহার নিয়ম: <code>/set_paid [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['set_free'])
def set_channel_free(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        cursor.execute("INSERT OR REPLACE INTO channel_modes (chat_id, mode) VALUES (?, 'FREE')", (chat_id,))
        conn.commit()
        bot.reply_to(message, f"🟢 <b>চ্যানেল মোড সেট: FREE</b>\n📢 চ্যানেল আইডি: <code>{chat_id}</code>\nএখন থেকে এই চ্যানেলে যে কেউ ফ্রিতে যুক্ত হতে পারবে।", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> ব্যবহার নিয়ম: <code>/set_free [Channel_ID]</code>", parse_mode='HTML')

@bot.message_handler(commands=['sub_on'])
def sub_mode_on(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("UPDATE settings SET setting_value = 'ON' WHERE setting_key = 'sub_mode'")
    conn.commit()
    bot.reply_to(message, "✅ <b>গ্লোবাল সাবস্ক্রিপশন মোড ON!</b>", parse_mode='HTML')

@bot.message_handler(commands=['sub_off'])
def sub_mode_off(message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("UPDATE settings SET setting_value = 'OFF' WHERE setting_key = 'sub_mode'")
    conn.commit()
    bot.reply_to(message, "🔓 <b>গ্লোবাল সাবস্ক্রিপশন মোড OFF! (ফ্রি মোড)</b>", parse_mode='HTML')

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
        bot.reply_to(message, f"✅ <b>ইউজার সাবস্ক্রিপশন যোগ করা হয়েছে!</b>\n👤 আইডি: <code>{user_id}</code>\n⏳ মেয়াদ: {days} দিন", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/add_user [User_ID] [দিন]</code>", parse_mode='HTML')

# 📌 ইনস্ট্যান্ট চ্যানেল ব্যান ও রিমুভ সহ আপডেট করা /del_user কমান্ড
@bot.message_handler(commands=['del_user'])
def delete_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        user_id = int(message.text.split()[1])
        
        # ১. ডাটাবেস থেকে ইউজারের যুক্ত থাকা চ্যানেলগুলো খুঁজে বের করা
        cursor.execute("SELECT chat_id FROM user_channels WHERE user_id = ?", (user_id,))
        user_chats = cursor.fetchall()
        
        removed_count = 0
        # ২. চ্যানেলগুলো থেকে সাথে সাথে ইউজারকে ব্যান/রিমুভ করা
        for chat in user_chats:
            chat_id = chat[0]
            try:
                bot.ban_chat_member(chat_id, user_id)
                removed_count += 1
            except Exception: pass
            
        # ৩. ডাটাবেস থেকে মুছে ফেলা
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_channels WHERE user_id = ?", (user_id,))
        conn.commit()
        
        # ৪. ইউজারকে সাথে সাথে নোটিফিকেশন দেওয়া
        try:
            bot.send_message(user_id, "⚠️️ <b>আপনার সাবস্ক্রিপশন এডমিন কর্তৃক বাতিল করা হয়েছে এবং আপনাকে চ্যানেল থেকে রিমুভ করা হয়েছে।</b>", parse_mode='HTML')
        except Exception: pass

        bot.reply_to(
            message, 
            f"🗑️ <b>ইউজার সাবস্ক্রিপশন বাতিল ও ব্যান সফল!</b>\n"
            f"👤 আইডি: <code>{user_id}</code>\n"
            f"📢 চ্যানেল থেকে রিমুভ করা হয়েছে: <b>{removed_count} টি</b>", 
            parse_mode='HTML'
        )
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/del_user [User_ID]</code>", parse_mode='HTML')

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
        bot.reply_to(message, f"🚨 <b>চ্যানেল টাইমার সেট!</b>\n📢 চ্যানেল: <code>{chat_id}</code>\n⏳ সময়: {days} দিন পর চ্যানেলটি পুরো লক ও মেম্বার খালি হয়ে যাবে।", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/set_channel_timer [Channel_ID] [দিন]</code>", parse_mode='HTML')

@bot.message_handler(commands=['unlock_channel'])
def unlock_channel(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        chat_id = int(message.text.split()[1])
        cursor.execute("DELETE FROM channel_timers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        bot.reply_to(message, f"🔓 <b>চ্যানেল আনলক সফল!</b>\n📢 চ্যানেল: <code>{chat_id}</code>", parse_mode='HTML')
    except Exception:
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/unlock_channel [Channel_ID]</code>", parse_mode='HTML')

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
        bot.reply_to(message, "⚠️ <b>ভুল কমান্ড!</b> নিয়ম: <code>/reply [User_ID] [মেসেজ]</code>", parse_mode='HTML')

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
        bot.reply_to(message, f"⚠️️ ব্যাকআপ নিতে সমস্যা: {e}")

# ================= 🚪 জয়েন রিকোয়েস্ট হ্যান্ডেলার =================
@bot.chat_join_request_handler()
def handle_join_request(message: telebot.types.ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_name = message.chat.title or "প্রাইভেট চ্যানেল"
    now = datetime.now()
    
    # ১. চ্যানেল টাইমার টেস্ট
    cursor.execute("SELECT expire_date FROM channel_timers WHERE chat_id = ?", (chat_id,))
    chan_timer = cursor.fetchone()
    if chan_timer:
        chan_expire_date = parse_date(chan_timer[0])
        if now >= chan_expire_date:
            try:
                bot.decline_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, f"🚫 <b>{chat_name}</b> চ্যানেলটির ফ্রি/পেইড অফারের মেয়াদ শেষ। চ্যানেলটি সাময়িকভাবে লক রাখা হয়েছে।", parse_mode='HTML')
            except Exception: pass
            return

    # ২. চ্যানেল ভিত্তিক ফ্রি/পেইড মোড চেক
    cursor.execute("SELECT mode FROM channel_modes WHERE chat_id = ?", (chat_id,))
    mode_res = cursor.fetchone()
    
    is_paid_channel = True
    if mode_res:
        if mode_res[0] == 'FREE':
            is_paid_channel = False
        elif mode_res[0] == 'PAID':
            is_paid_channel = True
    else:
        cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'sub_mode'")
        res = cursor.fetchone()
        if res and res[0] == 'OFF':
            is_paid_channel = False

    # ৩. যদি চ্যানেল ফ্রি হয় -> অটো এক্সেপ্ট
    if not is_paid_channel:
        try:
            bot.approve_chat_join_request(chat_id, user_id)
            cursor.execute("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
            conn.commit()
            bot.send_message(user_id, f"🎉 <b>স্বাগতম!</b>\n\n<b>{chat_name}</b> চ্যানেলে আপনার অ্যাক্সেস ফ্রিতে মঞ্জুর করা হয়েছে।", parse_mode='HTML')
        except Exception as e: print(f"Error: {e}")
        return

    # ৪. চ্যানেল পেইড হলে ইউজার সাবস্ক্রিপশন চেক
    cursor.execute("SELECT expire_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        expire_date = parse_date(result[0])
        if now < expire_date:
            try:
                bot.approve_chat_join_request(chat_id, user_id)
                cursor.execute("INSERT INTO user_channels (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
                conn.commit()
                bot.send_message(user_id, f"✅ <b>স্বাগতম VIP মেম্বার!</b>\n\n<b>{chat_name}</b> চ্যানেলে আপনার জয়েন রিকোয়েস্ট সফলভাবে অ্যাপ্রুভ করা হয়েছে।", parse_mode='HTML')
            except Exception as e: print(f"Error: {e}")
            return

    # ৫. ইউজার সাবস্ক্রাইবড না থাকলে রিজেক্ট করা
    try:
        bot.decline_chat_join_request(chat_id, user_id)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 সাবস্ক্রিপশন নিতে এখানে ক্লিক করুন", url="https://t.me/anisgazibd"))
        
        notice_msg = f"<b>🔒 এটি একটি প্রিমিয়াম ভিআইপি চ্যানেল!</b>\n" \
                     f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
                     f"📢 <b>চ্যানেল:</b> {chat_name}\n\n" \
                     f"⚠️ <b>দুঃখিত!</b> এই চ্যানেলে যুক্ত হতে আপনার একটি সক্রিয় প্রিমিয়াম সাবস্ক্রিপশন প্রয়োজন।\n\n" \
                     f"🆔 <b>আপনার ইউজার আইডি:</b> <code>{user_id}</code>\n\n" \
                     f"💡 <b>কীভাবে সাবস্ক্রিপশন নেবেন?</b>\n" \
                     f"১. নিচে '💳 সাবস্ক্রিপশন নিতে ক্লিক করুন' বাটনে চাপ দিন অথবা বটের চ্যাটে লিখুন।\n" \
                     f"২. এডমিনকে আপনার ইউজার আইডিটি (<code>{user_id}</code>) পাঠান।\n" \
                     f"৩. সাবস্ক্রিপশন অ্যাক্টিভ করার পর পুনরায় লিংকে ক্লিক করে জয়েন করুন।"
        
        bot.send_message(user_id, notice_msg, parse_mode='HTML', reply_markup=markup)
    except Exception: pass

# ================= 💬 কাস্টমার সাপোর্ট ও লাইভ মেসেজিং সিস্টেম =================
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID, content_types=['text', 'photo', 'voice', 'document'])
def handle_user_messages(message):
    user = message.from_user
    user_id = user.id
    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "নাই"

    header = f"<b>📩 নতুন ইনকামিং সাপোর্ট মেসেজ!</b>\n" \
             f"━━━━━━━━━━━━━━━━━━━━━━━\n" \
             f"👤 <b>ইউজার:</b> {name} ({username})\n" \
             f"🆔 <b>ইউজার আইডি:</b> <code>{user_id}</code>\n" \
             f"💬 <b>বার্তা/প্রুফ:</b>"

    try:
        bot.send_message(ADMIN_ID, header, parse_mode='HTML')
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ <b>আপনার মেসেজটি সরাসরি এডমিনের কাছে ফরোয়ার্ড করা হয়েছে!</b>\nএডমিন উত্তর দেওয়া পর্যন্ত অপেক্ষা করুন।", parse_mode='HTML')
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
            bot.reply_to(message, f"✅ ইউজার <code>{target_user_id}</code> এর কাছে সফলভাবে উত্তর চলে গেছে!", parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"❌ মেসেজ পাঠানো যায়নি: {e}")
    else:
        bot.reply_to(message, "⚠️ ইউজারের আইডি চেনা যায়নি। কাস্টম কমান্ড ব্যবহার করুন: <code>/reply [User_ID] [মেসেজ]</code>", parse_mode='HTML')

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
            try: bot.send_message(user_id, "⚠️ আপনার সাবস্ক্রিপশনের মেয়াদ শেষ হওয়ায় আপনাকে প্রিমিয়াম চ্যানেল থেকে রিমুভ করা হয়েছে।")
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
print("✅ প্রো-সাবস্ক্রিপশন বট সফলভাবে আপডেট হয়ে চালু হয়েছে...!")
bot.infinity_polling()
