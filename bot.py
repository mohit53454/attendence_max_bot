import os
import cv2
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from attendance import extract_absent_rolls, TOTAL_STUDENTS

BOT_TOKEN = os.getenv("BOT_TOKEN")  # 🔴 IMPORTANT

sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sessions[update.effective_user.id] = {}
    await update.message.reply_text(
        "Send *YESTERDAY* attendance screenshot 📸",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()

    os.makedirs("temp", exist_ok=True)

    if "yesterday" not in sessions[uid]:
        path = f"temp/{uid}_yesterday.jpg"
        await file.download_to_drive(path)
        sessions[uid]["yesterday"] = path
        await update.message.reply_text(
            "Now send *TODAY* attendance screenshot 📸",
            parse_mode="Markdown"
        )
        return

    if "today" not in sessions[uid]:
        path = f"temp/{uid}_today.jpg"
        await file.download_to_drive(path)
        sessions[uid]["today"] = path

        y_img = cv2.imread(sessions[uid]["yesterday"])
        t_img = cv2.imread(sessions[uid]["today"])

        absent_y = extract_absent_rolls(y_img)
        absent_t = extract_absent_rolls(t_img)

        present_to_absent = sorted(absent_t - absent_y)
        absent_to_present = sorted(absent_y - absent_t)

        absent_today = len(absent_t)
        present_today = TOTAL_STUDENTS - absent_today

        report = (
            "====== ATTENDANCE REPORT ======\n\n"
            f"Total Students   : {TOTAL_STUDENTS}\n"
            f"Present Today    : {present_today}\n"
            f"Absent Today     : {absent_today}\n\n"
            f"Present → Absent : {present_to_absent}\n"
            f"Absent → Present : {absent_to_present}\n\n"
            "=============================="
        )

        await update.message.reply_text(
            f"```\n{report}\n```",
            parse_mode="Markdown"
        )

        os.remove(sessions[uid]["yesterday"])
        os.remove(sessions[uid]["today"])
        sessions.pop(uid)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("🚀 Bot running on Railway (24/7)")
    app.run_polling()

if __name__ == "__main__":
    main()
