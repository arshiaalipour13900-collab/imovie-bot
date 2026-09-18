import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@imovie_arshia"
ADMIN_ID = 7310784586

FILES_FILE = "files.json"
STATS_FILE = "stats.json"


def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


files = load_json(FILES_FILE, {})
stats = load_json(STATS_FILE, {"users": [], "downloads": {}})


async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def membership_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📢 عضویت در کانال",
            url="https://t.me/imovie_arshia"
        )],
        [InlineKeyboardButton(
            "✅ بررسی عضویت",
            callback_data="check_membership"
        )]
    ])


def register_user(user_id):
    user_id = str(user_id)
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
        save_json(STATS_FILE, stats)


def add_download(number):
    number = str(number)
    if number not in stats["downloads"]:
        stats["downloads"][number] = 0
    stats["downloads"][number] += 1
    save_json(STATS_FILE, stats)


async def send_imovie(chat_id, number, context):
    number = str(number)

    if number not in files:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ این iMovie هنوز در ربات قرار نگرفته."
        )
        return

    await context.bot.send_document(
        chat_id=chat_id,
        document=files[number],
        caption=f"🎬 iMovie {number}\n\n❤️ @imovie_arshia"
    )

    add_download(number)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id)

    if not context.args:
        await update.message.reply_text(
            "سلام 👋\n\nبرای دریافت iMovie از لینک مخصوص همان iMovie وارد شو."
        )
        return

    number = context.args[0]

    if number not in files:
        await update.message.reply_text(
            "❌ این iMovie در ربات موجود نیست."
        )
        return

    context.user_data["imovie"] = number

    if not await is_member(context.bot, user.id):
        await update.message.reply_text(
            "🔒 برای دریافت این iMovie ابتدا در کانال عضو شو.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزن.",
            reply_markup=membership_keyboard()
        )
        return

    await send_imovie(user.id, number, context)


async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user

    number = context.user_data.get("imovie")

    if not number:
        await query.answer("❌ لینک iMovie پیدا نشد.", show_alert=True)
        return

    if not await is_member(context.bot, user.id):
        await query.answer(
            "❌ هنوز عضو کانال نیستی!",
            show_alert=True
        )
        return

    await query.answer()
    await query.message.reply_text(
        "✅ عضویت تأیید شد.\n🎬 در حال ارسال iMovie..."
    )

    await send_imovie(user.id, number, context)


async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("مثال:\n\n/save 25")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ روی فایل iMovie ریپلای کن و سپس بنویس:\n\n"
            f"/save {context.args[0]}"
        )
        return

    number = context.args[0]
    message = update.message.reply_to_message

    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    else:
        await update.message.reply_text(
            "❌ پیام باید فایل یا ویدیو باشد."
        )
        return

    files[number] = file_id
    save_json(FILES_FILE, files)

    await update.message.reply_text(
        f"✅ iMovie شماره {number} ذخیره شد."
    )


async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("مثال:\n/delete 25")
        return

    number = context.args[0]

    if number not in files:
        await update.message.reply_text(
            "❌ چنین iMovieای وجود ندارد."
        )
        return

    del files[number]
    save_json(FILES_FILE, files)

    await update.message.reply_text(
        f"🗑 iMovie شماره {number} حذف شد."
    )


async def make_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("مثال:\n/link 25")
        return

    number = context.args[0]
    me = await context.bot.get_me()

    link = f"https://t.me/{me.username}?start={number}"

    await update.message.reply_text(
        f"🔗 لینک iMovie {number}:\n\n{link}"
    )


async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = (
        "📊 آمار ربات\n\n"
        f"👥 کاربران: {len(stats['users'])}\n\n"
        "🎬 دانلودها:\n"
    )

    if not stats["downloads"]:
        text += "هنوز دانلودی ثبت نشده."
    else:
        for number, count in sorted(
            stats["downloads"].items(),
            key=lambda x: int(x[0])
        ):
            text += f"\niMovie {number}: {count}"

    await update.message.reply_text(text)


async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not files:
        await update.message.reply_text(
            "❌ هنوز هیچ iMovieای ذخیره نشده."
        )
        return

    text = "📁 iMovieهای ذخیره‌شده:\n\n"

    for number in sorted(files.keys(), key=lambda x: int(x)):
        text += f"🎬 {number}\n"

    await update.message.reply_text(text)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("save", save_file))
    app.add_handler(CommandHandler("delete", delete_file))
    app.add_handler(CommandHandler("link", make_link))
    app.add_handler(CommandHandler("stats", statistics))
    app.add_handler(CommandHandler("list", list_files))

    app.add_handler(
        CallbackQueryHandler(
            check_membership,
            pattern="^check_membership$"
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
