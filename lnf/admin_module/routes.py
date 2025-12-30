# admin_module/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db

admin_app = Blueprint('admin_app', __name__, template_folder='templates')

# @admin_app.route('/dashboard')
# def dashboard():
#     return render_template('admin_dashboard.html')
@admin_app.route('/dashboard')
def dashboard():
    db = get_db()
    #cursor = db.cursor(dictionary=True)
    #cursor = db.cursor(buffered=True, dictionary=True)
    cursor = db.cursor()

    # Total categories
    cursor.execute("SELECT COUNT(*) AS total_categories FROM category")
    total_categories = cursor.fetchone()['total_categories']

    # Total users
    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    # Lost items (status = 0)
    cursor.execute("SELECT COUNT(*) AS total_lost FROM items WHERE status = 0")
    total_lost = cursor.fetchone()['total_lost']

    # Found items (status = 1)
    cursor.execute("SELECT COUNT(*) AS total_found FROM items WHERE status = 1")
    total_found = cursor.fetchone()['total_found']

    # Top 5 ranked users
    cursor.execute("""
        SELECT 
            users.id,
            users.username,
            SUM(user_ranks.rank) AS total_rank
        FROM users
        JOIN user_ranks ON users.id = user_ranks.user_id
        GROUP BY users.id, users.username
        ORDER BY total_rank DESC
        LIMIT 5
    """)
    top_users = cursor.fetchall()

    return render_template(
        'admin_dashboard.html',
        total_categories=total_categories,
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        top_users=top_users
    )

