"""
Telegram Mini App - Backend API
Flask-based API for the Lunch Tracker Mini App
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import date

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'lunch_tracker.db')


def get_db():
    """Database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Serve the mini app"""
    return render_template('index.html')


@app.route('/api/user/<int:telegram_id>')
def get_user(telegram_id):
    """Get user info by Telegram ID"""
    conn = get_db()
    try:
        emp = conn.execute(
            "SELECT * FROM employees WHERE telegram_id = ? AND is_active = 1",
            (telegram_id,)
        ).fetchone()
        
        if not emp:
            # Foydalanuvchi topilmadi - ro'yxatdan o'tmagan
            return jsonify({
                'registered': False,
                'telegram_id': telegram_id,
                'message': 'Siz hali ro\'yxatdan o\'tmagansiz'
            }), 200
        
        return jsonify({
            'registered': True,
            'id': emp['id'],
            'first_name': emp['first_name'],
            'last_name': emp['last_name'],
            'position': emp['position'],
            'monthly_salary': emp['monthly_salary']
        })
    finally:
        conn.close()


@app.route('/api/balance/<int:employee_id>')
def get_balance(employee_id):
    """Get employee balance"""
    conn = get_db()
    try:
        today = date.today()
        year, month = today.year, today.month
        
        emp = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not emp:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Attendance
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM attendance 
               WHERE employee_id = ? AND status = 1 
               AND strftime('%Y', date) = ? AND strftime('%m', date) = ?""",
            (employee_id, str(year), f"{month:02d}")
        ).fetchone()
        attendance_count = row['cnt'] if row else 0
        
        # Payments
        payments = conn.execute(
            """SELECT amount, date, note FROM payments 
               WHERE employee_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
               ORDER BY date DESC""",
            (employee_id, str(year), f"{month:02d}")
        ).fetchall()
        
        total_paid = sum(p['amount'] for p in payments)
        daily_rate = emp['monthly_salary'] / 22
        earned = attendance_count * daily_rate
        debt = earned - total_paid
        
        # Paid status
        row = conn.execute(
            "SELECT is_paid FROM paid_status WHERE employee_id = ? AND year = ? AND month = ?",
            (employee_id, year, month)
        ).fetchone()
        is_paid = row['is_paid'] == 1 if row else False
        
        return jsonify({
            'employee': {
                'id': emp['id'],
                'name': f"{emp['first_name']} {emp['last_name'] or ''}".strip(),
                'position': emp['position']
            },
            'month': month,
            'year': year,
            'attendance_count': attendance_count,
            'daily_rate': round(daily_rate, 2),
            'earned': round(earned, 2),
            'paid': round(total_paid, 2),
            'debt': round(debt, 2) if debt > 0 else 0,
            'is_paid': is_paid,
            'payments': [{'amount': p['amount'], 'date': p['date'], 'note': p['note']} for p in payments]
        })
    finally:
        conn.close()


@app.route('/api/today')
def get_today():
    """Get today's attendance"""
    conn = get_db()
    try:
        today = date.today()
        records = conn.execute(
            """SELECT e.id, e.first_name, e.last_name, a.status
               FROM attendance a
               JOIN employees e ON e.id = a.employee_id
               WHERE a.date = ?
               ORDER BY e.first_name""",
            (today.isoformat(),)
        ).fetchall()
        
        present = [r for r in records if r['status'] == 1]
        absent = [r for r in records if r['status'] == 0]
        
        return jsonify({
            'date': today.isoformat(),
            'present': [{'id': r['id'], 'name': f"{r['first_name']} {r['last_name'] or ''}".strip()} for r in present],
            'absent': [{'id': r['id'], 'name': f"{r['first_name']} {r['last_name'] or ''}".strip()} for r in absent]
        })
    finally:
        conn.close()


@app.route('/api/mark-paid', methods=['POST'])
def mark_paid():
    """Mark as paid"""
    data = request.json
    employee_id = data.get('employee_id')
    
    if not employee_id:
        return jsonify({'error': 'Employee ID required'}), 400
    
    conn = get_db()
    try:
        today = date.today()
        conn.execute(
            """INSERT INTO paid_status (employee_id, year, month, is_paid) 
               VALUES (?, ?, ?, 1)
               ON CONFLICT(employee_id, year, month) 
               DO UPDATE SET is_paid = 1""",
            (employee_id, today.year, today.month)
        )
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()


@app.route('/api/admin/summary')
def admin_summary():
    """Admin summary"""
    conn = get_db()
    try:
        today = date.today()
        year, month = today.year, today.month
        
        employees = conn.execute("SELECT * FROM employees WHERE is_active = 1").fetchall()
        
        summary = []
        for emp in employees:
            row = conn.execute(
                """SELECT COUNT(*) as cnt FROM attendance 
                   WHERE employee_id = ? AND status = 1 
                   AND strftime('%Y', date) = ? AND strftime('%m', date) = ?""",
                (emp['id'], str(year), f"{month:02d}")
            ).fetchone()
            attendance_count = row['cnt'] if row else 0
            
            row = conn.execute(
                """SELECT COALESCE(SUM(amount), 0) as total FROM payments 
                   WHERE employee_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?""",
                (emp['id'], str(year), f"{month:02d}")
            ).fetchone()
            total_paid = row['total'] if row else 0
            
            earned = attendance_count * (emp['monthly_salary'] / 22)
            
            summary.append({
                'id': emp['id'],
                'name': f"{emp['first_name']} {emp['last_name'] or ''}".strip(),
                'attendance_count': attendance_count,
                'earned': round(earned, 2),
                'paid': round(total_paid, 2),
                'debt': round(max(0, earned - total_paid), 2)
            })
        
        return jsonify({
            'month': month,
            'year': year,
            'employees': summary
        })
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
