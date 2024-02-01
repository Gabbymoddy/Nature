```markdown
# File Zipper Bot

File Zipper Bot is a Telegram bot designed to help users manage and zip their files.

## Features
- Download, zip, and send files to Telegram.
- View active users and download queue.
- Clear user's files and remove from the queue.
- List user's files.
- Delete a file by its list number.

## Getting Started
### Prerequisites
- Python 3.x
- PostgreSQL database

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/file-zipper-bot.git
   cd file-zipper-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root and add the following variables:
     ```
     DB_USERNAME=your_db_username
     DB_PASSWORD=your_db_password
     DB_HOST=your_db_host
     DB_PORT=your_db_port
     DB_NAME=your_db_name
     BOT_TOKEN=your_telegram_bot_token
     ```

4. Create and set up the PostgreSQL database:
   - Run the SQL script in `database_setup.sql` to create the necessary tables.

5. Run the bot:
   ```bash
   python bot.py
   ```

## Usage
- Start the bot by sending `/start`.
- Use `/fzip <name>` to download, zip, and send files to Telegram.
- Use `/showusers` to view active users and the download queue.
- ... (other available commands)

## Contributing
Contributions are welcome! If you have suggestions, bug reports, or want to contribute to the project, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

Make sure to replace placeholders like `your-username`, `your_db_username`, `your_db_password`, etc., with your actual information.
