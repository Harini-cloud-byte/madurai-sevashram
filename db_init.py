import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

# ---------------- ADMIN ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ---------------- EVENTS (UPDATED) ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    datetime TEXT,
    location TEXT,
    description TEXT,
    image TEXT
)
""")

# ---------------- REPORTS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year TEXT,
    file TEXT
)
""")

# ---------------- GALLERY ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS gallery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image TEXT,
    category TEXT
)
""")

# ---------------- FEEDBACK (UPDATED) ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    phone TEXT,
    message TEXT
)
""")

# ---------------- HOME SETTINGS ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS home_settings (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    bgcolor TEXT,
    textcolor TEXT
)
""")

# ---------------- DEFAULT HOME DATA ----------------
c.execute("SELECT * FROM home_settings WHERE id=1")
if not c.fetchone():
    c.execute("""
    INSERT INTO home_settings (id, title, description, bgcolor, textcolor)
    VALUES (
        1,
        'Madurai Sevashram',
        'Serving Humanity • Education • Healthcare • Empowerment',
        '#eef5ff',
        '#1e293b'
    )
    """)

# ---------------- SAVE ----------------
db.commit()
db.close()

print("Database Ready ✅")
