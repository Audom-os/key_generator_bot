import base64
import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, error
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

# ----------------------------------------------------
# ផ្នែកកំណត់រចនាសម្ព័ន្ធ (Configuration)
# ----------------------------------------------------
# ជំនួស BOT_TOKEN នេះដោយ Token ពិតប្រាកដរបស់អ្នកពី BotFather
BOT_TOKEN = "8561784312:AAGARnzctDczo98nMA4hA8_EnntBinrCZw4"

# កំណត់ Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# កំណត់ states សម្រាប់ ConversationHandler
MACHINE_ID_STEP, DAYS_STEP = range(2)

# ----------------------------------------------------
# មុខងារជំនួយ (Helper Functions)
# ----------------------------------------------------

def generate_license_key(machine_id: str, days: int) -> str:
    """
    បង្កើត License Key ដោយផ្អែកលើតក្កវិជ្ជាដែលបានផ្តល់ឱ្យនៅក្នុងកូដ C#។
    License Key ត្រូវបានបង្កើតឡើងជា Base64(MachineID|YYYY-MM-DD)
    """
    try:
        # គណនាកាលបរិច្ឆេទផុតកំណត់
        expire_date = datetime.date.today() + datetime.timedelta(days=days)
        expire_date_str = expire_date.strftime('%Y-%m-%d')

        # បញ្ចូលគ្នា
        combined_string = f"{machine_id}|{expire_date_str}"
        
        # Base64 Encode
        encoded_bytes = base64.b64encode(combined_string.encode('utf-8'))
        license_key = encoded_bytes.decode('utf-8')
        
        return license_key
    
    except Exception as e:
        logging.error(f"Error during key generation: {e}")
        return "Error"

# ----------------------------------------------------
# មុខងារ Handler សម្រាប់ Telegram Bot
# ----------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ចាប់ផ្តើម Conversation ហើយសុំ Machine ID។"""
    # ប្រើ message_source ដើម្បីទ្រទ្រង់ទាំង Command និង Callback Query
    message_source = update.message if update.message else update.callback_query.message
    
    await message_source.reply_text(
        "👋 សួស្តី! សូមផ្ញើ **Machine ID** របស់កុំព្យូទ័រដែលអ្នកចង់ Activate:"
    )
    context.user_data['machine_id'] = None 
    return MACHINE_ID_STEP


async def get_machine_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ទទួល Machine ID និងសុំចំនួនថ្ងៃ។"""
    machine_id = update.message.text.strip()
    
    if not machine_id:
        await update.message.reply_text(
            "Machine ID មិនអាចទទេបានទេ។ សូមព្យាយាមផ្ញើ Machine ID ម្តងទៀត៖"
        )
        return MACHINE_ID_STEP

    context.user_data['machine_id'] = machine_id
    
    await update.message.reply_text(
        f"✅ ទទួលបាន Machine ID: `{machine_id}`\n\n"
        "ឥឡូវសូមបញ្ចូល **ចំនួនថ្ងៃ** ដែលអ្នកចង់ឱ្យ License Key នេះមានសុពលភាព (ឧទាហរណ៍៖ 365):"
    )
    return DAYS_STEP


async def generate_key_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ទទួលចំនួនថ្ងៃ បង្កើត Key ហើយបញ្ចប់ Conversation។"""
    try:
        days = int(update.message.text.strip())
        if days <= 0:
             await update.message.reply_text("ចំនួនថ្ងៃត្រូវតែជាលេខវិជ្ជមាន។ សូមបញ្ចូលម្តងទៀត៖")
             return DAYS_STEP

    except ValueError:
        await update.message.reply_text("សូមបញ្ចូលតែលេខប៉ុណ្ណោះ។ សូមបញ្ចូលចំនួនថ្ងៃម្តងទៀត៖")
        return DAYS_STEP

    machine_id = context.user_data.get('machine_id')
    
    if not machine_id:
        await update.message.reply_text("❌ មានបញ្ហា៖ មិនមាន Machine ID ត្រូវបានរក្សាទុកទេ។ សូមចាប់ផ្តើមឡើងវិញដោយចុច /start")
        return ConversationHandler.END

    license_key = generate_license_key(machine_id, days)
    expire_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    # រក្សាទុក Key សម្រាប់មុខងារ Copy
    context.user_data['last_license_key'] = license_key 

    message = (
        f"🎉 **បង្កើត License Key ជោគជ័យ!**\n\n"
        f"🔸 **Machine ID**: `{machine_id}`\n"
        f"🔸 **ចំនួនថ្ងៃ**: {days} ថ្ងៃ\n"
        f"🔸 **កាលបរិច្ឆេទផុតកំណត់**: {expire_date}\n\n"
        f"🔑 **LICENSE KEY** (ចុចចម្លង): \n"
        f"```\n{license_key}\n```"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📝 ចម្លងកូដ (Copy Key)", callback_data='copy_key_send'), 
            InlineKeyboardButton("🔑 ធ្វើកូដថ្មី (New Key)", callback_data='start_new_key')
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
    
    return ConversationHandler.END


async def restart_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ចាប់ផ្តើម Conversation ឡើងវិញនៅពេលចុចប៊ូតុង Inline Key។"""
    query = update.callback_query
    
    # === ដំណោះស្រាយចំពោះ Query is too old (Issue 1) ===
    # ឆ្លើយតបភ្លាមៗ ដើម្បីជៀសវាង Timeout Error
    try:
        await query.answer("ចាប់ផ្តើម Key ថ្មី...")
    except error.BadRequest as e:
        # ប្រសិនបើ Query ចាស់ពេក គ្រាន់តែ Logging ហើយបន្ត
        logging.warning(f"Error answering callback query: {e}")
        pass
        
    # លុប Keyboard ចាស់
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except error.BadRequest as e:
        # Ignore if message is too old to edit
        logging.warning(f"Failed to edit message markup on restart: {e}")
        pass
        
    # === ដំណោះស្រាយចំពោះបាត់បង់ State (Issue 2) ===
    # ហៅ start() ហើយប្រគល់ State ទៅ ConversationHandler
    return await start(update, context)


async def send_key_for_copying(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ផ្ញើ Key ឡើងវិញជាសារថ្មី សម្រាប់ចម្លងងាយស្រួល។"""
    query = update.callback_query
    await query.answer("ផ្ញើកូដជាអក្សរធម្មតា...") # Pop-up ជូនដំណឹង

    license_key = context.user_data.get('last_license_key')
    
    if license_key:
        # ផ្ញើ Key ឡើងវិញជាសារថ្មីដើម្បីងាយស្រួល Copy
        await query.message.reply_text(
            f"🔑 **License Key (សម្រាប់ចម្លងងាយ)**:\n`{license_key}`", 
            parse_mode='Markdown'
        )
    else:
        await query.message.reply_text("❌ កូដមិនត្រូវបានរកឃើញទេ។ សូមបង្កើតកូដថ្មី។")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """លុបចោល Conversation ហើយបញ្ចប់។"""
    await update.message.reply_text("🚫 លុបចោលការបង្កើត Key។ សូមចុច /start ដើម្បីចាប់ផ្តើមម្តងទៀត។")
    return ConversationHandler.END


def main():
    """ចាប់ផ្តើម Bot"""
    application = Application.builder().token(BOT_TOKEN).build()

    # === កែសម្រួល៖ បន្ថែម CallbackQueryHandler ទៅ entry_points ===
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(restart_conversation, pattern='^start_new_key$') # ឥឡូវនៅទីនេះ
        ],
        
        states={
            MACHINE_ID_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_machine_id)
            ],
            DAYS_STEP: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_key_and_finish)
            ],
        },
        
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # CallbackQueryHandler សម្រាប់ប៊ូតុង "Copy Key" (នៅក្រៅ ConvHandler ព្រោះវាមិនប្តូរ State)
    application.add_handler(CallbackQueryHandler(send_key_for_copying, pattern='^copy_key_send$'))

    # CallbackQueryHandler សម្រាប់ប៊ូតុង 'start_new_key' ត្រូវបានលុបចេញពីទីនេះហើយ

    logging.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
