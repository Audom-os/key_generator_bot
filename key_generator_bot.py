# ផ្ញើ Key ទៅអ្នកប្រើប្រាស់
    message = (
        f"🎉 បង្កើត License Key ជោគជ័យ!**\n\n"
        f"🔸 **Machine ID: `{machine_id}`\n"
        f"🔸 ចំនួនថ្ងៃ: {days} ថ្ងៃ\n"
        f"🔸 កាលបរិច្ឆេទផុតកំណត់: {expire_date}\n\n"
        f"🔑 LICENSE KEY (ចុចចម្លង): \n"
        f"\n{license_key}\n"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # ចំណាំ៖ នេះជាចំណុចដែលអ្នកអាចរក្សាទុក key និងព័ត៌មាននេះទៅកាន់ Database របស់អ្នកបាន។

    # បញ្ចប់ Conversation
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """លុបចោល Conversation ហើយបញ្ចប់។"""
    await update.message.reply_text("🚫 លុបចោលការបង្កើត Key។ សូមចុច /start ដើម្បីចាប់ផ្តើមម្តងទៀត។")
    return ConversationHandler.END


def main():
    """ចាប់ផ្តើម Bot"""
    # បង្កើត Application
    application = Application.builder().token(BOT_TOKEN).build()

    # បង្កើត ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        
        states={
            MACHINE_ID_STEP: [
                # រង់ចាំ Machine ID ជា Text
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_machine_id)
            ],
            DAYS_STEP: [
                # រង់ចាំចំនួនថ្ងៃជា Text (ដែលគួរតែជាលេខ)
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_key_and_finish)
            ],
        },
        
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # បន្ថែម ConversationHandler
    application.add_handler(conv_handler)

    # ចាប់ផ្តើម Polling
    logging.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "main":
    main()
