import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from pymongo import MongoClient

# Logging သတ်မှတ်ခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB ချိတ်ဆက်ခြင်း
MONGO_URI = "mongodb+srv://dxstr47_db_user:xDs62AdrRbDHhgFH@cluster0.fso9l3s.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["teletv_db"]
movies_collection = db["movies"]

# Telegram Settings
BOT_TOKEN = "8761072743:AAG9klC1yLxEUAttBTBO1klBW9LgOz2WRLM"
CHANNEL_ID = "-1004409384544" # ဥပမာ - @my_movie_channel (သို့မဟုတ် -100xxxxxxxxxx ID)

# Conversation States
TITLE, YEAR, RATING, SYNOPSIS, POSTER, VIDEO = range(6)

async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🎬 Movie တင်ခြင်းစနစ်မှ ကြိုဆိုပါတယ်။\n\nMovie Title (ဇာတ်ကားအမည်) ကို ရိုက်ထည့်ပါ။")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['title'] = update.message.text
    await update.message.reply_text("📅 ထွက်ရှိသည့်နှစ် (Year) ကို ရိုက်ထည့်ပါ (ဥပမာ - 2025)။")
    return YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['year'] = update.message.text
    await update.message.reply_text("⭐ IMDb Rating ကို ရိုက်ထည့်ပါ (ဥပမာ - 7.5)။")
    return RATING

async def get_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['rating'] = update.message.text
    await update.message.reply_text("📝 ဇာတ်လမ်းအကျဉ်း (Synopsis / Review) ကို ရိုက်ထည့်ပါ။")
    return SYNOPSIS

async def get_synopsis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['description'] = update.message.text
    await update.message.reply_text("🖼️ Movie Poster ရဲ့ Direct Image URL (ပုံလင့်ခ်) ကို ထည့်ပေးပါ။\n(မှတ်ချက် - Internet ပေါ်ရှိ ပုံလင့်ခ် တစ်ခုခု)")
    return POSTER

async def get_poster(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['poster_url'] = update.message.text
    await update.message.reply_text("📹 ယခု ဇာတ်ကား၏ ဗီဒီယိုဖိုင် (Video File) ကို ပို့ပေးပါ။ Channel သို့ Auto တင်ပေးမည် ဖြစ်သည်။")
    return VIDEO

async def get_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.video:
        await update.message.reply_text("ကျေးဇူးပြု၍ ဗီဒီယိုဖိုင် အမျိုးအစား စစ်စစ်ကိုသာ ပို့ပေးပါ။")
        return VIDEO
    
    status_msg = await update.message.reply_text("⏳ ဗီဒီယိုကို Channel သို့ တင်နေပါသည်... ခေတ္တစောင့်ပါ။")
    video_file_id = update.message.video.file_id
    
    try:
        # ၁. Channel သို့ Video Auto Upload တင်ခြင်း
        caption_text = f"🎬 {context.user_data['title']} ({context.user_data['year']})\n⭐ Rating: {context.user_data['rating']}\n\n🍿 Enjoy Your Movie!"
        channel_post = await context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=video_file_id,
            caption=caption_text
        )
        
        # Telegram Link ဖန်တီးခြင်း
        channel_username = CHANNEL_ID.replace("@", "")
        telegram_link = f"https://t.me/{channel_username}/{channel_post.message_id}"
        
        # Web URL အတွက် Unique Slug ပြုလုပ်ခြင်း
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', context.user_data['title']).lower().replace(" ", "-")
        slug = f"{clean_title}-{context.user_data['year']}"

        # ၂. Database ထဲသို့ Data သိမ်းဆည်းခြင်း
        movie_data = {
            "title": context.user_data['title'],
            "year": context.user_data['year'],
            "rating": context.user_data['rating'],
            "description": context.user_data['description'],
            "poster_url": context.user_data['poster_url'],
            "telegram_link": telegram_link,
            "slug": slug
        }
        
        movies_collection.insert_one(movie_data)
        
        await status_msg.edit_text(f"✅ အောင်မြင်စွာ တင်ပြီးပါပြီ!\n🌐 Website တွင် ဝင်ရောက်ကြည့်ရှုနိုင်ပါပြီ။\n🔗 Link: {telegram_link}")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ ချို့ယွင်းချက်ရှိသွားပါသည်- {str(e)}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", start_add)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_rating)],
            SYNOPSIS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_synopsis)],
            POSTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_poster)],
            VIDEO: [MessageHandler(filters.VIDEO, get_video)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
