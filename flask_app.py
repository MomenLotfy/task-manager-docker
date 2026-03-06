from flask import Flask, jsonify, request, render_template_string
import os, datetime, json
import psycopg2
import redis

app = Flask(__name__)

# DB connection
def get_db():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        database=os.environ.get("POSTGRES_DB", "bookstore"),
        user=os.environ.get("POSTGRES_USER", "appuser"),
        password=os.environ.get("POSTGRES_PASSWORD", "secret"),
        connect_timeout=5,
    )

# Redis connection
def get_redis():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "redis"),
        port=6379, decode_responses=True, socket_timeout=3,
    )

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>📚 BookStore API</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div class="container">
    <h1>📚 BookStore API</h1>
    <div class="info-grid">
      <div class="info-card">
        <div class="label">Worker</div>
        <div class="value">{{ worker }}</div>
      </div>
      <div class="info-card">
        <div class="label">Time</div>
        <div class="value">{{ time }}</div>
      </div>
      <div class="info-card">
        <div class="label">DB Status</div>
        <div class="value {{ 'ok' if db_ok else 'err' }}">{{ 'Connected ✓' if db_ok else 'Error ✗' }}</div>
      </div>
      <div class="info-card">
        <div class="label">Redis Status</div>
        <div class="value {{ 'ok' if redis_ok else 'err' }}">{{ 'Connected ✓' if redis_ok else 'Error ✗' }}</div>
      </div>
    </div>
    <div class="endpoints">
      <h2>API Endpoints</h2>
      <a href="/api/books" class="btn">GET /api/books</a>
      <a href="/api/health" class="btn green">GET /api/health</a>
    </div>
    <div class="add-form">
      <h2>Add a Book</h2>
      <input id="title" placeholder="Book Title" type="text">
      <input id="author" placeholder="Author" type="text">
      <button onclick="addBook()">Add Book</button>
      <div id="msg"></div>
    </div>
  </div>
  <script>
    async function addBook() {
      const title = document.getElementById('title').value;
      const author = document.getElementById('author').value;
      const r = await fetch('/api/books', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({title, author})
      });
      const d = await r.json();
      document.getElementById('msg').textContent = d.message || d.error;
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    db_ok, redis_ok = False, False
    try:
        db = get_db(); db.close(); db_ok = True
    except: pass
    try:
        r = get_redis(); r.ping(); redis_ok = True
    except: pass
    return render_template_string(HTML,
        worker=os.environ.get("SERVER_NAME", "flask"),
        time=datetime.datetime.now().strftime("%H:%M:%S"),
        db_ok=db_ok, redis_ok=redis_ok
    )

@app.route("/api/health")
def health():
    db_ok, redis_ok = False, False
    try: db=get_db(); db.close(); db_ok=True
    except: pass
    try: r=get_redis(); r.ping(); redis_ok=True
    except: pass
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    return jsonify({"status":status, "worker":os.environ.get("SERVER_NAME","flask"),
                    "db":db_ok, "redis":redis_ok, "time":str(datetime.datetime.now())}), 200 if status=="healthy" else 503

@app.route("/api/books", methods=["GET"])
def get_books():
    try:
        r = get_redis()
        cached = r.get("books:all")
        if cached:
            return jsonify({"books": json.loads(cached), "source":"cache (redis)"})
    except: pass
    try:
        db = get_db(); cur = db.cursor()
        cur.execute("SELECT id, title, author, created_at FROM books ORDER BY id DESC LIMIT 50")
        books = [{"id":row[0],"title":row[1],"author":row[2],"created_at":str(row[3])} for row in cur.fetchall()]
        cur.close(); db.close()
        try: r.setex("books:all", 60, json.dumps(books))
        except: pass
        return jsonify({"books":books, "source":"database"})
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.get_json(silent=True) or {}
    title = data.get("title","").strip()
    author = data.get("author","").strip()
    if not title or not author:
        return jsonify({"error":"title and author required"}), 400
    try:
        db = get_db(); cur = db.cursor()
        cur.execute("INSERT INTO books (title, author) VALUES (%s, %s) RETURNING id", (title, author))
        book_id = cur.fetchone()[0]; db.commit(); cur.close(); db.close()
        try: get_redis().delete("books:all")
        except: pass
        return jsonify({"message":"Book added!", "id":book_id}), 201
    except Exception as e:
        return jsonify({"error":str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
