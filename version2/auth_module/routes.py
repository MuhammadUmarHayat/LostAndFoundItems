# auth_routes.py
from flask import Blueprint, render_template, request
from flask import flash, session, redirect, url_for
from db import get_db

auth_app = Blueprint('auth_app', __name__, template_folder='templates')

@auth_app.route('/signup', methods=['GET', 'POST'])
def signup():  #`sec_question`, `sec_answer`
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        mobile = request.form['mobile']
        address = request.form['address']
        user_type = "customer"
        sq=request.form['sq']
        sa= request.form['sa']
        status = "ok"
        return signup_user(username, name, email, password, mobile, address, user_type,sq,sa, status)
    return render_template('signup.html')

@auth_app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        return login_user(username, password, user_type)
    return render_template('login.html')

@auth_app.route('/logout')
def logout():
    # Return the result of logout_user
    return logout_user()
    
   
################################ Method definations #################

def signup_user(username, name, email, password, mobile, address, user_type,sq,sa,status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO users (username, name, email, password, mobile, address, user_type,sec_question,sec_answer, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s,%s, %s, %s)
    """, (username, name, email, password, mobile, address, user_type,sq,sa,status))
    db.commit()
    flash('Signup successful. Please login.')
    return redirect(url_for('auth_app.login'))

def login_user(username, password, user_type):
    db = get_db()
    cursor = db.cursor()

    # Admin login
    if username == 'admin' and password == 'admin' and user_type == 'admin':
        session['username'] = username
        session['type'] = 'admin'
        return redirect(url_for('admin_app.dashboard'))

    # Customer login
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()

    if user:
        session['username'] = username
        session['type'] = 'customer'
        return redirect(url_for('customer_app.home'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('auth_app.login'))

def logout_user():
    session.pop('username', None)
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('auth_app.login'))  # Redirect to login page

from datetime import date

# today = date.today()

@auth_app.route("/contactus", methods=["GET", "POST"])
def contactus():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message= request.form["message"]
        msg_date = date.today()
        status="message"

        ""
        return saveContactus(name, email, message, msg_date, status)
    return render_template('index.html')


def saveContactus(name, email, message, msg_date, status):
     db = get_db()
     cursor = db.cursor()
     cursor.execute("""
        INSERT INTO contactus(name, email, message, msg_date, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, message, msg_date, status))
     db.commit()
     #flash('Signup successful. Please login.')
     return redirect(url_for('index'))

def get_user_feedback():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT name, message, msg_date
        FROM contactus
        WHERE status = 'message'
        ORDER BY msg_date DESC
        LIMIT 6
    """)
    return cursor.fetchall()

     


