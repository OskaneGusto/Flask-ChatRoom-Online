# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import os
import secrets
from database import create_user, verify_user, save_message, log_action, get_db,init_db
import time
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# 配置头像上传
AVATAR_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['AVATAR_FOLDER'] = AVATAR_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 初始化房间
rooms = {
    "general": {"users": []},
    "tech": {"users": []},
    "gaming": {"users": []},
    "random": {"users": []}
}


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('home'))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    """自定义日期时间格式化过滤器"""
    if isinstance(value, datetime):
        return value.strftime(format)
    try:
        # 尝试将字符串转换为 datetime 对象
        dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return dt.strftime(format)
    except (ValueError, TypeError):
        return value  # 如果转换失败，返回原始值

@app.route('/home')
def home():
    """现代化首页"""
    return render_template('home.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'], rooms=rooms)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 设置默认值
        avatar = 'default_avatar.png'
        #last_seen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   ##datetime.datetime.now()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_seen = created_at

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 20:
            flash('用户名长度必须在3-20个字符之间', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')

        # conn = get_db()
        # c = conn.cursor()
        # try:
        #     # 插入新用户（包含默认值）
        #     c.execute("INSERT INTO users (username, password, avatar, last_seen) VALUES (?, ?, ?, ?)",
        #               (username, bcrypt.generate_password_hash(password), avatar, last_seen))
        #     conn.commit()
        #
        #     flash('注册成功！请登录。', 'success')
        #     return redirect(url_for('login'))
        # except sqlite3.IntegrityError:
        #     flash('用户名已存在！', 'danger')

        # 创建用户
        user_id = create_user(username, password,avatar, created_at,last_seen)
        if user_id:
            log_action(user_id, 'REGISTER', f'Username: {username}')
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        else:
            flash('用户名已存在', 'danger')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_id = verify_user(username, password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            log_action(user_id, 'LOGIN')
            return redirect(url_for('index'))
        else:
            log_action(None, 'LOGIN_FAILED', f'Username: {username}')
            flash('用户名或密码错误', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_action(session['user_id'], 'LOGOUT')
        session.pop('user_id', None)
        session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', username=session.get('username'))

@app.route('/terms')
def terms():
    return render_template('terms.html', username=session.get('username'))

@app.route('/contact')
def contact():
    return render_template('contact.html', username=session.get('username'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    try:
        # 获取当前用户信息
        c.execute("SELECT id, username, email, avatar, bio, location, website, created_at FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        if not user:
            flash('用户不存在', 'danger')
            return redirect(url_for('index'))  # 或者返回一个错误页面

        # 将 created_at 字符串转换为 datetime 对象
        created_at = datetime.strptime(user[7], '%Y-%m-%d %H:%M:%S') if user[7] else datetime.now()

        # 处理空值
        user = {
            'id': user[0],
            'username': user[1],
            'email': user[2] or '',
            'avatar': user[3] or 'default_avatar.png',
            'bio': user[4] or '',
            'location': user[5] or '',
            'website': user[6] or '',
            'created_at': created_at
        }

        # 获取用户统计信息
        c.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (session['user_id'],))
        messages_sent = c.fetchone()[0]


        # # 获取用户加入的房间数量（假设有一个相应的查询）
        # c.execute("SELECT COUNT(*) FROM rooms_users WHERE user_id = ?", (session['user_id'],))
        # rooms_joined = c.fetchone()[0]

        # 获取用户加入的房间数量（使用 rooms_users 表）
        c.execute("SELECT COUNT(*) FROM rooms_users WHERE user_id = ?", (session['user_id'],))
        rooms_joined_result = c.fetchone()
        rooms_joined = rooms_joined_result[0] if rooms_joined_result else 0

        # 获取最后活跃时间
        c.execute("SELECT last_seen FROM users WHERE id = ?", (session['user_id'],))
        last_seen_result = c.fetchone()
        #last_seen = last_seen_result[0] if last_seen_result else datetime.now().strftime('%Y-%m-%d %H:%M')
        last_seen = datetime.strptime(last_seen_result[0], '%Y-%m-%d %H:%M:%S') if last_seen_result and last_seen_result[0] else datetime.now()

        stats = {
            'rooms_joined': rooms_joined,
            'messages_sent': messages_sent,
            'last_active': last_seen  # 使用 UTC 时间
        }

    finally:
        conn.close()  # 确保数据库连接总是被关闭

    return render_template('profile.html', user=user, stats=stats, is_own_profile=True)


# @app.route('/profile')
# def profile():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#
#     conn = get_db()
#     c = conn.cursor()
#
#     # 获取当前用户信息
#     c.execute("SELECT id, username, email, avatar, bio, location,website, created_at FROM users WHERE id = ?",(session['user_id'],))   ###
#     user = c.fetchone()
#
#     # 获取用户统计信息
#     c.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (session['user_id'],))
#     messages_sent = c.fetchone()[0]
#
#     # 这里简化处理，实际应用中可能需要更复杂的统计
#     stats = {
#         'rooms_joined': len(rooms),  # 假设用户加入了所有房间
#         'messages_sent': messages_sent,
#         'last_active': datetime.now().strftime('%Y-%m-%d %H:%M')
#     }
#
#     return render_template('profile.html', user=user, stats=stats, is_own_profile=True)


@app.route('/room/<int:room_id>')
def room(room_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    # 检查用户是否已加入该房间
    c.execute("SELECT 1 FROM rooms_users WHERE user_id = ? AND room_id = ?",
              (session['user_id'], room_id))
    if not c.fetchone():
        # 如果未加入，则添加记录
        c.execute("INSERT INTO rooms_users (user_id, room_id) VALUES (?, ?)",
                  (session['user_id'], room_id))
        conn.commit()

    # 获取房间信息
    c.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = c.fetchone()

    if not room:
        flash('房间不存在', 'danger')
        return redirect(url_for('index'))

    # 获取房间消息
    c.execute("""
        SELECT m.id, m.message, m.timestamp, u.username 
        FROM messages m 
        JOIN users u ON m.user_id = u.id 
        WHERE m.room_id = ? 
        ORDER BY m.timestamp ASC
    """, (room_id,))
    messages = c.fetchall()

    return render_template('room.html', room=room, messages=messages)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401

    data = request.get_json()
    bio = data.get('bio', '')
    email = data.get('email', '')
    location = data.get('location', '')
    website = data.get('website', '')

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET bio = ?, email = ?, location = ?, website = ? WHERE id = ?",
              (bio, email, location, website, session['user_id']))
    conn.commit()

    return jsonify({'success': True})


@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'}), 401

    if 'avatar' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    if file and allowed_file(file.filename):
        if not os.path.exists(app.config['AVATAR_FOLDER']):
            os.makedirs(app.config['AVATAR_FOLDER'])

        filename = f"{session['user_id']}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}"
        file.save(os.path.join(app.config['AVATAR_FOLDER'], filename))

        # 更新数据库
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET avatar = ? WHERE id = ?", (filename, session['user_id']))
        conn.commit()

        return jsonify({'success': True, 'filename': filename})

    return jsonify({'success': False, 'message': '文件类型不允许'}), 400


@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        log_action(session['user_id'], 'CONNECT')
        print(f"用户 {session['username']} 已连接")


@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        log_action(session['user_id'], 'DISCONNECT')
        print(f"用户 {session['username']} 已断开连接")


@socketio.on('join')
def handle_join(data):
    if 'user_id' not in session:
        return

    room = data['room']
    username = session['username']
    user_id = session['user_id']

    if room not in rooms:
        rooms[room] = {"users": []}

    if user_id not in rooms[room]["users"]:
        rooms[room]["users"].append(user_id)

    join_room(room)
    emit('system_message', {
        'message': f'{username} 加入了聊天室',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }, room=room)

    log_action(user_id, 'JOIN_ROOM', f'Room: {room}')

    emit('update_room_users', {
        'room': room,
        'users': [session['username']]  # 简化处理
    }, room=room)


@socketio.on('leave')
def handle_leave(data):
    if 'user_id' not in session:
        return

    room = data['room']
    username = session['username']
    user_id = session['user_id']

    if room in rooms and user_id in rooms[room]["users"]:
        rooms[room]["users"].remove(user_id)

    leave_room(room)
    emit('system_message', {
        'message': f'{username} 离开了聊天室',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }, room=room)

    log_action(user_id, 'LEAVE_ROOM', f'Room: {room}')

    emit('update_room_users', {
        'room': room,
        'users': [session['username']]  # 简化处理
    }, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    if 'user_id' not in session:
        return

    room = data['room']
    message = data['message']
    username = session['username']
    user_id = session['user_id']

    if message.strip():
        # 保存消息到数据库
        save_message(user_id, room, message)

        # 记录消息日志
        log_action(user_id, 'SEND_MESSAGE', f'Room: {room}, Length: {len(message)}')

        emit('new_message', {
            'username': username,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }, room=room)


@socketio.on('create_room')
def handle_create_room(data):
    if 'user_id' not in session:
        return

    room_name = data['room_name']
    if room_name and room_name not in rooms:
        rooms[room_name] = {"users": []}
        log_action(session['user_id'], 'CREATE_ROOM', f'Room: {room_name}')
        emit('new_room', {'room_name': room_name}, broadcast=True)


@socketio.on('administrator')
def admin():
    """管理员功能"""



def main():
    # 启动服务器
    ip = input("请输入服务器IP地址(localhost/0.0.0.0)：暂时无用，直接回车\n\n")
    socketio.run(app, debug=True, host='0.0.0.0', port=5111, log_output=True, allow_unsafe_werkzeug=True)
    # app.run( debug=True, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()