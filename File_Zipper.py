import os
import shutil
import zipfile
import logging
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler

# Load environment variables
load_dotenv()

# Replace with the actual Heroku Postgres URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Establish a connection
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create the Updater instance with your bot token
updater = Updater(BOT_TOKEN, use_context=True)

# Define constants for storage limits
MAX_STORAGE_PER_USER = 4 * 1024 * 1024 * 1024  # 4GB in bytes

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_storage(user_id):
    """Retrieve user storage information from the PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT storage_used FROM users WHERE id = %s", (user_id,))
        storage_usage = cursor.fetchone()[0]
        conn.close()
        return storage_usage
    except Exception as e:
        logger.error(f"Error retrieving user storage: {e}")
        return None

def retrieve_files_info(user_id):
    """Retrieves file information from the PostgreSQL database based on user_id"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = "SELECT * FROM uploaded_files WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        files_info = cursor.fetchall()

        conn.close()
        return files_info
    except Exception as e:
        logger.error(f"Error retrieving files information from the database: {e}")
        return []

def clear_database(user_id):
    """Clears file information from the PostgreSQL database based on user_id"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        query = "DELETE FROM uploaded_files WHERE user_id = %s"
        cursor.execute(query, (user_id,))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error clearing database: {e}")

def fzip_files(update, context):
    """Downloads files, zips, and sends the zipped file to Telegram"""

    user_id = update.message.from_user.id

    # User-provided directory name for the zip file
    try:
        zip_name = update.message.text.split()[1]
    except IndexError:
        update.message.reply_text("Please provide a name for the zipped directory.")
        return

    # Retrieve files from the database based on user_id
    files_info = retrieve_files_info(user_id)

    # Check if there are files to zip
    if not files_info:
        update.message.reply_text("No files found for zipping.")
        return

    # Download each file to the server and prepare for zipping
    file_paths = []
    total_size = 0

    for file_info in files_info:
        file_name = file_info[1]  # Assuming the second column is the file_name
        file_paths.append(file_name)
        total_size += file_info[2]  # Assuming the third column is the file_size

    # Check total file size and user storage usage
    user_storage = get_user_storage(user_id) or 0

    # Check if user storage limit exceeded
    if user_storage and total_size + user_storage > MAX_STORAGE_PER_USER:
        update.message.reply_text("Insufficient storage space. Please delete some files or upgrade your plan.")
        return

    # Create the zip archive
    zip_dir = f"{zip_name}/{zip_name}"
    os.makedirs(zip_dir, exist_ok=True)
    with zipfile.ZipFile(f"{zip_name}.zip", "w") as zip_file:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))

    try:
        # Send the zip file to the user
        with open(f"{zip_name}.zip", "rb") as zip_file:
            context.bot.send_document(chat_id=update.effective_chat.id, document=zip_file)
        update.message.reply_text("All files in the temporary directory have been cleared!")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {e}")
        logger.error(f"An error occurred in the 'fzip_files' command: {e}")

    # Cleanup downloaded files and zip file
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)
    os.remove(f"{zip_name}.zip")

    # Clear the database after zipping
    clear_database(user_id)

def start(update, context):
    """Welcome message for users"""
    update.message.reply_text(
        "Hello there! This is FILE ZIPPER Bot. I can help you manage your files."
        "\nUse /help for a list of commands."
    )

def help_command(update, context):
    """Provides help information about the bot and available commands"""
    update.message.reply_text(
        "Available commands:\n"
        "/start - Starts the bot and displays this message.\n"
        "/help - Shows this help message.\n"
        "/about - Provides information about the bot.\n"
        "/clear - Clears all files in your temporary directory.\n"
        "/my_files - Lists all files available for you to zip.\n"
        "/del [file_number] - Deletes a file by its list number from /my_files.\n"
        "/fzip [zip_name] - Zips the specified files into a zip archive and sends it to Telegram.\n"
    )

def clear_files(update, context):
    """Clears all files in the temporary directory"""
    user_id = update.message.from_user.id
    files_info = retrieve_files_info(user_id)

    # Clear the database first
    clear_database(user_id)

    # Remove files from the temporary directory
    for file_info in files_info:
        file_path = file_info[1]
        if os.path.exists(file_path):
            os.remove(file_path)

    update.message.reply_text("All files in the temporary directory have been cleared!")

def list_files(update, context):
    """Lists all files available for the user to zip"""
    user_id = update.message.from_user.id
    files_info = retrieve_files_info(user_id)

    if not files_info:
        update.message.reply_text("No files found for zipping.")
        return

    file_list = "\n".join([f"{index + 1}. {file_info[1]} - {file_info[2] / (1024 * 1024):.2f} MB" for index, file_info in enumerate(files_info)])
    update.message.reply_text(f"Files available for zipping:\n{file_list}")

def delete_file(update, context):
    """Deletes a file by its list number from /my_files"""
    try:
        file_number = int(update.message.text.split()[1])
        user_id = update.message.from_user.id
        files_info = retrieve_files_info(user_id)

        if 0 < file_number <= len(files_info):
            file_info = files_info[file_number - 1]
            file_path = file_info[1]

            # Remove file from the database and delete the file
            clear_database(user_id)
            if os.path.exists(file_path):
                os.remove(file_path)

            update.message.reply_text(f"File {file_number} has been deleted.")
        else:
            update.message.reply_text("Invalid file number.")
    except (ValueError, IndexError):
        update.message.reply_text("Please provide a valid file number.")

def about(update, context):
    """Provides information about the bot"""
    update.message.reply_text("FILE ZIPPER Bot is a Telegram bot designed to help you manage and zip your files.")

# Add handlers to the dispatcher
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help_command))
dispatcher.add_handler(CommandHandler('clear', clear_files))
dispatcher.add_handler(CommandHandler('my_files', list_files))
dispatcher.add_handler(CommandHandler('del', delete_file))
dispatcher.add_handler(CommandHandler('about', about))
dispatcher.add_handler(CommandHandler('fzip', fzip_files))

# Start the bot
updater.start_polling()
updater.idle()
