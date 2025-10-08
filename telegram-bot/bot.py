import os
import requests
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

logger.info(f"Telegram Token: {TELEGRAM_TOKEN[:20]}..." if TELEGRAM_TOKEN else "No token found!")
logger.info(f"Backend URL: {BACKEND_URL}")

# Store user quiz sessions
user_sessions: Dict[int, dict] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    logger.info(f"Start command from user {update.effective_user.id}")
    welcome_message = """
🎓 Welcome to AIQuizMasterBot! 🤖

I can generate AI-powered quizzes on any topic!

Commands:
/quiz <topic> <num> - Start a quiz
Example: /quiz React 5

/help - Show help message
    """
    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    logger.info(f"Help command from user {update.effective_user.id}")
    help_text = """
📚 How to use AIQuizMasterBot:

1️⃣ Use /quiz command:
   /quiz <topic> <number>
   
   Example: /quiz Python 5
   
2️⃣ Choose your answer:
   Click on A, B, C, or D buttons
   
3️⃣ Get instant feedback:
   ✅ Green = Correct
   ❌ Red = Wrong
   
📝 Rules:
- Number of questions: 3-30
- Topics: Any subject you want!
    """
    await update.message.reply_text(help_text)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quiz command handler"""
    user_id = update.effective_user.id
    logger.info(f"Quiz command from user {user_id} with args: {context.args}")
    
    # Check arguments
    if len(context.args) < 2:
        logger.warning(f"Invalid args from user {user_id}")
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: /quiz <topic> <number>\n"
            "Example: /quiz React 5"
        )
        return
    
    # Parse topic and number
    num_questions = context.args[-1]
    topic = " ".join(context.args[:-1])
    
    logger.info(f"Parsed topic: {topic}, num: {num_questions}")
    
    # Validate number
    try:
        num_questions = int(num_questions)
        if num_questions < 3 or num_questions > 30:
            raise ValueError
    except ValueError:
        logger.warning(f"Invalid number from user {user_id}: {context.args[-1]}")
        await update.message.reply_text(
            "❌ Number of questions must be between 3 and 30!"
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        f"🔄 Generating {num_questions} questions about {topic}...\n"
        "Please wait..."
    )
    
    try:
        # Call backend API
        api_url = f"{BACKEND_URL}/api/quiz/generate"
        logger.info(f"Calling API: {api_url}")
        
        response = requests.post(
            api_url,
            json={"topic": topic, "num_questions": num_questions},
            timeout=60
        )
        
        logger.info(f"API Response Status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API Error: {response.text}")
            raise Exception(f"API returned status {response.status_code}: {response.text[:200]}")
        
        response.raise_for_status()
        quiz_data = response.json()
        
        logger.info(f"Quiz generated successfully with {len(quiz_data['questions'])} questions")
        
        # Store quiz session
        user_sessions[user_id] = {
            "topic": quiz_data["topic"],
            "questions": quiz_data["questions"],
            "current_question": 0,
            "score": 0
        }
        
        # Delete loading message
        await loading_msg.delete()
        
        # Send first question
        await send_question(update, context, user_id)
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        await loading_msg.edit_text(
            f"❌ Cannot connect to backend server!\n\n"
            f"Backend URL: {BACKEND_URL}\n"
            "Please make sure the FastAPI server is running:\n"
            "`uvicorn app.main:app --reload`"
        )
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error: {e}")
        await loading_msg.edit_text(
            "❌ Request timeout!\n"
            "The backend took too long to respond.\n"
            "Please try again."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await loading_msg.edit_text(
            f"❌ Error connecting to backend:\n{str(e)[:200]}\n\n"
            "Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        await loading_msg.edit_text(
            f"❌ An error occurred:\n{str(e)[:200]}"
        )


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Send current question to user"""
    logger.info(f"Sending question to user {user_id}")
    
    session = user_sessions.get(user_id)
    if not session:
        logger.warning(f"No session found for user {user_id}")
        return
    
    current_idx = session["current_question"]
    questions = session["questions"]
    
    if current_idx >= len(questions):
        # Quiz finished
        score = session["score"]
        total = len(questions)
        percentage = (score / total) * 100
        
        result_message = f"""
🎉 Quiz Completed! 🎉

📊 Results:
✅ Correct: {score}/{total}
📈 Score: {percentage:.1f}%

{'🏆 Excellent!' if percentage >= 80 else '👍 Good job!' if percentage >= 60 else '📚 Keep learning!'}

Start a new quiz with /quiz <topic> <number>
        """
        
        logger.info(f"Quiz finished for user {user_id}. Score: {score}/{total}")
        
        if update.callback_query:
            await update.callback_query.message.reply_text(result_message)
        else:
            await update.message.reply_text(result_message)
        
        # Clear session
        del user_sessions[user_id]
        return
    
    # Get current question
    question = questions[current_idx]
    options = question["options"]
    
    logger.info(f"Question {current_idx + 1}/{len(questions)} for user {user_id}")
    
    # Create question text
    question_text = f"""
📝 Question {current_idx + 1}/{len(questions)}
Topic: {session['topic']}

{question['question']}
    """
    
    # Create inline keyboard with options
    keyboard = [
        [
            InlineKeyboardButton(f"A: {options['A']}", callback_data=f"answer_A_{user_id}"),
        ],
        [
            InlineKeyboardButton(f"B: {options['B']}", callback_data=f"answer_B_{user_id}"),
        ],
        [
            InlineKeyboardButton(f"C: {options['C']}", callback_data=f"answer_C_{user_id}"),
        ],
        [
            InlineKeyboardButton(f"D: {options['D']}", callback_data=f"answer_D_{user_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send question
    if update.callback_query:
        await update.callback_query.message.reply_text(
            question_text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            question_text,
            reply_markup=reply_markup
        )


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle answer button clicks"""
    query = update.callback_query
    await query.answer()
    
    logger.info(f"Answer callback: {query.data}")
    
    # Parse callback data
    _, selected_answer, user_id_str = query.data.split("_")
    user_id = int(user_id_str)
    
    logger.info(f"User {user_id} selected {selected_answer}")
    
    # Verify user
    if update.effective_user.id != user_id:
        await query.answer("❌ This is not your quiz!", show_alert=True)
        return
    
    session = user_sessions.get(user_id)
    if not session:
        logger.warning(f"No session for user {user_id}")
        await query.edit_message_text("❌ Quiz session expired. Start a new quiz with /quiz")
        return
    
    # Get correct answer
    current_idx = session["current_question"]
    question = session["questions"][current_idx]
    correct_answer = question["correct_answer"]
    options = question["options"]
    
    # Check if answer is correct
    is_correct = selected_answer == correct_answer
    
    logger.info(f"Answer is {'correct' if is_correct else 'wrong'}. Correct: {correct_answer}")
    
    if is_correct:
        session["score"] += 1
        result_emoji = "✅"
        result_text = "Correct!"
    else:
        result_emoji = "❌"
        result_text = f"Wrong! Correct answer: {correct_answer}"
    
    # Create updated keyboard with colored buttons
    keyboard = []
    for option in ["A", "B", "C", "D"]:
        if option == correct_answer:
            button_text = f"✅ {option}: {options[option]}"
        elif option == selected_answer and not is_correct:
            button_text = f"❌ {option}: {options[option]}"
        else:
            button_text = f"{option}: {options[option]}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"disabled_{option}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Update message with result
    result_message = f"""
📝 Question {current_idx + 1}/{len(session['questions'])}
Topic: {session['topic']}

{question['question']}

{result_emoji} {result_text}
    """
    
    await query.edit_message_text(result_message, reply_markup=reply_markup)
    
    # Move to next question
    session["current_question"] += 1
    
    # Send next question after a delay
    import asyncio
    await asyncio.sleep(2)
    await send_question(update, context, user_id)


def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    logger.info(f"Starting bot with token: {TELEGRAM_TOKEN[:20]}...")
    logger.info(f"Backend URL: {BACKEND_URL}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CallbackQueryHandler(answer_callback, pattern="^answer_"))
    
    # Start bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()