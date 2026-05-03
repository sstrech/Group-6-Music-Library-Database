from flask import Flask, request, jsonify, send_from_directory, session, render_template
import psycopg2
import psycopg2.extras
import bcrypt
import os
from datetime import date
from dotenv import load_dotenv
from werkzeug.utils import redirect

load_dotenv()
required_vars = ["DB_NAME", "USERNAME", "PASSWORD", "HOST", "PORT"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")

app = Flask(__name__, static_folder='.')
app.secret_key = os.getenv('SECRET_KEY')

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": int(os.getenv("PORT"))
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

#Serve HTML
@app.route('/')
def serve_login():
    return render_template('login.html')

@app.route('/index.html')
def serve_index():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('index.html', username=session.get('username'))

@app.route('/login.html')
def login_html_route():
    session.clear()  # Clear session on logout
    return render_template('login.html')

#Signup
@app.route('/signup-process', methods=['POST'])
def signup():
    username  = request.form.get('signup-username')
    firstname = request.form.get('signup-firstname')
    lastname  = request.form.get('signup-lastname')
    email     = request.form.get('signup-email')
    password  = request.form.get('signup-password')

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_conn()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Users (u_Username, u_PasswordHash, u_FirstName, u_LastName, u_Email) VALUES (%s,%s,%s,%s,%s)",
            (username, pw_hash, firstname, lastname, email)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        cur.close()
        conn.close()
        return render_template('login.html', signup_error="Username or email already exists.")
    cur.close();
    conn.close()
    return render_template('login.html', signup_success="Account created successfully! Please log in.")

#Login
@app.route('/login-process', methods=['POST'])
def login():
    username = request.form.get('login-username')
    password = request.form.get('login-password')

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT * FROM Users WHERE u_Username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and bcrypt.checkpw(password.encode(), user['u_passwordhash'].encode()):
            session['user_id'] = user['u_userid']
            session['username'] = user['u_username']
            return render_template('index.html', username=session.get('username'))
    except Exception as e:
        cur.close()
        conn.close()
        return render_template('login.html', login_error=e)
    cur.close()
    conn.close()
    return render_template('login.html', login_error="Username or password incorrect.")


#Logout
@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')

#Who is logged in
@app.route('/api/me')
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'user_id': session['user_id'], 'username': session['username']})

#Listen History 
@app.route('/api/history')
def get_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT s.s_Name AS song, u.u_Username AS artist, lh.lr_ListenedTime AS played_at
        FROM ListenHistory lh
        JOIN Songs s   ON lh.lr_SongID  = s.s_SongID
        JOIN Artists a ON s.s_ArtistID  = a.art_ArtistID
        JOIN Users u   ON a.art_UserID  = u.u_UserID
        WHERE lh.lr_UserID = %s
        ORDER BY lh.lr_ListenedTime DESC
        LIMIT 20
    """, (session['user_id'],))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/history', methods=['POST'])
def add_history():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    song_id = request.json.get('song_id')
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO ListenHistory (lr_ListenedTime, lr_UserID, lr_SongID)
        VALUES (%s, %s, %s)
        ON CONFLICT (lr_UserID, lr_SongID) DO UPDATE SET lr_ListenedTime = EXCLUDED.lr_ListenedTime
    """, (int(date.today().strftime('%Y%m%d')), session['user_id'], song_id))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

#Search Songs
@app.route('/api/songs')
def search_songs():
    name   = request.args.get('name', '')
    artist = request.args.get('artist', '')
    album  = request.args.get('album', '')
    genre  = request.args.get('genre', '')

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT s.s_SongID, s.s_Name, s.s_Length, s.s_ReleaseDate,
               u.u_Username AS artist_name,
               g.g_Name     AS genre_name,
               al.al_Name   AS album_name
        FROM Songs s
        LEFT JOIN Artists a      ON s.s_ArtistID    = a.art_ArtistID
        LEFT JOIN Users u        ON a.art_UserID     = u.u_UserID
        LEFT JOIN Genres g       ON s.s_GenreID      = g.g_GenreID
        LEFT JOIN AlbumSongs als ON s.s_SongID       = als.als_SongID
        LEFT JOIN Albums al      ON als.als_AlbumID  = al.al_AlbumID
        WHERE (%s = '' OR s.s_Name     ILIKE '%%' || %s || '%%')
          AND (%s = '' OR u.u_Username ILIKE '%%' || %s || '%%')
          AND (%s = '' OR al.al_Name   ILIKE '%%' || %s || '%%')
          AND (%s = '' OR g.g_Name     ILIKE %s)
        LIMIT 50
    """, (name, name, artist, artist, album, album, genre, genre))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

#Playlists
@app.route('/api/playlists')
def get_playlists():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT pl_PlaylistID, pl_Name, pl_CreatedAt FROM Playlists WHERE pl_UserID = %s ORDER BY pl_CreatedAt DESC",
        (session['user_id'],)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    name = request.json.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO Playlists (pl_Name, pl_CreatedAt, pl_UserID) VALUES (%s, %s, %s)",
        (name, date.today(), session['user_id'])
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

@app.route('/api/playlists/<int:pl_id>', methods=['DELETE'])
def delete_playlist(pl_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "DELETE FROM Playlists WHERE pl_PlaylistID = %s AND pl_UserID = %s",
        (pl_id, session['user_id'])
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

@app.route('/api/playlists/<int:pl_id>/songs')
def get_playlist_songs(pl_id):
    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT s.s_SongID, s.s_Name, u.u_Username AS artist_name
        FROM PlaylistSongs ps
        JOIN Songs s        ON ps.ps_SongID    = s.s_SongID
        LEFT JOIN Artists a ON s.s_ArtistID    = a.art_ArtistID
        LEFT JOIN Users u   ON a.art_UserID     = u.u_UserID
        WHERE ps.ps_PlaylistID = %s
    """, (pl_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/playlists/<int:pl_id>/songs', methods=['POST'])
def add_song_to_playlist(pl_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    song_id = request.json.get('song_id')
    conn = get_conn()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO PlaylistSongs (ps_PlaylistID, ps_SongID) VALUES (%s, %s)",
            (pl_id, song_id)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        cur.close(); conn.close()
        return jsonify({'error': 'Song already in playlist'}), 409
    cur.close(); conn.close()
    return jsonify({'success': True})

@app.route('/api/playlists/<int:pl_id>/songs/<int:song_id>', methods=['DELETE'])
def remove_song_from_playlist(pl_id, song_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "DELETE FROM PlaylistSongs WHERE ps_PlaylistID = %s AND ps_SongID = %s",
        (pl_id, song_id)
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

#Following
@app.route('/api/following')
def get_following():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT u.u_UserID, u.u_Username, f.f_CreatedAt
        FROM Follows f
        JOIN Users u ON f.f_FollowedID = u.u_UserID
        WHERE f.f_FollowerID = %s
        ORDER BY f.f_CreatedAt DESC
    """, (session['user_id'],))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route('/api/following', methods=['POST'])
def follow_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    followed_id = request.json.get('followed_id')
    conn = get_conn()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Follows (f_FollowerID, f_FollowedID, f_CreatedAt) VALUES (%s, %s, %s)",
            (session['user_id'], followed_id, date.today())
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        cur.close(); conn.close()
        return jsonify({'error': 'Already following'}), 409
    cur.close(); conn.close()
    return jsonify({'success': True})

@app.route('/api/following/<int:followed_id>', methods=['DELETE'])
def unfollow_user(followed_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(
        "DELETE FROM Follows WHERE f_FollowerID = %s AND f_FollowedID = %s",
        (session['user_id'], followed_id)
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

#Song Ratings
@app.route('/api/ratings/song', methods=['POST'])
def rate_song():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    song_id = request.json.get('song_id')
    rating  = request.json.get('rating')

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO SongRatings (sr_Rating, sr_CreateDate, sr_UserID, sr_SongID)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (sr_UserID, sr_SongID) DO UPDATE SET sr_Rating = EXCLUDED.sr_Rating
    """, (rating, date.today(), session['user_id'], song_id))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

#Artist Upload
@app.route('/api/upload', methods=['POST'])
def upload_song():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    data       = request.json
    title      = data.get('title')
    genre_name = data.get('genre')
    length     = data.get('length', 180)
    release    = data.get('release_date', str(date.today()))

    conn = get_conn()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get genre ID — must already exist
    cur.execute("SELECT g_GenreID FROM Genres WHERE g_Name = %s", (genre_name,))
    genre = cur.fetchone()
    if not genre:
        cur.close(); conn.close()
        return jsonify({'error': 'Genre not found'}), 400
    genre_id = genre['g_genreid']

    # Get or create artist record for this user
    cur.execute("SELECT art_ArtistID FROM Artists WHERE art_UserID = %s", (session['user_id'],))
    artist = cur.fetchone()
    if not artist:
        cur.execute("INSERT INTO Artists (art_UserID) VALUES (%s) RETURNING art_ArtistID", (session['user_id'],))
        artist = cur.fetchone()
    artist_id = artist['art_artistid']

    # Insert the song
    cur.execute(
        "INSERT INTO Songs (s_Name, s_Length, s_ReleaseDate, s_ArtistID, s_GenreID) VALUES (%s,%s,%s,%s,%s)",
        (title, length, release, artist_id, genre_id)
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify({'success': True})

#Run
if __name__ == '__main__':
    app.run(debug=True)