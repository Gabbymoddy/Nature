import os
import zipfile
import logging
import psycopg2
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler

# Load environment variables
load_dotenv()


# Access the secrets
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Construct the DATABASE_URL from individual environment variables
DATABASE_URL = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Establish a connection
conn = psycopg2.connect(DATABASE_URL, sslmode='require', sslrootcert='path/to/your/certificate.pem')


# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create the Updater instance with your bot token
updater = Updater(BOT_TOKEN, use_context=True)

# Define constants for storage limits
MAX_STORAGE_PER_USER = 4 * 1024 * 1024 * 1024  # 4GB in bytes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(name)

# New features
active_users = set()  # Set to store active user IDs
download_queue = []   # List to maintain the download queue
queue_time_remaining = 0

# New function to process the next user request
def process_next_user_request():
    if download_queue:
        user_id = download_queue.pop(0)  # Get the next user from the queue
        process_user_request_for_id(user_id)

# New function to process the next user request
def process_next_user_request():
    if download_queue:
        user_id = download_queue.pop(0)  # Get the next user from the queue
        process_user_request_for_id(user_id)

def process_user_request_for_id(user_id):
    # Add the file processing logic here for the specified user_id
    # This function should handle downloading, zipping, and sending files to Telegram
    active_users.add(user_id)
    # Once processing is complete, remove user from active_users set
    active_users.remove(user_id)

def clear_database(user_id):
    """Clears file information and user from the queue"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM uploaded_files WHERE user_id = %s", (user_id, ))
        conn.commit()
        cursor.close()
        if user_id in download_queue:
            download_queue.remove(user_id)  # Remove user from queue if present
    except Exception as e:
        logger.error(f"Error clearing database: {e}")

def show_active_users(update, context):
    active_users_list = "\n".join(str(user) for user in active_users)
    queue_info = f"ACTIVE USERS:\n{active_users_list}\n\nDOWNLOAD IN QUEUE:\n{download_queue}\nNEXT QUEUE IN: {queue_time_remaining} seconds"
    update.message.reply_text(queue_info)

def handle_user_request(update, context):
    user_id = update.message.from_user.id
    if len(active_users) < 5 and user_id not in active_users:
        active_users.add(user_id)
        process_user_request(update, context)
    else:
        download_queue.append(user_id)
        queue_position = len(download_queue)  # Position in the queue
        update.message.reply_text(
            f"I have added your file in the queue to download. Your position in the queue is: {queue_position}"
        )

def process_user_request(update, context):
    # Add the implementation to handle the user's file processing here
    # This function should handle downloading, zipping, and sending files to Telegram
    pass

def store_file_info(user_id, file_name, file_size):
    """Stores file information in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO uploaded_files (user_id, file_name, file_size) VALUES (%s, %s, %s)",
                       (user_id, file_name, file_size))
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Error storing file information: {e}")

def retrieve_files_info(user_id):
    """Retrieves file information from the database based on user_id."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM uploaded_files WHERE user_id = %s", (user_id,))
        files_info = cursor.fetchall()
        cursor.close()
        return files_info
    except Exception as e:
        logger.error(f"Error retrieving file information: {e}")
        return None


def fzip_files(update, context):
    """Downloads files, zips, and sends the zipped file to Telegram."""
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
        update.message.reply_text(
            "Insufficient storage space. Please delete some files or upgrade your plan."
        )
        return

    # Create the zip archive
    zip_dir = f"{zip_name}/{zip_name}"
    os.makedirs(zip_dir, exist_ok=True)
    with zipfile.ZipFile(f"{zip_name}.zip", "w") as zip_file:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))

    # Send the zip file to the user with progress
    zip_url = f"{zip_name}.zip"
    download_file_with_progress(zip_url, zip_url)

    try:
        # Automatically process next user from the queue
        process_next_user_request()
    except Exception as e:
        logger.error(f"Error processing next user request: {e}")

def start(update, context):
    """Welcome message for users"""
    update.message.reply_text(
        "Hello there! This is FILE ZIPPER Bot. I can help you manage your files."
        "\nUse /help for a list of commands."
    )


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
  update.message.reply_text(
      "FILE ZIPPER Bot is a Telegram bot designed to help you manage and zip your files."
  )

def help_command(update, context):
    """Displays information about available commands."""
    update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/fzip <name> - Download, zip, and send files to Telegram\n"
        "/showusers - Show active users and download queue\n"
        "/help - Display this help message\n"
        "/clear - Clear user's files and remove from the queue\n"
        "/my_files - List user's files\n"
        "/del <file_number> - Delete a file by its list number\n"
        "/about - Information about the bot"
    )


def main():
    # Load environment variables
    load_dotenv()

    # Access the secrets
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    bot_token = os.getenv('BOT_TOKEN')

    # Construct the DATABASE_URL from individual environment variables
    DATABASE_URL = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Establish a connection
    conn = psycopg2.connect(DATABASE_URL, sslmode='require', sslrootcert='eu-north-1-bundle.pem')

    # Create the Updater instance with your bot token
    updater = Updater(bot_token, use_context=True)

    # Define constants for storage limits
    MAX_STORAGE_PER_USER = 4 * 1024 * 1024 * 1024  # 4GB in bytes

    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
    logger = logging.getLogger(name)

    # No need to redefine active_users and download_queue here

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('fzip', fzip_files))
    dp.add_handler(CommandHandler('showusers', show_active_users))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('clear', clear_files))
    dp.add_handler(CommandHandler('my_files', list_files))
    dp.add_handler(CommandHandler('del', delete_file))
    dp.add_handler(CommandHandler('about', about))

    updater.start_polling()  # Start the bot
    updater.idle()

if __name__ == '__main__':
    main()
