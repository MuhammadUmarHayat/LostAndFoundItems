# routes.py
from flask import Blueprint, session, render_template, request, redirect, url_for, flash
from db import get_db
import os
from werkzeug.utils import secure_filename

import numpy as np

from flask import request, render_template, flash
import numpy as np
from customer_module.model import extract_features
#from model import extract_features
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image, PngImagePlugin
from datetime import datetime


customer_app = Blueprint('customer_app', __name__, template_folder='templates')

# Folders
# UPLOAD_LOST_FOLDER = os.path.join(os.getcwd(), "lostItems")
# UPLOAD_FOUND_FOLDER = os.path.join(os.getcwd(), "foundItems")
UPLOAD_LOST_FOLDER = os.path.join("static", "lostItems")
UPLOAD_FOUND_FOLDER = os.path.join("static", "foundItems")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# ------------------------------
# Helper Functions
# ------------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def mse(img1, img2):
    return np.mean((img1.astype("float") - img2.astype("float")) ** 2)


# ------------------------------
# Home Page
# ------------------------------
@customer_app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("auth_app.login"))

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM items WHERE status = 1")
    items = cursor.fetchall()# returns tuples

    return render_template("home.html", items=items)


# ------------------------------
# Lost/Found Image Matching
# ------------------------------
#new match model

@customer_app.route("/match", methods=["GET", "POST"])
def match_items():
    if request.method == "POST":
        uploaded = request.files["photo"]
        lost_path = os.path.join(UPLOAD_LOST_FOLDER, uploaded.filename)
        uploaded.save(lost_path)
        #check image is living thing or not
        file=is_living_thing(uploaded )
        if(file):
             flash(f"This model is not working on living things . Please upload image of non living thing ")
             return render_template("match.html")
        
        
        
        #read image
        read_data=readLostItem(uploaded)
        print(read_data)
        # Extract features for uploaded (lost) image
        lost_feat = extract_features(lost_path)

        best_match_file = None
        best_similarity = 0

        # Loop through all FOUND images
        for file in os.listdir(UPLOAD_FOUND_FOLDER):
            found_path = os.path.join(UPLOAD_FOUND_FOLDER, file)

            found_feat = extract_features(found_path)

            # Compute similarity (0–1)
            sim = cosine_similarity([lost_feat], [found_feat])[0][0]

            if sim > best_similarity:
                best_similarity = sim
                best_match_file = file

        # Convert similarity to percentage accuracy
        accuracy = round(best_similarity * 100, 2)

        if best_similarity > 0.70:   # threshold 70%
                      

            flash(f"Reported By User ID: {read_data['user_id']}")
            flash(f"Reported Date: {read_data['date']}")
            flash(f"Status: {read_data['status']}")
            flash(f"Accuracy: {accuracy}%")

        else:
            #flash(f"No match found! Best accuracy = {accuracy}%")
            flash(f"No match found! Best accuracy = 0%")

    return render_template("match.html")




"""
######################old match method###############
@customer_app.route("/match", methods=["GET", "POST"])
def match_items():
    if request.method == "POST":
        uploaded = request.files["photo"]
        lost_path = os.path.join(UPLOAD_LOST_FOLDER, uploaded.filename)
        uploaded.save(lost_path)

        min_error = 999999
        match_file = None

        for file in os.listdir(UPLOAD_FOUND_FOLDER):
            found_path = os.path.join(UPLOAD_FOUND_FOLDER, file)

            lost_img = np.array(Image.open(lost_path).resize((256, 256)))
            found_img = np.array(Image.open(found_path).resize((256, 256)))

            error = mse(lost_img, found_img)
            if error < min_error:
                min_error = error
                match_file = file

        if min_error < 100:
            flash(f"Match found: {match_file}")
            #flash(f"Match found: {match_file} (error={min_error})")
        else:
            flash("No match found!")

    return render_template("match.html")

"""

# ------------------------------
# Add Found Items
# ------------------------------
@customer_app.route("/found-items", methods=["GET", "POST"])
def foundItems():
    
    if request.method == "POST":
        title = request.form["title"]
        found_by = request.form["found_by"]
        found_date = request.form["found_date"]
        remarks = request.form["remarks"]
        status = 1
       
        file = request.files["photo"]
        photo_path = None
        print(found_by)
       # getUserID(found_by)
        #exit() 

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = os.path.splitext(filename)[0] + ".png" 
            os.makedirs(UPLOAD_FOUND_FOLDER, exist_ok=True)
            saved_path = os.path.join(UPLOAD_FOUND_FOLDER, filename)
            # Save the image with metadata
            img = Image.open(file)
            #image copy writing
            # Prepare metadata
            meta = PngImagePlugin.PngInfo()
            meta.add_text("user_id", str(found_by))
            meta.add_text("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            meta.add_text("status", "found")

            img.save(saved_path, pnginfo=meta)

            photo_path = f"foundItems/{filename}"
##############################
            #meta = img.info
            #print(meta)
            # user_id = meta.get("user_id", )
            # date = meta.get("date", )
            # status = meta.get("status", "Unknown")

            # print(user_id)
            # print (date)
            # print (status)
         

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO founds (photo, title, found_by, found_date, remarks, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (photo_path, title, found_by, found_date, remarks, status))

        db.commit()
        
        rank=1

        # saveRank(found_by,  rank, remarks, status, found_date)
        saveRank(found_by,rank,found_date)

        flash("Found item added successfully!")
        return redirect(url_for("customer_app.foundItems"))

    return render_template("found_items.html")

from PIL import Image, PngImagePlugin
from datetime import datetime

@customer_app.route("/lost-items", methods=["GET", "POST"])
def lostItems():
    db = get_db()
    cursor = db.cursor()

    # Fetch categories
    cursor.execute("SELECT id, title FROM category WHERE status = 1")
    categories = cursor.fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category_id = request.form["category_id"]
        user_id = request.form["username"]
        remarks = request.form["remarks"]
        status = 1

        file = request.files["photo"]
        photo_path = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = os.path.splitext(filename)[0] + ".png" 

            os.makedirs(UPLOAD_LOST_FOLDER, exist_ok=True)
            saved_path = os.path.join(UPLOAD_LOST_FOLDER, filename)

            # Save the image with metadata
            img = Image.open(file)

            # Prepare metadata
            meta = PngImagePlugin.PngInfo()
            meta.add_text("user_id", str(user_id))
            meta.add_text("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            meta.add_text("status", "lost")

            img.save(saved_path, pnginfo=meta)

            photo_path = f"lostItems/{filename}"

        cursor.execute("""
            INSERT INTO items (title, description, category_id, status, user_id, remarks, photo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, description, category_id, status, user_id, remarks, photo_path))

        db.commit()

        flash("Lost item added successfully!")
        return redirect(url_for("customer_app.lostItems"))

    return render_template("lost_items.html", categories=categories)

from PIL import Image

def readLostItem(file_name):
    img = Image.open(file_name)
    meta = img.info
    print(meta)
    user_id = meta.get("user_id", "Unknown")
    date = meta.get("date", "Unknown")
    status = meta.get("status", "Unknown")
    
    data = {
        "user_id": user_id,
        "date": date,
        "status": status
    }

    return data   


   
# ------------------------------
# Search Items
# ------------------------------
@customer_app.route("/search", methods=["GET", "POST"])
def search():
    items = []
    if request.method == "POST":
        keyword = "%" + request.form["keyword"] + "%"
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM items 
            WHERE title LIKE %s OR description LIKE %s
        """, (keyword, keyword))
        items = cursor.fetchall()

    return render_template("home.html", items=items)

############################category 

@customer_app.route('/add', methods=['GET', 'POST'])
def add_category():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        cursor.execute("INSERT INTO `category`(`title`, `description`)  VALUES (%s,%s)",
                       (title, description))
        db.commit()
        flash('category is  added successfully.')
        return redirect(url_for('customer_app.list_category')) #return redirect(url_for('admin_app.list_category'))
    return render_template('add_category.html')

@customer_app.route('/list')
def list_category():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM category")
    categories = cursor.fetchall()
    return render_template('list_category.html', categories=categories)

@customer_app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        
        status = int(request.form['status'])
        
        cursor.execute("UPDATE category SET title=%s, description=%s, status=%s WHERE id=%s",
               (title, description,  status, id))
        db.commit()
       # flash('Category is  updated successfully.')
        return redirect(url_for('customer_app.list_category'))

    cursor.execute("SELECT * FROM category WHERE id=%s", (id,))
    item = cursor.fetchone()
    return render_template('edit_category.html', item=item)

@customer_app.route('/delete/<int:id>')
def delete_category(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM category WHERE id=%s", (id,))
    db.commit()
    flash('Product deleted successfully.')
    return redirect(url_for('customer_app.list_category'))


# ------------------------------
# Logout
# ------------------------------
# @customer_app.route("/logout")
# def logout():
#     session.clear()
#     return render_template("login.html")

#import numpy as np
#from PIL import Image
import tensorflow as tf

# Load pretrained model once
model = tf.keras.applications.MobileNetV2(weights="imagenet")
#use imagenet model for binary classification

def is_living_thing(image_file):
    # Load image
    img = Image.open(image_file).convert("RGB")
    img = img.resize((224, 224))

    # Preprocess
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)

    # Predict
    predictions = model.predict(img_array)
    decoded = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=3)[0]

    # Living categories keywords
    living_keywords = [
        "dog", "cat", "bird", "cow", "horse", "sheep", "person",
        "human", "plant", "tree", "flower", "fish", "insect",
        "lion", "tiger", "bear", "monkey"
    ]

    for _, label, confidence in decoded:
        for word in living_keywords:
            if word in label.lower():
                return True

    return False

def saveRank(user_name,rank, date):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
            INSERT INTO ranks(user_name,rank, date)
                    
            VALUES ( %s, %s,  %s)
        """, (user_name,rank, date))

    db.commit()


   
    return id

def getUserID(username):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT id FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    
    result = cursor.fetchone()
    print(result[0])
    # if result:
    #     return result[0]
    # else:
    #     return None
