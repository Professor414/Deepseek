import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from dotenv import load_dotenv

# ផ្ទុកค่าពីឯកសារ .env ចូលទៅក្នុង Environment Variables របស់ប្រព័ន្ធ
load_dotenv()

# --- ការកំណត់ค่า (Configuration) ---

# បើកដំណើរការ Logging ដើម្បីឱ្យយើងអាចមើលឃើញ Error និងសកម្មភាពរបស់ Bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# យក Token និង Key ពី Environment Variables (វិធីសាស្ត្រដែលមានសុវត្ថិភាព)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ពិនិត្យមើលថា Token ត្រូវបានរកឃើញពី Environment Variables ហើយឬនៅ
if not TELEGRAM_BOT_TOKEN:
    logger.error("!!! FATAL: មិនអាចរកឃើញ 'TELEGRAM_BOT_TOKEN' ទេ។ សូមពិនិត្យមើលឯកសារ .env ឬ Environment Variables នៅលើ Render។")
    exit()
if not DEEPSEEK_API_KEY:
    logger.error("!!! FATAL: មិនអាចរកឃើញ 'DEEPSEEK_API_KEY' ទេ។ សូមពិនិត្យមើលឯកសារ .env ឬ Environment Variables នៅលើ Render។")
    exit()

# កំណត់ค่า OpenAI client ឱ្យចង្អុលទៅកាន់ DeepSeek API
try:
    client = openai.OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    logger.error(f"เกิดข้อผิดพลาดในการตั้งค่า OpenAI client: {e}")
    exit()


# --- មុខងាររបស់ Bot (Bot Functions) ---

async def get_deepseek_response(user_message: str) -> str:
    """បញ្ជូនសារទៅកាន់ DeepSeek API ហើយទទួលយកចម្លើយមកវិញ"""
    logger.info(f"កំពុងបញ្ជូនសារទៅ DeepSeek: '{user_message}'")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant speaking Khmer."},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"មានបញ្ហាក្នុងការទាក់ទងជាមួយ DeepSeek API: {e}")
        return "សូមអភ័យទោស! ខ្ញុំកំពុងមានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ខួរក្បាលរបស់ខ្ញុំ។ សូមព្យាយាមម្តងទៀតនៅពេលក្រោយ។"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """គ្រប់គ្រងពាក្យបញ្ជា /start"""
    user_name = update.effective_user.first_name
    await update.message.reply_html(
        rf"សួស្តី {user_name}! ខ្ញុំគឺជា Bot ដែលដំណើរការដោយ DeepSeek។ សូមផ្ញើសារមកខ្ញុំ ខ្ញុំនឹងព្យាយាមឆ្លើយតប។"
    )

#
# --- !! ផ្នែកដែលបានកែប្រែ !! ---
#
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """គ្រប់គ្រងសារអត្ថបទធម្មតា (បាន Update សម្រាប់ PTB v20+)"""
    # ត្រូវប្រាកដថាមានសារ ហើយសារនោះមានអក្សរ
    if not update.message or not update.message.text:
        return

    user_message = update.message.text
    
    # បញ្ជូនសកម្មភាព "typing..." ។ នេះគឺជាវិធីថ្មី និងត្រឹមត្រូវ។
    await update.message.chat.send_action(action="typing")

    # យកចម្លើយពី DeepSeek
    bot_response = await get_deepseek_response(user_message)

    # ឆ្លើយតបទៅកាន់សាររបស់អ្នកប្រើប្រាស់
    await update.message.reply_text(bot_response)
#
# --- !! ចប់ផ្នែកដែលបានកែប្រែ !! ---
#

def main() -> None:
    """ចាប់ផ្តើម Bot"""
    # បង្កើត Application ហើយដាក់ Token របស់ Bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ចុះឈ្មោះអ្នកគ្រប់គ្រង (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot កំពុងចាប់ផ្តើមដំណើរការ...")
    
    # ដំណើរការ Bot
    application.run_polling()

if __name__ == '__main__':
    main()