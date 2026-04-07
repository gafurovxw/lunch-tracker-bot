# 🚀 Mini App Hostingga Yuklash Qo'llanmasi

## Eng oson va bepul variantlar:

1. **Render** (Tavsiya etiladi) ⭐
2. **Railway** 
3. **PythonAnywhere**

---

## 1️⃣ Render.com orqali deploy qilish (BEPUL)

### Step 1: GitHub ga yuklash

```bash
# Yangi repo yaratish
cd /Users/gafurov.dev/Documents/lunch_tracker_bot
git init
git add .
git commit -m "Initial commit"

# GitHub ga yuklash (avval GitHub da repo yaratib oling)
git remote add origin https://github.com/YOUR_USERNAME/lunch-tracker-bot.git
git push -u origin main
```

### Step 2: Render da sozlash

1. [render.com](https://render.com) ga kiring (GitHub bilan)
2. **"New +"** → **"Web Service"**
3. GitHub repo ni ulang
4. Sozlamalar:

| Sozlama | Qiymat |
|---------|--------|
| Name | `lunch-tracker-app` |
| Environment | `Python 3` |
| Build Command | `pip install -r mini_app/requirements.txt` |
| Start Command | `cd mini_app && gunicorn -w 4 -b 0.0.0.0:$PORT app:app` |
| Plan | Free |

5. **Environment Variables** qo'shish:

```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
MINI_APP_URL=https://lunch-tracker-app.onrender.com
```

6. **Create Web Service** tugmasini bosing

⏱ Deploy ~2-3 daqiqa davom etadi.

### Step 3: BotFather da sozlash

1. [@BotFather](https://t.me/botfather) ga kiring
2. Botni tanlang → **Bot Settings** → **Menu Button**
3. **Configure menu button**:
   - Button text: `📱 Mini App`
   - URL: `https://lunch-tracker-app.onrender.com`

✅ Tayyor!

---

## 2️⃣ Railway.app orqali deploy (BEPUL)

### Step 1: Railway da loyiha yaratish

1. [railway.app](https://railway.app) ga kiring (GitHub bilan)
2. **"New Project"** → **"Deploy from GitHub repo"**
3. Repo ni tanlang

### Step 2: Sozlash

1. **Settings** → **Root Directory**: `mini_app`
2. **Variables** qo'shish:

```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
MINI_APP_URL=${{RAILWAY_STATIC_URL}}
PORT=5000
```

3. **Generate Domain** tugmasini bosing

✅ Avtomatik deploy bo'ladi!

---

## 3️⃣ PythonAnywhere orqali deploy (BEPUL)

### Step 1: Files yuklash

1. [pythonanywhere.com](https://pythonanywhere.com) ga kiring
2. **Files** tabiga o'ting
3. `mini_app` papkasini yuklang

### Step 2: Web app yaratish

1. **Web** tabiga o'ting
2. **"Add a new web app"**
3. **Flask** tanlang
4. Python 3.10 ni tanlang
5. Path: `/home/YOUR_USERNAME/mini_app/app.py`

### Step 3: WSGI sozlash

`/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`:

```python
import sys
path = '/home/YOUR_USERNAME/mini_app'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### Step 4: Virtual env

Bash console da:

```bash
cd mini_app
pip install -r requirements.txt
```

### Step 5: Reload

**Web** tabida **Reload** tugmasini bosing.

---

## 4️⃣ VPS (Ubuntu) orqali deploy

### Server ga ulanish:

```bash
ssh root@YOUR_SERVER_IP
```

### Loyihani o'rnatish:

```bash
# System yangilash
apt update && apt upgrade -y

# Python va git o'rnatish
apt install python3 python3-pip git nginx -y

# Loyihani klonlash
cd /var/www
git clone https://github.com/YOUR_USERNAME/lunch-tracker-bot.git
cd lunch-tracker-bot/mini_app

# Virtual env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# .env fayl
nano .env
```

### Systemd service:

```bash
sudo nano /etc/systemd/system/lunch-app.service
```

```ini
[Unit]
Description=Lunch Tracker Mini App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/lunch-tracker-bot/mini_app
Environment="PATH=/var/www/lunch-tracker-bot/mini_app/venv/bin"
ExecStart=/var/www/lunch-tracker-bot/mini_app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable lunch-app
sudo systemctl start lunch-app
```

### Nginx sozlash:

```bash
sudo nano /etc/nginx/sites-available/lunch-app
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/lunch-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL (HTTPS):

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Hosting taqqoslash

| Platform | Narx | Osonlik | Tezlik | Tavsiya |
|----------|------|---------|--------|---------|
| **Render** | Bepul | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Eng yaxshi |
| Railway | Bepul | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Yaxshi |
| PythonAnywhere | Bepul | ⭐⭐⭐ | ⭐⭐ | ⭐ O'rtacha |
| VPS | $5-10/oy | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ Professional |

---

## 🔧 Muammolar va yechimlari

### 1. "Build failed" xatosi

**Sabab:** Requirements noto'g'ri

**Yechim:**
```bash
# requirements.txt ni yangilang
pip freeze > requirements.txt
```

### 2. "Import error"

**Sabab:** Root directory noto'g'ri

**Yechim:** Render/Railway da `mini_app` papkasini root sifatida belgilang

### 3. Database topilmadi

**Sabab:** SQLite yo'li noto'g'ri

**Yechim:** `app.py` da DB_PATH ni tekshiring:

```python
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lunch_tracker.db')
```

### 4. Mini App ochilmayapti

**Sabab:** URL noto'g'ri

**Yechim:** 
- BotFather da URL ni tekshiring
- `https://` bilan boshlanishi kerak
- URL oxirida `/` bo'lmasligi kerak

---

## ✅ Tekshirish ro'yxati

Deploy qilgach, tekshiring:

- [ ] Mini App ochiladimi?
- [ ] Balans ma'lumotlari ko'rinadimi?
- [ ] Bugun ovqatlanish ro'yxati yangilanadimi?
- [ ] "Men to'ladim" tugmasi ishlaydimi?

---

## 📞 Yordam

Muammo bo'lsa:
1. Render/Railway logs ni tekshiring
2. `.env` fayl sozlamalarini tekshiring
3. GitHub issues ga yozing

**Omad! 🚀**
