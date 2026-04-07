# 🍽 Lunch Tracker Bot - Foydalanish Qo'llanmasi

## Bot haqida
Bu bot ofis hodimlarining ovqatlanishini tracking qilish va hisob-kitob qilish uchun mo'ljallangan.

---

## 👔 ADMIN UCHUN YO'RIQNOMA

### 1. Birinchi marta sozlash

#### 1.1 Hodimlarni yuklash
```
/import_csv
```
- CSV faylni yuboring (format: `ism,familya,lavozim`)
- Misol: `Ali,Valiyev,Dasturchi`
- Faqat bir marta qilinadi!

#### 1.2 Hodimlarni ro'yxatdan o'tkazish
Hodim `/start` bosganda, sizga avtomatik xabar keladi:
```
🆕 Yangi foydalanuvchi

👤 Ali Valiyev
🔗 @username
🆔 123456789

Ro'yxatdan o'tkazish uchun:
/link 123456789 5
```

Hodimni bog'lash:
```
/link [telegram_id] [hodim_id]
```
Misollar:
```
/link 123456789 5    (Ali Valiyev ni bog'lash)
/link 987654321 3    (Vali Aliyev ni bog'lash)
```

**Hodim ID sini `/employees` bilan ko'rasiz**

---

### 2. Ovqatlanishni boshqarish

#### 2.1 Ovqatlanish votini yuborish
```
/lunch_vote
```
- Barcha hodimlarga ovqatlanishga borish-yo'qligi haqida so'rov yuboriladi
- Hodimlar "Ha, boraman" yoki "Yo'q, bormayman" tugmalari bilan javob beradi

#### 2.2 Kim borayotganini ko'rish
```
/today
```
Natija:
```
🍽 15.04.2025 - ovqatlanish

✅ Boradi (15): Ali, Vali, G'ani, ...
❌ Bormaydi (8): Anvar, Baxtiyor, ...
```

#### 2.3 Davomatni qo'lda belgilash (agar kerak bo'lsa)
```
/mark
```
- Tugmalar orqali kim keldi/kelmadi belgilaydi
- ⬜ Belgilanmagan → ✅ Keldi → ❌ Kelmadi

---

### 3. To'lovlar bilan ishlash

#### 3.1 To'lov kiritish
```
/pay
```
- Hodimni tanlang
- Summani kiriting
- Izoh qo'shing (ixtiyoriy)

#### 3.2 To'lovni o'zgartirish
```
/edit_paid [hodim_id]
```
Misol:
```
/edit_paid 5
```
Yangi summani kiriting.

#### 3.3 Qarzdorlarni ko'rish
```
/debtors
```
Natija:
```
🔴 Qarzdorlar - Aprel 2025:

• Ali Valiyev: 50,000 so'm (✓ to'lagan)
• Vali Aliyev: 30,000 so'm (✗ to'lamagan)
```

---

### 4. Hisobotlar

#### 4.1 Umumiy hisobot
```
/report
```
Natija:
```
📊 Hisobot - Aprel 2025

👥 Hodimlar: 23 ta
📊 Jami ishlangan kun: 420
💵 Jami oylik: 4,600,000 so'm
💰 Jami ishlab topilgan: 3,818,181 so'm
💸 Jami to'langan: 3,500,000 so'm
🔴 Jami qarz: 318,181 so'm

• Ali Valiyev: 20 kun | 🔴 50,000 | ✓
• Vali Aliyev: 22 kun | 🟢 0 | ✓
• ...
```

#### 4.2 Hodimlar ro'yxati
```
/employees
```
Natija:
```
👥 Hodimlar ro'yxati (23 ta):

#1. Ali Valiyev (Dasturchi)
#2. Vali Aliyev (Dizayner)
#3. ...
```

---

### 5. Xabar yuborish

```
/broadcast
```
Xabar matnini kiriting va barcha hodimlarga yuboriladi.

---

### 6. Avtomatik eslatmalar
Bot har kuni avtomatik yuboradi:
- **11:50** - "Ovqatlanishga 10 daqiqa qoldi!"
- **11:55** - "Ovqatlanishga 5 daqiqa qoldi!"

**Faqat ish kunlari (Dushanba-Juma)**

---

## 👤 HODIM UCHUN YO'RIQNOMA

### 1. Ro'yxatdan o'tish

#### 1.1 Botga kirish
1. Botga kiring: [@your_bot_username]
2. `/start` buyrug'ini yuboring

#### 1.2 Admin tasdiqlashini kuting
```
👋 Salom, Ali Valiyev!

Siz hali ro'yxatda emassiz.
Admin sizni ro'yxatdan o'tkazishini kuting...

🆔 Sizning ID: 123456789
(Admin ga ayting)
```

#### 1.3 Tasdiqlashdan so'ng
Admin sizni bog'lagach, quyidagi xabar keladi:
```
✅ Siz ro'yxatdan o'tdingiz!

👤 Ali Valiyev
Endi siz botdan foydalanishingiz mumkin:
/today - Bugun ovqatlanish
/paid - Men to'ladim
```

---

### 2. Ovqatlanishga kelish

#### 2.1 Ovqatlanishga borishni tasdiqlash
Admin `/lunch_vote` yuborganda, sizga xabar keladi:
```
🍽 Ovqatlanishga borasizmi?

📅 Sana: 15.04.2025
⏰ Vaqti: 12:00

Iltimos, variantni tanlang:
[✅ Ha, boraman] [❌ Yo'q, bormayman]
```

Tugmani bosing:
- ✅ Ha, boraman - Ovqatlanishga borasiz
- ❌ Yo'q, bormayman - Bormaysiz

#### 2.2 O'z holatini tekshirish
```
/today
```
Natija:
```
👤 Ali Valiyev
📅 15.04.2025
🍽 ✅ Siz ovqatlanishga borasiz

Ovoz berish: /lunch_vote (admin yuborgan xabarga javob bering)
```

---

### 3. To'lov

#### 3.1 To'laganingizni belgilash
```
/paid
```
Natija:
```
✅ Siz to'laganingiz belgilandi!

👤 Ali Valiyev
📅 Aprel 2025

Admin tomonidan tasdiqlanishini kuting.
```

**Diqqat:** Bu faqat sizning e'loningiz. Admin `/pay` buyrug'i bilan to'lovni qayd etadi.

#### 3.2 To'lovni qayta belgilash
Agar oldinroq belgilagan bo'lsangiz:
```
⚠️ Siz allaqachon Aprel 2025 uchun to'lagansiz!

Agar xato bo'lsa, admin bilan bog'laning.
```

---

### 4. Avtomatik eslatmalar
Bot sizga har kuni avtomatik yuboradi:
- **11:50** - "🍽 Eslatma! Ovqatlanishga 10 daqiqa qoldi! ⏰ 12:00"
- **11:55** - "🍽 Eslatma! Ovqatlanishga 5 daqiqa qoldi! ⏰ 12:00"

---

## 💰 HISOB-KITOB TIZIMI

### Qanday hisoblanadi?

```
Kunlik sarfi = 200,000 ÷ 22 = 9,091 so'm
Ishlab topgan = Kelgan kunlar × 9,091 so'm
Qarz = Ishlab topgan - To'langan
```

### Misol:
Ali 20 kun ishlagan bo'lsa:
- Ishlab topgan: 20 × 9,091 = **181,818 so'm**
- To'langan: **150,000 so'm**
- Qarz: 181,818 - 150,000 = **31,818 so'm**

---

## ❓ KO'P SO'RALADIGAN SAVOLLAR

### Admin uchun

**S: Hodim qo'shishim kerak, qanday qilaman?**
J: `/import_csv` bilan CSV fayl yuklang. Faqat bir marta!

**S: Yangi hodim qo'shishim kerak, lekin allaqachon yuklaganman.**
J: Avval `/clear_employees` bilan tozalang, keyin yangi CSV yuklang.

**S: Hodim ro'yxatdan o'tmadi, nima qilish kerak?**
J: Hodim `/start` bosganmi? Tekshiring. Telegram ID ni olib, `/link` bilan bog'lang.

**S: To'lovni o'zgartirish mumkinmi?**
J: Ha, `/edit_paid [hodim_id]` buyrug'idan foydalaning.

### Hodim uchun

**S: Botga kirdim, lekin "ro'yxatda emassiz" deydi.**
J: Admin ga Telegram ID ingizni ayting. U sizni `/link` bilan bog'laydi.

**S: Ovqatlanishga borishni qanday tasdiqlayman?**
J: Admin `/lunch_vote` yuborganda, sizga xabar keladi. Tugmani bosing.

**S: To'ladim, lekin admin bilmayapti.**
J: `/paid` buyrug'ini yuboring. Admin ga xabar ketadi.

**S: Bugun ovqatlanishga boramanmi yo'qmi qanday bilaman?**
J: `/today` buyrug'ini yuboring.

---

## 📞 ALOQA

Muammolar yuzaga kelsa, admin bilan bog'laning.

---

**Bot versiyasi:** 2.0  
**Yangilangan:** 2025-yil
