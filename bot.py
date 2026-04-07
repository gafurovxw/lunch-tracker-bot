import logging
import asyncio
import csv
import io
import os
from datetime import date, time
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import database as db

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PAY_AMOUNT, PAY_NOTE, EDIT_PAID_AMOUNT, BROADCAST_MSG = range(4)


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if uid not in config.ADMIN_IDS:
            await update.effective_message.reply_text("⛔ Bu buyruq faqat adminlar uchun.")
            return ConversationHandler.END
        return await func(update, ctx)
    return wrapper


def fmt_money(amount: float) -> str:
    return f"{amount:,.0f} so'm".replace(",", " ")


def get_employee_name(emp) -> str:
    name = emp["first_name"]
    if emp["last_name"]:
        name += f" {emp['last_name']}"
    return name


def get_month_name(month: int) -> str:
    names = ["", "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
             "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"]
    return names[month]


# ── /start ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    is_admin = uid in config.ADMIN_IDS
    user = update.effective_user
    
    # Hodimni tekshirish
    if not is_admin:
        emp = db.get_employee_by_telegram_id(uid)
        
        if not emp:
            # Yangi hodim - admin ga xabar
            username = f"@{user.username}" if user.username else "username yo'q"
            full_name = user.full_name
            
            # Adminlarga xabar
            for admin_id in config.ADMIN_IDS:
                try:
                    await ctx.bot.send_message(
                        chat_id=admin_id,
                        text=f"🆕 <b>Yangi foydalanuvchi</b>\n\n"
                             f"👤 {full_name}\n"
                             f"🔗 {username}\n"
                             f"🆔 <code>{uid}</code>\n\n"
                             f"Ro'yxatdan o'tkazish uchun:\n"
                             f"/link {uid} [hodim_id]",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Admin xabar yuborishda xato: {e}")
            
            await update.message.reply_html(
                f"👋 Salom, <b>{full_name}</b>!\n\n"
                f"Siz hali ro'yxatda emassiz.\n"
                f"Admin sizni ro'yxatdan o'tkazishini kuting...\n\n"
                f"🆔 Sizning ID: <code>{uid}</code>\n"
                f"(Admin ga ayting)"
            )
            return
    
    if is_admin:
        text = """👔 <b>Admin panel</b>

<b>Buyruqlar:</b>
/import_csv - Hodimlarni bir martaba yuklash
/employees - Hodimlar ro'yxati
/link - Hodimni Telegram bilan bog'lash
/lunch_vote - Ovqatlanish votini boshlash
/today - Bugungi ovqatlanish
/mark - Davomat belgilash
/pay - To'lov kiritish
/edit_paid - To'langan summani o'zgartirish
/broadcast - Xabar yuborish
/report - Oylik hisobot
/debtors - Qarzdorlar
/app - Mini app ochish"""
    else:
        text = """👤 <b>Hodim paneli</b>

<b>Buyruqlar:</b>
/today - Bugun ovqatlanishga kelish
/paid - Men to'ladim
/app - Mini app orqali ko'rish"""
    
    await update.message.reply_html(text)


# ── /import_csv ────────────────────────────────────────────────────────────

@admin_only
async def cmd_import_csv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees()
    if employees:
        count = len(employees)
        await update.message.reply_html(
            f"⚠️ <b>Diqqat!</b>\n\n"
            f"Allaqachon <b>{count} ta</b> hodim mavjud.\n"
            f"Yangi yuklash uchun avval /clear_employees bilan tozalang."
        )
        return
    
    await update.message.reply_text("📄 CSV faylni yuboring.\nFormat: ism,familya,lavozim")


@admin_only
async def handle_csv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith('.csv'):
        await update.message.reply_text("❌ Faqat .csv fayllar")
        return
    
    try:
        file = await ctx.bot.get_file(doc.file_id)
        content = await file.download_as_bytearray()
        
        csv_text = content.decode('utf-8')
        reader = csv.reader(io.StringIO(csv_text))
        
        count = 0
        for row in reader:
            if len(row) >= 1 and row[0].strip():
                first = row[0].strip()
                last = row[1].strip() if len(row) > 1 else ""
                pos = row[2].strip() if len(row) > 2 else ""
                db.add_employee(first, last, pos, 200000)
                count += 1
        
        await update.message.reply_html(
            f"✅ <b>{count} ta</b> doimiy hodim qo'shildi!\n\n"
            f"Endi hodimlar /start bosib o'zlarini ro'yxatdan o'tkazishlari kerak."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")


# ── /clear_employees ───────────────────────────────────────────────────────

@admin_only
async def cmd_clear_employees(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Ha, o'chir", callback_data="clear_confirm")],
        [InlineKeyboardButton("❌ Yo'q, bekor qil", callback_data="clear_cancel")],
    ]
    await update.message.reply_text(
        "⚠️ <b>Diqqat!</b>\n\nBarcha hodimlar va ularning ma'lumotlari o'chiriladi.\nDavom etishmi?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def cb_clear_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "clear_cancel":
        await query.edit_message_text("❌ Bekor qilindi")
        return
    
    if query.data == "clear_confirm":
        count = db.clear_all_employees()
        await query.edit_message_text(f"🗑 <b>{count} ta</b> hodim o'chirildi", parse_mode="HTML")


# ── /link ─────────────────────────────────────────────────────────────────

@admin_only
async def cmd_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    
    if len(args) < 2:
        await update.message.reply_html(
            "<b>Foydalanish:</b>\n"
            "/link [telegram_id] [hodim_id]\n\n"
            "<b>Misol:</b>\n"
            "/link 123456789 5\n\n"
            "Hodim ID sini bilish uchun /employees"
        )
        return
    
    try:
        telegram_id = int(args[0])
        employee_id = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID. Raqam kiriting.")
        return
    
    emp = db.get_employee(employee_id)
    if not emp:
        await update.message.reply_text(f"❌ Hodim #{employee_id} topilmadi")
        return
    
    success = db.update_employee_telegram_id(employee_id, telegram_id)
    
    if success:
        name = get_employee_name(emp)
        await update.message.reply_html(
            f"✅ <b>Bog'landi!</b>\n\n"
            f"👤 {name} (ID: {employee_id})\n"
            f"🆔 Telegram: <code>{telegram_id}</code>\n\n"
            f"Hodim endi /start bosa oladi"
        )
        
        try:
            await ctx.bot.send_message(
                chat_id=telegram_id,
                text=f"✅ <b>Siz ro'yxatdan o'tdingiz!</b>\n\n"
                     f"👤 {name}\n"
                     f"Endi siz botdan foydalanishingiz mumkin:\n"
                     f"/today - Bugun ovqatlanish",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Hodimga xabar yuborishda xato: {e}")
    else:
        await update.message.reply_text("❌ Bog'lashda xatolik yuz berdi")


# ── /employees ─────────────────────────────────────────────────────────────

@admin_only
async def cmd_employees(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees()
    if not employees:
        await update.message.reply_text("❌ Hodimlar yo'q")
        return
    
    lines = [f"👥 <b>Hodimlar ro'yxati ({len(employees)} ta):</b>\n"]
    
    for emp in employees:
        name = get_employee_name(emp)
        pos = f" ({emp['position']})" if emp['position'] else ""
        lines.append(f"#{emp['id']}. {name}{pos}")
    
    await update.message.reply_html("\n".join(lines))


# ── /lunch_vote ────────────────────────────────────────────────────────────

@admin_only
async def cmd_lunch_vote(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Ovqatlanish votini boshlash"""
    employees = db.get_employees_with_telegram_id()
    if not employees:
        await update.message.reply_text("❌ Hodimlar topilmadi")
        return
    
    today = date.today()
    
    # Barcha hodimlarga xabar yuborish
    sent_count = 0
    for emp in employees:
        try:
            keyboard = [
                [InlineKeyboardButton("✅ Ha, boraman", callback_data=f"lunch_yes_{today.isoformat()}")],
                [InlineKeyboardButton("❌ Yo'q, bormayman", callback_data=f"lunch_no_{today.isoformat()}")],
            ]
            
            await ctx.bot.send_message(
                chat_id=emp["telegram_id"],
                text=f"🍽 <b>Ovqatlanishga borasizmi?</b>\n\n"
                     f"📅 Sana: {today.strftime('%d.%m.%Y')}\n"
                     f"⏰ Vaqti: 12:00\n\n"
                     f"Iltimos, variantni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Xabar yuborishda xato ({emp['first_name']}): {e}")
    
    await update.message.reply_html(
        f"✅ <b>{sent_count} ta</b> hodimga ovqatlanish voti yuborildi!\n\n"
        f"Natijalarni ko'rish: /today"
    )


async def cb_lunch_vote(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Hodim ovqatlanishga borishini tasdiqlash"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    if len(data) < 3:
        return
    
    vote = data[1]  # yes yoki no
    vote_date = data[2]
    
    uid = query.from_user.id
    emp = db.get_employee_by_telegram_id(uid)
    
    if not emp:
        await query.answer("❌ Siz ro'yxatda topilmadingiz", show_alert=True)
        return
    
    # Sana tekshirish
    today = date.today().isoformat()
    if vote_date != today:
        await query.answer("❌ Bu vot eskirgan", show_alert=True)
        return
    
    # Davomatni belgilash
    if vote == "yes":
        db.mark_attendance(emp["id"], date.today(), 1)
        status_text = "✅ Siz ovqatlanishga borasiz!"
    else:
        db.mark_attendance(emp["id"], date.today(), 0)
        status_text = "❌ Siz ovqatlanishga bormaysiz"
    
    await query.edit_message_text(
        f"🍽 <b>Ovqatlanishga borish</b>\n\n"
        f"📅 {date.today().strftime('%d.%m.%Y')}\n"
        f"{status_text}\n\n"
        f"Admin tasdiqlashini kuting..."
    )


# ── /today ─────────────────────────────────────────────────────────────────

async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = date.today()
    
    if uid in config.ADMIN_IDS:
        # Admin - barcha ovqatlanish ro'yxati
        records = db.get_attendance_for_day(today)
        present = [r for r in records if r["status"] == 1]
        absent = [r for r in records if r["status"] == 0]
        
        text = f"🍽 <b>{today.strftime('%d.%m.%Y')} - ovqatlanish</b>\n\n"
        if present:
            text += f"✅ <b>Boradi ({len(present)}):</b>\n"
            text += ", ".join([get_employee_name(r) for r in present])
            text += "\n\n"
        if absent:
            text += f"❌ <b>Bormaydi ({len(absent)}):</b>\n"
            text += ", ".join([get_employee_name(r) for r in absent])
            text += "\n\n"
        if not records:
            text += "Hali javob yo'q\n\n"
        
        text += f"<b>Vot yuborish:</b> /lunch_vote"
        
        await update.message.reply_html(text)
    else:
        # Hodim - faqat o'zi
        emp = db.get_employee_by_telegram_id(uid)
        if not emp:
            await update.message.reply_text("❌ Siz ro'yxatda topilmadingiz. /start bosing.")
            return
        
        records = db.get_attendance_for_day(today)
        my_status = None
        for r in records:
            if r["id"] == emp["id"]:
                my_status = r["status"]
                break
        
        status_text = {
            1: "✅ Siz ovqatlanishga borasiz",
            0: "❌ Siz ovqatlanishga bormaysiz",
        }.get(my_status, "⬜ Hali javob bermadingiz")
        
        await update.message.reply_html(
            f"👤 <b>{get_employee_name(emp)}</b>\n"
            f"📅 {today.strftime('%d.%m.%Y')}\n"
            f"🍽 {status_text}\n\n"
            f"<b>Ovoz berish:</b> /lunch_vote (admin yuborgan xabarga javob bering)"
        )


# ── /mark ──────────────────────────────────────────────────────────────────

@admin_only
async def cmd_mark(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees()
    if not employees:
        await update.message.reply_text("❌ Hodimlar yo'q")
        return
    
    today = date.today()
    attendance = {r["id"]: r["status"] for r in db.get_attendance_for_day(today)}
    
    keyboard = []
    for emp in employees:
        status = attendance.get(emp["id"])
        tick = "✅" if status == 1 else "❌" if status == 0 else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{tick} {get_employee_name(emp)}",
            callback_data=f"att_{emp['id']}"
        )])
    keyboard.append([InlineKeyboardButton("✔ Tayyor", callback_data="att_done")])
    
    await update.message.reply_text(
        f"📋 {today.strftime('%d.%m.%Y')} - davomat",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_attendance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "att_done":
        today = date.today()
        records = db.get_attendance_for_day(today)
        present = sum(1 for r in records if r["status"] == 1)
        absent = sum(1 for r in records if r["status"] == 0)
        await query.edit_message_text(
            f"✅ Saqlandi!\n📅 {today.strftime('%d.%m.%Y')}\n"
            f"✅ Keldi: {present}\n❌ Kelmadi: {absent}"
        )
        return
    
    if not query.data.startswith("att_"):
        return
    
    uid = query.from_user.id
    if uid not in config.ADMIN_IDS:
        await query.answer("⛔ Ruxsat yo'q", show_alert=True)
        return
    
    emp_id = int(query.data.split("_")[1])
    today = date.today()
    attendance = {r["id"]: r["status"] for r in db.get_attendance_for_day(today)}
    
    current = attendance.get(emp_id)
    if current is None:
        new_status = 1
    elif current == 1:
        new_status = 0
    else:
        db.unmark_attendance(emp_id, today)
        new_status = None
    
    if new_status is not None:
        db.mark_attendance(emp_id, today, new_status)
    
    employees = db.get_employees()
    attendance = {r["id"]: r["status"] for r in db.get_attendance_for_day(today)}
    
    keyboard = []
    for emp in employees:
        status = attendance.get(emp["id"])
        tick = "✅" if status == 1 else "❌" if status == 0 else "⬜"
        keyboard.append([InlineKeyboardButton(
            f"{tick} {get_employee_name(emp)}",
            callback_data=f"att_{emp['id']}"
        )])
    keyboard.append([InlineKeyboardButton("✔ Tayyor", callback_data="att_done")])
    
    await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))


# ── /pay ───────────────────────────────────────────────────────────────────

@admin_only
async def cmd_pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees()
    if not employees:
        await update.message.reply_text("❌ Hodimlar yo'q")
        return
    
    year, month = date.today().year, date.today().month
    
    keyboard = []
    for emp in employees:
        b = db.get_employee_balance(emp["id"], year, month)
        name = get_employee_name(emp)
        
        if b["debt"] > 0 or not b["is_paid"]:
            debt_text = f" ({fmt_money(b['debt'])} qarz)" if b["debt"] > 0 else " (to'lamagan)"
            keyboard.append([InlineKeyboardButton(
                f"{name}{debt_text}",
                callback_data=f"pay_{emp['id']}"
            )])
    
    if not keyboard:
        await update.message.reply_text("✅ Barcha hodimlar to'lovlarini amalga oshirgan!")
        return
    
    await update.message.reply_text(
        "💰 Kimga to'lov?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cb_pay_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith("pay_"):
        return
    
    emp_id = int(query.data.split("_")[1])
    emp = db.get_employee(emp_id)
    
    ctx.user_data["pay_emp_id"] = emp_id
    ctx.user_data["pay_emp_name"] = get_employee_name(emp)
    
    await query.edit_message_text("💵 Miqdorni kiriting (so'm):")
    return PAY_AMOUNT


async def pay_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri raqam. Qaytadan:")
        return PAY_AMOUNT
    
    ctx.user_data["pay_amount"] = amount
    await update.message.reply_text("📝 Izoh (yo'q bo'lsa /skip):")
    return PAY_NOTE


async def pay_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    note = "" if text == "/skip" else text
    
    emp_id = ctx.user_data.pop("pay_emp_id")
    emp_name = ctx.user_data.pop("pay_emp_name")
    amount = ctx.user_data.pop("pay_amount")
    
    db.add_payment(emp_id, amount, note)
    
    await update.message.reply_html(
        f"✅ <b>To'lov saqlandi!</b>\n"
        f"👤 {emp_name}\n"
        f"💵 {fmt_money(amount)}"
        + (f"\n📝 {note}" if note else "")
    )
    return ConversationHandler.END


async def pay_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi")
    return ConversationHandler.END


# ── /edit_paid ─────────────────────────────────────────────────────────────

@admin_only
async def cmd_edit_paid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Hodimning to'langan summasini o'zgartirish"""
    args = ctx.args
    
    if len(args) < 1:
        await update.message.reply_html(
            "<b>Foydalanish:</b>\n"
            "/edit_paid [hodim_id]\n\n"
            "<b>Misol:</b>\n"
            "/edit_paid 5\n\n"
            "Hodim ID sini bilish uchun /employees"
        )
        return
    
    try:
        employee_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri ID. Raqam kiriting.")
        return
    
    emp = db.get_employee(employee_id)
    if not emp:
        await update.message.reply_text(f"❌ Hodim #{employee_id} topilmadi")
        return
    
    year, month = date.today().year, date.today().month
    b = db.get_employee_balance(emp["id"], year, month)
    
    ctx.user_data["edit_emp_id"] = employee_id
    ctx.user_data["edit_emp_name"] = get_employee_name(emp)
    
    await update.message.reply_html(
        f"✏️ <b>To'lovni o'zgartirish</b>\n\n"
        f"👤 {get_employee_name(emp)}\n"
        f"📅 {get_month_name(month)} {year}\n"
        f"💰 Hozirgi to'langan: {fmt_money(b['paid'])}\n\n"
        f"Yangi summani kiriting (so'm):"
    )
    return EDIT_PAID_AMOUNT


async def edit_paid_amount(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        new_amount = float(update.message.text.strip().replace(" ", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri raqam. Qaytadan:")
        return EDIT_PAID_AMOUNT
    
    emp_id = ctx.user_data.pop("edit_emp_id")
    emp_name = ctx.user_data.pop("edit_emp_name")
    
    # Avvalgi to'lovlarni o'chirish va yangi summani qo'shish
    year, month = date.today().year, date.today().month
    
    # Yangi to'lov qo'shish (farq sifatida)
    db.add_payment(emp_id, new_amount, "Admin tomonidan o'zgartirildi")
    
    await update.message.reply_html(
        f"✅ <b>To'lov o'zgartirildi!</b>\n\n"
        f"👤 {emp_name}\n"
        f"💰 Yangi summa: {fmt_money(new_amount)}"
    )
    return ConversationHandler.END


# ── /broadcast ─────────────────────────────────────────────────────────────

@admin_only
async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Barcha hodimlarga xabar yuborish"""
    await update.message.reply_html(
        "📢 <b>Barcha hodimlarga xabar yuborish</b>\n\n"
        "Xabar matnini kiriting:"
    )
    return BROADCAST_MSG


async def broadcast_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    
    employees = db.get_employees_with_telegram_id()
    sent_count = 0
    failed_count = 0
    
    for emp in employees:
        try:
            await ctx.bot.send_message(
                chat_id=emp["telegram_id"],
                text=f"📢 <b>Xabar admin dan:</b>\n\n{message_text}",
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Xabar yuborishda xato ({emp['first_name']}): {e}")
            failed_count += 1
    
    await update.message.reply_html(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"📤 Yuborildi: {sent_count} ta\n"
        f"❌ Xato: {failed_count} ta"
    )
    return ConversationHandler.END


# ── /paid (hodim uchun) ────────────────────────────────────────────────────

async def cmd_paid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Hodim o'zini to'laganini belgilash"""
    uid = update.effective_user.id
    
    if uid in config.ADMIN_IDS:
        await update.message.reply_text("⛔ Bu buyruq faqat hodimlar uchun")
        return
    
    emp = db.get_employee_by_telegram_id(uid)
    if not emp:
        await update.message.reply_text("❌ Siz ro'yxatda topilmadingiz. /start bosing.")
        return
    
    year, month = date.today().year, date.today().month
    
    if db.is_marked_as_paid(emp["id"], year, month):
        await update.message.reply_html(
            f"⚠️ Siz allaqachon {get_month_name(month)} {year} uchun to'lagansiz!\n\n"
            f"Agar xato bo'lsa, admin bilan bog'laning."
        )
        return
    
    db.mark_as_paid(emp["id"], year, month)
    
    name = get_employee_name(emp)
    
    # Adminlarga xabar yuborish
    for admin_id in config.ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                chat_id=admin_id,
                text=f"💰 <b>Hodim to'lovni belgiladi!</b>\n\n"
                     f"👤 {name}\n"
                     f"📅 {get_month_name(month)} {year}\n\n"
                     f"Iltimos, tasdiqlang: /pay",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin ga xabar yuborishda xato: {e}")
    
    await update.message.reply_html(
        f"✅ <b>Siz to'laganingiz belgilandi!</b>\n\n"
        f"👤 {name}\n"
        f"📅 {get_month_name(month)} {year}\n\n"
        f"Admin tomonidan tasdiqlanishini kuting."
    )


# ── /app ────────────────────────────────────────────────────────────────────

async def cmd_app(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Open Mini App"""
    uid = update.effective_user.id
    
    # Check if user exists
    if uid not in config.ADMIN_IDS:
        emp = db.get_employee_by_telegram_id(uid)
        if not emp:
            await update.message.reply_text("❌ Siz ro'yxatda topilmadingiz. /start bosing.")
            return
    
    # Mini App URL - replace with your actual URL
    mini_app_url = os.getenv('MINI_APP_URL', 'https://your-domain.com')
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Mini App ochish", web_app={"url": mini_app_url})]
    ])
    
    await update.message.reply_html(
        f"📱 <b>Mini App</b>\n\n"
        f"Balansingizni, davomatingizni va to'lovlaringizni ko'rish uchun mini app oching:",
        reply_markup=keyboard
    )


# ── /report ─────────────────────────────────────────────────────────────────

@admin_only
async def cmd_report(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    year, month = date.today().year, date.today().month
    summary = db.get_monthly_summary(year, month)
    
    if not summary:
        await update.message.reply_text("❌ Ma'lumot yo'q")
        return
    
    total_salary = sum(b["monthly_salary"] for b in summary if b)
    total_earned = sum(b["earned"] for b in summary if b)
    total_paid = sum(b["paid"] for b in summary if b)
    total_debt = sum(b["debt"] for b in summary if b)
    total_attendance = sum(b["attendance_count"] for b in summary if b)
    
    text = f"📊 <b>Hisobot - {get_month_name(month)} {year}</b>\n\n"
    text += f"👥 Hodimlar: {len(summary)} ta\n"
    text += f"📊 Jami ishlangan kun: {total_attendance}\n"
    text += f"💵 Jami oylik (to'liq): {fmt_money(total_salary)}\n"
    text += f"💰 Jami ishlab topilgan: {fmt_money(total_earned)}\n"
    text += f"💸 Jami to'langan: {fmt_money(total_paid)}\n"
    text += f"🔴 Jami qarz: {fmt_money(total_debt)}\n\n"
    
    for b in summary:
        if not b:
            continue
        name = get_employee_name(b['employee'])
        paid_mark = "✓" if b['is_paid'] else "✗"
        
        if b["debt"] > 0:
            status = f"🔴 {fmt_money(b['debt'])}"
        elif b["overpaid"] > 0:
            status = f"🟢 +{fmt_money(b['overpaid'])}"
        else:
            status = "🟢 0"
        
        text += f"• {name}: {b['attendance_count']} kun | {status} | {paid_mark}\n"
    
    await update.message.reply_html(text)


# ── /debtors ───────────────────────────────────────────────────────────────

@admin_only
async def cmd_debtors(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    year, month = date.today().year, date.today().month
    summary = db.get_monthly_summary(year, month)
    debtors = [b for b in summary if b and (b["debt"] > 0 or not b["is_paid"])]
    
    if not debtors:
        await update.message.reply_html(
            f"🎉 <b>{get_month_name(month)} {year}</b>\nBarcha to'lovlar amalga oshirilgan!"
        )
        return
    
    text = f"🔴 <b>Qarzdorlar - {get_month_name(month)} {year}:</b>\n\n"
    for b in sorted(debtors, key=lambda x: -x["debt"]):
        name = get_employee_name(b['employee'])
        paid_mark = "✓ to'lagan" if b['is_paid'] else "✗ to'lamagan"
        text += f"• <b>{name}</b>: {fmt_money(b['debt'])} ({paid_mark})\n"
    
    await update.message.reply_html(text)


# ── Eslatmalar ─────────────────────────────────────────────────────────────

async def lunch_reminder_10min(context: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees_with_telegram_id()
    for emp in employees:
        try:
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text="🍽 <b>Eslatma!</b>\n\nOvqatlanishga <b>10 daqiqa</b> qoldi!\n⏰ 12:00",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Eslatma xato: {emp['first_name']}: {e}")


async def lunch_reminder_5min(context: ContextTypes.DEFAULT_TYPE):
    employees = db.get_employees_with_telegram_id()
    for emp in employees:
        try:
            await context.bot.send_message(
                chat_id=emp["telegram_id"],
                text="🍽 <b>Eslatma!</b>\n\nOvqatlanishga <b>5 daqiqa</b> qoldi!\n⏰ 12:00",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Eslatma xato: {emp['first_name']}: {e}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN yo'q!")
        return
    
    db.init_db()
    
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    # Conversation handlers
    pay_conv = ConversationHandler(
        entry_points=[CommandHandler("pay", cmd_pay), CallbackQueryHandler(cb_pay_select, pattern=r"^pay_\d+$")],
        states={
            PAY_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pay_amount)],
            PAY_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, pay_note)],
        },
        fallbacks=[CommandHandler("cancel", pay_cancel)],
    )
    
    edit_paid_conv = ConversationHandler(
        entry_points=[CommandHandler("edit_paid", cmd_edit_paid)],
        states={
            EDIT_PAID_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_paid_amount)],
        },
        fallbacks=[CommandHandler("cancel", pay_cancel)],
    )
    
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", cmd_broadcast)],
        states={
            BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", pay_cancel)],
    )
    
    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("import_csv", cmd_import_csv))
    app.add_handler(CommandHandler("clear_employees", cmd_clear_employees))
    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(CommandHandler("employees", cmd_employees))
    app.add_handler(CommandHandler("lunch_vote", cmd_lunch_vote))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("mark", cmd_mark))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("debtors", cmd_debtors))
    app.add_handler(CommandHandler("paid", cmd_paid))
    app.add_handler(CommandHandler("app", cmd_app))
    app.add_handler(pay_conv)
    app.add_handler(edit_paid_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CallbackQueryHandler(cb_clear_confirm, pattern=r"^clear_"))
    app.add_handler(CallbackQueryHandler(cb_attendance, pattern=r"^att_"))
    app.add_handler(CallbackQueryHandler(cb_lunch_vote, pattern=r"^lunch_"))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), handle_csv))
    
    # Eslatmalar (Dushanba-Juma, 11:50 va 11:55)
    app.job_queue.run_daily(lunch_reminder_10min, time=time(hour=11, minute=50), days=(0,1,2,3,4))
    app.job_queue.run_daily(lunch_reminder_5min, time=time(hour=11, minute=55), days=(0,1,2,3,4))
    
    # Event loop
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
