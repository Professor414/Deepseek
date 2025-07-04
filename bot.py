import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai
from dotenv import load_dotenv # <-- ផ្នែកដែលបានបន្ថែមថ្មី

# ផ្ទុកค่าពីឯកសារ .env ចូលទៅក្នុង Environment Variables របស់ប្រព័ន្ធ
load_dotenv() # <-- ផ្នែកដែលបានបន្ថែមថ្មី

# --- ការកំណត់ค่า (Configuration) ---

# បើកដំណើរការ Logging ដើម្បីឱ្យយើងអាចមើលឃើញ Error និងសកម្មភាពរបស់ Bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# យក Token និង Key ពី Environment Variables (វិធីសាស្ត្រដែលមានសុវត្ថិភាព)
# កូដនេះនឹងទៅអានค่าពីឯកសារ .env ដែលអ្នកបានបង្កើត
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ពិនិត្យមើលថា Token ត្រូវបានរកឃើញពី Environment Variables ហើយឬនៅ
if not TELEGRAM_BOT_TOKEN:
    logger.error("!!! FATAL: មិនអាចរកឃើញ 'TELEGRAM_BOT_TOKEN' ទេ។ សូមពិនិត្យមើលឯកសារ .env របស់អ្នក។")
    exit()
if not DEEPSEEK_API_KEY:
    logger.error("!!! FATAL: មិនអាចរកឃើញ 'DEEPSEEK_API_KEY' ទេ។ សូមពិនិត្យមើលឯកសារ .env របស់អ្នក។")
    exit()

# កំណត់ค่า OpenAI client ឱ្យចង្អុលទៅកាន់ DeepSeek API
# នេះជាផ្នែកសំខាន់បំផុតដែលធ្វើឱ្យ Library របស់ OpenAI អាចនិយាយជាមួយ DeepSeek បាន
try:
    client = openai.OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    logger.error(f"เกิดข้อผิดพลาดในการตั้งค่า OpenAI client: {e}")
    exit()


# --- មុខងាររបស់ Bot (Bot Functions) ---
# (ផ្នែកខាងក្រោមនេះនៅដដែលទាំងអស់)

async def get_deepseek_response(user_message: str) -> str:
    """បញ្ជូនសារទៅកាន់ DeepSeek API ហើយទទួលយកចម្លើយមកវិញ"""
    logger.info(f"កំពុងបញ្ជូនសារទៅ DeepSeek: '{user_message}'")
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # ប្រើម៉ូឌែលរបស់ DeepSeek
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """គ្រប់គ្រងសារអត្ថបទធម្មតា"""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # បង្ហាញសារ "កំពុងគិត..." ដើម្បីឱ្យអ្នកប្រើប្រាស់ដឹងថា Bot កំពុងដំណើរការ
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    # យកចម្លើយពី DeepSeek
    bot_response = await get_deepseek_response(user_message)

    # ផ្ញើចម្លើយចុងក្រោយទៅកាន់អ្នកប្រើប្រាស់
    await update.message.reply_text(bot_response)

def main() -> None:
    """ចាប់ផ្តើម Bot"""
    # បង្កើត Application ហើយដាក់ Token របស់ Bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ចុះឈ្មោះអ្នកគ្រប់គ្រង (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot កំពុងចាប់ផ្តើមដំណើរការ... សូមចុច Ctrl+C ដើម្បីបញ្ឈប់។")
    
    # ដំណើរការ Bot រហូតដល់អ្នកប្រើប្រាស់ចុច Ctrl+C
    application.run_polling()

if __name__ == '__main__':
    main()