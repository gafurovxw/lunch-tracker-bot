# Lunch Tracker Bot - Agent Documentation

## Project Overview

Lunch Tracker Bot is a Telegram bot designed for tracking employee attendance and managing lunch payment calculations. The bot helps organizations monitor who attended work each day and calculate how much each employee should pay for lunches based on their attendance.

**Primary Language**: Uzbek (interface and comments)

## Technology Stack

- **Language**: Python 3
- **Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21.6 (async-based)
- **Database**: SQLite3 (file-based)
- **Configuration**: python-dotenv for environment variables
- **Dependencies**: See `requirements.txt`

## Project Structure

```
.
├── bot.py           # Main bot entry point, command handlers, and business logic
├── database.py      # Database operations, SQLite schema, and queries
├── config.py        # Configuration loader (environment variables)
├── requirements.txt # Python dependencies
├── .env             # Environment variables (not in version control)
├── .env.example     # Example environment file
├── lunch_tracker.db # SQLite database (created at runtime)
└── venv/            # Virtual environment directory
```

## Architecture

### Core Modules

1. **bot.py** (~866 lines)
   - Entry point and application setup
   - Command handlers for both admin and employee roles
   - Conversation flows for payment entry
   - Scheduled job queue for lunch reminders
   - Helper functions for formatting and name handling

2. **database.py** (~322 lines)
   - SQLite database initialization and schema
   - Employee management CRUD operations
   - Attendance tracking (mark present/absent)
   - Payment recording and balance calculations
   - Context manager for database connections

3. **config.py** (~10 lines)
   - Loads environment variables from `.env`
   - Exports: `BOT_TOKEN`, `ADMIN_IDS`, `DEFAULT_MONTHLY_SALARY`

### Database Schema

The SQLite database contains four tables:

- **employees**: Employee profiles with Telegram linkage
  - `id`, `first_name`, `last_name`, `position`, `telegram_id`, `monthly_salary`, `is_active`, `created_at`
  
- **attendance**: Daily attendance records
  - `id`, `employee_id`, `date`, `status` (1=present, 0=absent)
  
- **payments**: Payment records from employees
  - `id`, `employee_id`, `amount`, `date`, `note`
  
- **paid_status**: Tracks whether employee marked themselves as paid for the month
  - `id`, `employee_id`, `year`, `month`, `is_paid`

### Calculation Logic

- **Working days per month**: 22 days (hardcoded as `WORKING_DAYS_PER_MONTH`)
- **Daily rate**: `monthly_salary / 22`
- **Earned amount**: `attendance_count * daily_rate`
- **Debt**: `earned - paid` (if positive)
- **Overpayment**: `paid - earned` (if paid > earned)

## Role-Based Access

The bot has two user roles:

### Admin
- Configured via `ADMIN_IDS` environment variable (comma-separated Telegram IDs)
- Full access to all commands
- Can manage employees, mark attendance, view reports

### Employee
- Must be linked to a Telegram account by admin
- Limited to viewing own data and marking self as paid

## Available Commands

### Admin Commands
| Command | Description |
|---------|-------------|
| `/start` | Show admin panel with available commands |
| `/import_csv` | Bulk import employees from CSV file (format: first_name,last_name,position) |
| `/clear_employees` | Delete all employees and related data (with confirmation) |
| `/employees` | List all employees with IDs |
| `/link <telegram_id> <employee_id>` | Link Telegram account to employee record |
| `/mark` | Interactive attendance marking with inline keyboard |
| `/today` | Show today's attendance for all employees |
| `/balance` | Show all employees' balance summary for current month |
| `/pay` | Start payment entry conversation (select employee, enter amount, optional note) |
| `/report` | Monthly financial report with totals |
| `/debtors` | List employees with outstanding debt |
| `/paid_list` | List employees who marked themselves as paid |

### Employee Commands
| Command | Description |
|---------|-------------|
| `/start` | Show employee panel (or registration prompt if not linked) |
| `/today` | Check own attendance status for today |
| `/balance` | View detailed balance with payment history |
| `/paid` | Mark self as having paid for the current month |

## Configuration

Create a `.env` file in the project root:

```bash
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321  # Comma-separated Telegram user IDs
DEFAULT_MONTHLY_SALARY=200000  # Default monthly lunch budget in so'm
```

## Setup and Running

### Installation

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Bot

```bash
# Ensure .env is configured
python bot.py
```

The bot will:
1. Initialize the SQLite database if it doesn't exist
2. Start the Telegram polling loop
3. Schedule daily lunch reminders (11:50 and 11:55, Monday-Friday)

## Code Style Guidelines

- **Comments**: Use Uzbek language for inline comments and section dividers
- **Function names**: Use English with descriptive names (e.g., `cmd_start`, `get_employee_balance`)
- **Variable names**: Mixed English and Uzbek (e.g., `hodim` for employee in some contexts, `emp` in others)
- **String formatting**: Use f-strings for all user-facing messages (HTML parse mode)
- **Money formatting**: Use `fmt_money()` helper - formats as `XXX XXX so'm`

## Key Patterns

### Admin-only Decorator
```python
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in config.ADMIN_IDS:
            await update.effective_message.reply_text("⛔ Bu buyruq faqat adminlar uchun.")
            return ConversationHandler.END
        return await func(update, ctx)
    return wrapper
```

### Database Connection Context Manager
```python
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
```

### Conversation Handler Pattern (for /pay)
The bot uses `ConversationHandler` for multi-step interactions:
1. Entry: Select employee via callback
2. State `PAY_AMOUNT`: Enter payment amount
3. State `PAY_NOTE`: Enter optional note (or /skip)
4. End: Save to database

## Scheduled Jobs

The bot uses `python-telegram-bot`'s `JobQueue` for scheduled reminders:

- **11:50 AM** (Mon-Fri): "10 minutes until lunch" reminder
- **11:55 AM** (Mon-Fri): "5 minutes until lunch" reminder

## Security Considerations

1. **Bot Token**: Store in `.env`, never commit to version control
2. **Admin IDs**: Hardcoded in config, verify on every admin operation
3. **SQL Injection**: Uses parameterized queries throughout `database.py`
4. **File Uploads**: Only accepts `.csv` files for import
5. **Telegram IDs**: Stored as integers, linked manually by admin only

## Testing

There are no automated tests in this project. Testing is done manually:

1. Create a test bot via @BotFather
2. Set your Telegram ID as the only admin
3. Test commands in sequence:
   - `/import_csv` with a test CSV file
   - `/link` to connect your account
   - `/mark` to test attendance
   - `/pay` to test payment flow

## Deployment Notes

- The bot uses polling mode (suitable for small-scale deployment)
- Database is file-based (`lunch_tracker.db`), ensure write permissions
- For production, consider:
  - Webhook mode instead of polling
  - Regular database backups
  - Process manager (systemd, supervisor) for auto-restart

## Common Issues

1. **Database locked**: SQLite doesn't support concurrent writes well; bot is designed for single-instance use
2. **Time zones**: Reminder times are in server local time
3. **CSV encoding**: Import expects UTF-8 encoded files
