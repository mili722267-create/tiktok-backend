import os
import sqlite3
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# የቪዲዮ ፋይሎች እና የዳታቤዝ ስም መወሰን
UPLOAD_FOLDER = 'uploads'
DATABASE_FILE = 'tiktok_database.db'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 1. የSQLite ዳታቤዝ ሰንጠረዦችን በትክክል መፍጠሪያ (ስህተቱ የተስተካከለበት)
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # የተጠቃሚዎች ሰንጠረዥ (TEXT NOT NULL ተብሎ ተስተካክሏል)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0
        )
    ''')
    
    # የቪዲዮዎች ሰንጠረዥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            video_url TEXT,
            username TEXT,
            caption TEXT,
            likes INTEGER DEFAULT 0
        )
    ''')
    
    # መጀመሪያ ላይ አንድ ናሙና ቪዲዮ ማስገባት (ዳታቤዙ ባዶ ከሆነ)
    cursor.execute("SELECT COUNT(*) FROM videos")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO videos (id, video_url, username, caption, likes) 
            VALUES (?, ?, ?, ?, ?)
        """, ("vid_1", "/uploads/sample.mp4", "@eti_coder", "በስልክ ፒሲ ሳይኖር Python ኮድ መጻፍ! 🇪🇹 #python", 12500))
        
    conn.commit()
    conn.close()

# ዳታቤዙን መጀመሪያ ላይ ማስጀመር
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 2. አዲስ አካውንት መክፈቻ ኤፒአይ (User Signup)
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"status": "error", "message": "እባክዎ ስም እና ፓስወርድ ያስገቡ"}), 400
        
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"የ @{username} አካውንት በዳታቤዝ ውስጥ ተፈጥሯል!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "ይህ የስም አጠቃቀም ቀድሞ ተይዟል"}), 400

# 3. አዲስ ቪዲዮ መጫኛ ኤፒአይ (Video Upload)
@app.route('/api/upload', methods=['POST'])
def upload_video():
    username = request.form.get("username")
    caption = request.form.get("caption", "")
    
    if not username:
        return jsonify({"status": "error", "message": "እባክዎ የተጠቃሚ ስም ያስገቡ"}), 400
    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "ምንም የቪዲዮ ፋይል አልተላከም"}), 400
        
    file = request.files['video']
    if file.filename == '':
        return jsonify({"status": "error", "message": "ያልተመረጠ ፋይል"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # አዲስ ID ለመስጠት ያሉትን ቪዲዮዎች መቁጠር
        cursor.execute("SELECT COUNT(*) FROM videos")
        count = cursor.fetchone()[0]
        video_id = f"vid_{count + 1}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_{filename}")
        file.save(file_path)
        
        # መረጃውን ዳታቤዝ ውስጥ ማስቀመጥ
        cursor.execute("""
            INSERT INTO videos (id, video_url, username, caption, likes) 
            VALUES (?, ?, ?, ?, ?)
        """, (video_id, f"/{file_path}", f"@{username.replace('@', '')}", caption, 0))
        
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "ቪዲዮው በዳታቤዝ ውስጥ ተቀምጧል!", "video_id": video_id}), 201
        
    return jsonify({"status": "error", "message": "የተከለከለ የፋይል አይነት"}), 400

# 4. የቪዲዮዎችን ዝርዝር ከዳታቤዝ አውጥቶ ማሳያ ኤፒአይ (Video Feed)
@app.route('/api/feed', methods=['GET'])
def get_feed():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos")
    rows = cursor.fetchall()
    conn.close()
    
    videos = [dict(row) for row in rows]
    return jsonify({"status": "success", "data": videos}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
