import os
import sqlite3
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# የሰራነውን የቲክቶክ አልጎሪዝም ወደዚህ ማምጣት (Import)
from recommendation import TikTokRecommendationEngine

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DATABASE_FILE = 'tiktok_database.db'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            video_url TEXT,
            username TEXT,
            caption TEXT,
            likes INTEGER DEFAULT 0,
            tags TEXT
        )
    ''')
    
    # የናሙና ቪዲዮዎች ከሃሽታግ (Tags) ጋር መመዝገብ
    cursor.execute("SELECT COUNT(*) FROM videos")
    if cursor.fetchone() == 0:
        cursor.execute("INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?)", 
                       ("vid_1", "/uploads/dance.mp4", "@eti_coder", "አዲስ የዳንስ ቻሌንጅ! 🔥 #dance", 12500, "dance,fyp"))
        cursor.execute("INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?)", 
                       ("vid_2", "/uploads/cook.mp4", "@habesha_tech", "የፓስታ አሰራር 🍝 #cooking", 89300, "cooking,recipe"))
    conn.commit()
    conn.close()

init_db()
# የቲክቶክ 'For You' ገጽ አልጎሪዝም የተገጠመለት ኤፒአይ
@app.route('/api/feed', methods=['GET'])
def get_algo_feed():
    # የውሸት ተጠቃሚ የፍላጎት ታሪክ (cooking ይወዳል)
    mock_user_history = {
        "watch_percentage": 0.95,
        "liked": True,
        "shared": False,
        "favorite_tags": ["cooking", "recipe"]
    }
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos")
    rows = cursor.fetchall()
    conn.close()
    
    all_videos = []
    for row in rows:
        v_dict = dict(row)
        v_dict['tags'] = v_dict['tags'].split(',') if v_dict.get('tags') else []
        all_videos.append(v_dict)
    
    # አልጎሪዝሙን አስነስቶ ቪዲዮዎቹን በደረጃ ነጥብ ማደራጀት
    engine = TikTokRecommendationEngine(mock_user_history)
    personalized_feed = engine.rank_videos(all_videos)
    
    return jsonify({
        "status": "success",
        "message": "አልጎሪዝሙ የመረጣቸው የ For You ቪዲዮዎች",
        "data": personalized_feed
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
