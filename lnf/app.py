# app.py
from flask import Flask, render_template
from config import *
from db import close_db
from auth_module.routes import auth_app
from admin_module.routes import admin_app
from customer_module.routes import customer_app
from db import get_db

app = Flask(__name__)
app.secret_key = 'atiya_and_khadija'
app.debug = True  # Enables debugging
app.config.from_object('config')
app.teardown_appcontext(close_db)

# Register Blueprints
app.register_blueprint(auth_app, url_prefix='/auth')
app.register_blueprint(admin_app, url_prefix='/admin')
app.register_blueprint(customer_app, url_prefix='/customer')

# --- File Upload Configuration ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    q = """
    SELECT user_name, SUM(`rank`) AS consolidated_rank
    FROM ranks
    GROUP BY user_name
    ORDER BY consolidated_rank DESC
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute(q)
    ranks = cursor.fetchall()

    print(ranks)  # DEBUG – must show data

    return render_template('index.html', ranks=ranks)





if __name__ == '__main__':
    app.run(debug=True)
