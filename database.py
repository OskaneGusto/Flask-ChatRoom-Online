# database.py
import sqlite3
import bcrypt
from datetime import datetime
import os

DATABASE = 'chatroom.db'


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        avatar TEXT ,
        bio TEXT,
        location TEXT,
        website TEXT,
        created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now'))
         
    )''')                   ##last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    # 房间表
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
        )''')

    # 消息表
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # # 创建消息表
    # c.execute('''CREATE TABLE IF NOT EXISTS messages (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     user_id INTEGER NOT NULL,
    #     room TEXT NOT NULL,
    #     message TEXT NOT NULL,
    #     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     FOREIGN KEY (user_id) REFERENCES users (id)
    # )''')

    # 创建日志表
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # 用户-房间关联表（新增）
    c.execute('''CREATE TABLE IF NOT EXISTS rooms_users (
            user_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, room_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
    )''')


    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DATABASE)


def create_user(username, password,avatar, created_at,last_seen):
    conn = get_db()
    c = conn.cursor()

    # 检查用户名是否存在
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return False

    # 哈希密码
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 插入新用户
    c.execute("INSERT INTO users (username, password, avatar, created_at,last_seen) VALUES (?, ?, ?, ?,?)",
              (username, hashed_password, avatar, created_at,last_seen))
    # c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
    #           (username, hashed_password))
    conn.commit()

    user_id = c.lastrowid
    conn.close()

    return user_id


def verify_user(username, password):
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if not user:
        return None

    user_id, hashed_password = user
    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        return user_id

    return None


def save_message(user_id, room, message):
    conn = get_db()
    c = conn.cursor()

    c.execute("INSERT INTO messages (user_id, room, message) VALUES (?, ?, ?)",
              (user_id, room, message))
    conn.commit()
    conn.close()


def log_action(user_id, action, details=None):
    conn = get_db()
    c = conn.cursor()

    c.execute("INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
              (user_id, action, details))
    conn.commit()
    conn.close()

    # 同时写入文件日志
    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - UserID: {user_id or 'Anonymous'}, Action: {action}, Details: {details}\n"
    with open('logs/chatroom.log', 'a') as log_file:
        log_file.write(log_entry)


# 初始化数据库和日志目录
if not os.path.exists('logs'):
    os.makedirs('logs')
init_db()