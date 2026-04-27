import sqlite3

# =========================
# CONNECTION + AUTO TABLE INIT
# =========================
def get_connection():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # create table once safely
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    conn.commit()
    return conn


# =========================
# REGISTER USER
# =========================
def register_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        username = username.strip().lower()
        role = role.strip().lower()

        # check if user exists
        cursor.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )

        if cursor.fetchone():
            return False

        # insert user
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )

        conn.commit()
        return True

    except Exception as e:
        print("REGISTER ERROR:", e)
        return False

    finally:
        conn.close()


# =========================
# LOGIN USER
# =========================
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    username = username.strip().lower()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )

    user = cursor.fetchone()
    conn.close()
    return user


# =========================
# GET ALL STUDENTS
# =========================
def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users WHERE role='student'")
    students = [{"username": row[0]} for row in cursor.fetchall()]

    conn.close()
    return students