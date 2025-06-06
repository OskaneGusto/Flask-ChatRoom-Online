# # create_migration.py (更新后)
# import sqlite3
# import datetime
#
# DATABASE = 'chatroom.db'
#
#
# def migrate_database():
#     conn = sqlite3.connect(DATABASE)
#     c = conn.cursor()
#
#     # 获取现有列
#     c.execute("PRAGMA table_info(users)")
#     existing_columns = [row[1] for row in c.fetchall()]
#
#     # 添加缺失的列（分步处理）
#     columns_to_add = [
#         ('email', 'TEXT'),
#         ('avatar', 'TEXT'),
#         ('bio', 'TEXT'),
#         ('location', 'TEXT'),
#         ('website', 'TEXT'),
#         ('last_seen', 'TIMESTAMP')
#     ]
#
#     # 添加缺失的列（不带默认值）
#     for column, col_type in columns_to_add:
#         if column not in existing_columns:
#             print(f"Adding column: {column}")
#             c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
#
#     # 设置默认值（分步处理）
#     # 1. 设置 avatar 默认值
#     c.execute("UPDATE users SET avatar = 'default_avatar.png' WHERE avatar IS NULL")
#
#     # 2. 设置 last_seen 默认值（使用当前时间）
#     current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     c.execute("UPDATE users SET last_seen = ? WHERE last_seen IS NULL", (current_time,))
#
#     # 3. 设置其他列的默认值为空字符串
#     for column, _ in columns_to_add:
#         if column not in ['avatar', 'last_seen']:
#             c.execute(f"UPDATE users SET {column} = '' WHERE {column} IS NULL")
#
#     conn.commit()
#     conn.close()
#     print("Database migration completed successfully!")
#
#
# if __name__ == '__main__':
#     migrate_database()

# create_migration.py (更新后)
import sqlite3
import datetime

DATABASE = 'chatroom.db'


def migrate_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # 创建 rooms_users 表（如果不存在）
    c.execute('''CREATE TABLE IF NOT EXISTS rooms_users (
        user_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, room_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id)
    )''')

    # 获取现有列
    c.execute("PRAGMA table_info(users)")
    existing_columns = [row[1] for row in c.fetchall()]

    # 添加缺失的列（分步处理）
    columns_to_add = [
        ('email', 'TEXT'),
        ('avatar', 'TEXT'),
        ('bio', 'TEXT'),
        ('location', 'TEXT'),
        ('website', 'TEXT'),
        ('last_seen', 'TIMESTAMP')
    ]

    # 添加缺失的列（不带默认值）
    for column, col_type in columns_to_add:
        if column not in existing_columns:
            print(f"Adding column: {column}")
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {column} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding column {column}: {e}")

    # 设置默认值（分步处理）
    # 1. 设置 avatar 默认值
    c.execute("UPDATE users SET avatar = 'default_avatar.png' WHERE avatar IS NULL")

    # 2. 设置 last_seen 默认值（使用当前时间）
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("UPDATE users SET last_seen = ? WHERE last_seen IS NULL", (current_time,))

    # 3. 设置其他列的默认值为空字符串
    for column, _ in columns_to_add:
        if column not in ['avatar', 'last_seen']:
            c.execute(f"UPDATE users SET {column} = '' WHERE {column} IS NULL")

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")


if __name__ == '__main__':
    migrate_database()