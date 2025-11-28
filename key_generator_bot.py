import base64
import datetime
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
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
    await update.message.reply_text(
        "👋 សួស្តី! សូមផ្ញើ **Machine ID** របស់កុំព្យូទ័រដែលអ្នកចង់ Activate:"
    )
    # រក្សាទុកក្នុង context សម្រាប់ប្រើពេលក្រោយ
    context.user_data['machine_id'] = None 
    return MACHINE_ID_STEP


async def get_machine_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ទទួល Machine ID និងសុំចំនួនថ្ងៃ។"""
    machine_id = update.message.text.strip()
    
    # === កែសម្រួលតាម GeneratorKeyLicense.cs ===
    # កូដ C# គ្រាន់តែត្រួតពិនិត្យថា Machine ID មិនទទេប៉ុណ្ណោះ។
    if not machine_id:
        await update.message.reply_text(
            "Machine ID មិនអាចទទេបានទេ។ សូមព្យាយាមផ្ញើ Machine ID ម្តងទៀត៖"
        )
        return MACHINE_ID_STEP # រង់ចាំ Machine ID ត្រឹមត្រូវ
    # ==========================================
    
    # រក្សាទុក Machine ID
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

    # យក Machine ID ដែលបានរក្សាទុក
    machine_id = context.user_data.get('machine_id')
    
    if not machine_id:
        await update.message.reply_text("❌ មានបញ្ហា៖ មិនមាន Machine ID ត្រូវបានរក្សាទុកទេ។ សូមចាប់ផ្តើមឡើងវិញដោយចុច /start")
        return ConversationHandler.END

    # បង្កើត License Key
    license_key = generate_license_key(machine_id, days)

    expire_date = (datetime.date.today() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')

    # ផ្ញើ Key ទៅអ្នកប្រើប្រាស់
    message = (
        f"🎉 **បង្កើត License Key ជោគជ័យ!**\n\n"
        f"🔸 **Machine ID**: `{machine_id}`\n"
        f"🔸 **ចំនួនថ្ងៃ**: {days} ថ្ងៃ\n"
        f"🔸 **កាលបរិច្ឆេទផុតកំណត់**: {expire_date}\n\n"
        f"🔑 **LICENSE KEY** (ចុចចម្លង): \n"
        f"```\n{license_key}\n```"
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

if __name__ == "__main__":
    main()
