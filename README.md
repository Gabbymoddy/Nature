```markdown
# File Zipper Telegram Bot

File Zipper is a Telegram bot designed to help you manage and zip your files. The bot can handle multiple users concurrently, allowing them to upload files, queue for processing, and receive zipped files.

## Features

- **Concurrent Processing:** The bot can handle up to five users simultaneously, ensuring efficient file processing.

- **File Zipping:** Users can upload files, and the bot will zip them upon request, sending the zipped file back to the user.

- **Queue System:** If the bot is busy, users are placed in a queue and processed in the order they joined.

## Getting Started

### Prerequisites

- Python 3
- PostgreSQL database

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/your-repository.git
   cd your-repository
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:

   Create a `.env` file in the root directory and add the following:

   ```env
   DB_USERNAME="your_database_username"
   DB_PASSWORD="your_database_password"
   DB_HOST="your_database_host"
   DB_PORT="your_database_port"
   DB_NAME="your_database_name"
   BOT_TOKEN="your_telegram_bot_token"
   ```

### Database Setup

1. Create a PostgreSQL database and update the `.env` file with your database credentials.

2. Run the following command to set up the database tables:

   ```bash
   python setup_database.py
   ```

### Running the Bot

```bash
python your_bot_script.py
```

### Usage

- `/start`: Start the bot and receive a welcome message.

- `/fzip <name>`: Upload files and request zipping. Replace `<name>` with the desired zip file name.

- `/showusers`: View active users and download queue.

- `/help`: Display a list of available commands.

- `/clear`: Clear user's files and remove from the queue.

- `/my_files`: List user's files.

- `/del <file_number>`: Delete a file by its list number.

- `/about`: Information about the bot.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

Make sure to replace placeholders like `your_database_username`, `your_database_password`, etc., with your actual credentials. 
