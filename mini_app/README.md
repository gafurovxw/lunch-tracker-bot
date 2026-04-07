# 🍽 Lunch Tracker - Telegram Mini App

Telegram Mini App for the Lunch Tracker Bot - Web-based interface for employees and admins.

## Features

### For Employees:
- 📊 View monthly balance (attendance, earned, paid, debt)
- 📅 View today's lunch attendance list
- ✅ Mark payment status
- 📱 Native Telegram WebApp experience

### For Admins:
- 📈 Monthly summary report
- 👥 All employees debt overview
- 📊 Real-time attendance tracking

## Installation

### 1. Install Dependencies

```bash
cd mini_app
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in `mini_app` folder:

```bash
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
FLASK_ENV=production
```

### 3. Run the Server

Development:
```bash
python app.py
```

Production (with gunicorn):
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Setup with BotFather

1. Open [@BotFather](https://t.me/botfather)
2. Select your bot
3. Go to "Bot Settings" → "Menu Button" → "Configure menu button"
4. Set button text: "📱 Mini App"
5. Set URL: `https://your-domain.com` (or ngrok URL for development)

### For Local Development with ngrok:

```bash
# Install ngrok
# Run Flask app
python app.py

# In another terminal
ngrok http 5000

# Copy the https URL and set it in BotFather
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve mini app HTML |
| `/api/user/<telegram_id>` | GET | Get user info |
| `/api/balance/<employee_id>` | GET | Get employee balance |
| `/api/today` | GET | Get today's attendance |
| `/api/mark-paid` | POST | Mark as paid |
| `/api/admin/summary` | GET | Admin monthly summary |

## Project Structure

```
mini_app/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/               # Static assets (CSS, JS, images)
└── templates/
    └── index.html        # Main mini app interface
```

## Screenshots

### Employee View
- Balance card with stats
- Payment history
- Today's attendance

### Admin View
- Monthly summary
- All employees debt list
- Real-time attendance

## Notes

- Mini App uses Telegram WebApp API for native feel
- Automatically adapts to Telegram theme (light/dark)
- Responsive design for all screen sizes
- No separate login required (uses Telegram auth)
