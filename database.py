import sqlite3
from datetime import date, datetime
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "lunch_tracker.db")
WORKING_DAYS_PER_MONTH = 22  # Oydagi ish kunlari


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                position TEXT,
                telegram_id INTEGER,
                monthly_salary REAL DEFAULT 200000,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status INTEGER DEFAULT 1,
                UNIQUE(employee_id, date),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            
            CREATE TABLE IF NOT EXISTS paid_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                is_paid INTEGER DEFAULT 0,
                UNIQUE(employee_id, year, month),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
        """)


# ── Employees ──────────────────────────────────────────────────────────────

def add_employee(first_name: str, last_name: str = "", position: str = "", monthly_salary: float = 200000) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO employees (first_name, last_name, position, monthly_salary) VALUES (?, ?, ?, ?)",
            (first_name, last_name, position, monthly_salary),
        )
        return cur.lastrowid


def deactivate_employee(employee_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE employees SET is_active = 0 WHERE id = ?",
            (employee_id,),
        )
        return cur.rowcount > 0


def get_employees(active_only: bool = True) -> list:
    with get_conn() as conn:
        query = "SELECT * FROM employees"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY first_name, last_name"
        return conn.execute(query).fetchall()


def get_employee(employee_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()


def get_employee_by_telegram_id(telegram_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM employees WHERE telegram_id = ? AND is_active = 1",
            (telegram_id,)
        ).fetchone()


def get_employee_by_name(first_name: str, last_name: str = ""):
    with get_conn() as conn:
        if last_name:
            return conn.execute(
                "SELECT * FROM employees WHERE first_name = ? AND last_name = ? AND is_active = 1",
                (first_name, last_name)
            ).fetchone()
        else:
            return conn.execute(
                "SELECT * FROM employees WHERE first_name = ? AND is_active = 1",
                (first_name,)
            ).fetchone()


def update_employee_telegram_id(employee_id: int, telegram_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE employees SET telegram_id = ? WHERE id = ?",
            (telegram_id, employee_id)
        )
        return cur.rowcount > 0


def update_monthly_salary(employee_id: int, salary: float) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE employees SET monthly_salary = ? WHERE id = ?",
            (salary, employee_id),
        )
        return cur.rowcount > 0


def clear_all_employees() -> int:
    with get_conn() as conn:
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM payments")
        conn.execute("DELETE FROM paid_status")
        cur = conn.execute("DELETE FROM employees")
        return cur.rowcount


def get_employees_with_telegram_id() -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM employees WHERE telegram_id IS NOT NULL AND is_active = 1"
        ).fetchall()


# ── Attendance ───────────────────────────────────────────────────────────

def mark_attendance(employee_id: int, day: date = None, status: int = 1) -> bool:
    day = day or date.today()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)",
                (employee_id, day.isoformat(), status),
            )
            return True
    except sqlite3.IntegrityError:
        with get_conn() as conn:
            conn.execute(
                "UPDATE attendance SET status = ? WHERE employee_id = ? AND date = ?",
                (status, employee_id, day.isoformat()),
            )
            return True


def unmark_attendance(employee_id: int, day: date = None) -> bool:
    day = day or date.today()
    with get_conn() as conn:
        cur = conn.execute(
            "DELETE FROM attendance WHERE employee_id = ? AND date = ?",
            (employee_id, day.isoformat()),
        )
        return cur.rowcount > 0


def get_attendance_for_day(day: date = None) -> list:
    day = day or date.today()
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT e.id, e.first_name, e.last_name, a.status
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE a.date = ?
            ORDER BY e.first_name, e.last_name
            """,
            (day.isoformat(),),
        ).fetchall()


def get_attendance_count(employee_id: int, year: int, month: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM attendance
            WHERE employee_id = ? AND status = 1 
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """,
            (employee_id, str(year), f"{month:02d}"),
        ).fetchone()
        return row["cnt"] if row else 0


# ── Payments ─────────────────────────────────────────────────────────────

def add_payment(employee_id: int, amount: float, note: str = "") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO payments (employee_id, amount, date, note) VALUES (?, ?, ?, ?)",
            (employee_id, amount, date.today().isoformat(), note),
        )
        return cur.lastrowid


def get_total_paid(employee_id: int, year: int, month: int) -> float:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) as total FROM payments
            WHERE employee_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """,
            (employee_id, str(year), f"{month:02d}"),
        ).fetchone()
        return row["total"] if row else 0.0


def get_payments_for_month(employee_id: int, year: int, month: int) -> list:
    """Hodimning ma'lum oyda qilgan to'lovlarini olish"""
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT amount, date, note FROM payments
            WHERE employee_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date DESC
            """,
            (employee_id, str(year), f"{month:02d}"),
        ).fetchall()


# ── Paid Status (Hodim to'laganini belgilash) ────────────────────────────

def mark_as_paid(employee_id: int, year: int, month: int) -> bool:
    """Hodim oyligini to'laganini belgilash"""
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO paid_status (employee_id, year, month, is_paid) VALUES (?, ?, ?, 1)",
                (employee_id, year, month),
            )
            return True
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE paid_status SET is_paid = 1 WHERE employee_id = ? AND year = ? AND month = ?",
                (employee_id, year, month),
            )
            return True


def is_marked_as_paid(employee_id: int, year: int, month: int) -> bool:
    """Hodim oyligini to'laganmi yoki yo'qligini tekshirish"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT is_paid FROM paid_status WHERE employee_id = ? AND year = ? AND month = ?",
            (employee_id, year, month),
        ).fetchone()
        return row["is_paid"] == 1 if row else False


def unmark_as_paid(employee_id: int, year: int, month: int) -> bool:
    """Hodim to'lagan belgisini olib tashlash"""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE paid_status SET is_paid = 0 WHERE employee_id = ? AND year = ? AND month = ?",
            (employee_id, year, month),
        )
        return cur.rowcount > 0


# ── Balance ──────────────────────────────────────────────────────────────

def get_employee_balance(employee_id: int, year: int, month: int) -> dict:
    emp = get_employee(employee_id)
    if not emp:
        return {}
    
    attendance_count = get_attendance_count(employee_id, year, month)
    monthly_salary = emp["monthly_salary"]
    paid = get_total_paid(employee_id, year, month)
    
    # Hisoblash: kelgan kunlar * (oylik / 22)
    earned = attendance_count * (monthly_salary / WORKING_DAYS_PER_MONTH)
    debt = earned - paid
    is_paid = is_marked_as_paid(employee_id, year, month)
    
    return {
        "employee": emp,
        "attendance_count": attendance_count,
        "monthly_salary": monthly_salary,
        "earned": earned,  # Ishlab topgan puli
        "paid": paid,
        "debt": debt if debt > 0 else 0,
        "overpaid": -debt if debt < 0 else 0,
        "is_paid": is_paid,  # Hodim to'laganmi
    }


def get_monthly_summary(year: int, month: int) -> list:
    employees = get_employees(active_only=True)
    result = []
    for emp in employees:
        b = get_employee_balance(emp["id"], year, month)
        result.append(b)
    return result
