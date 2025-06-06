// script.js
document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    let currentRoom = 'general';

    // DOM 元素
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages');
    const roomLinks = document.querySelectorAll('.room-link');
    const roomList = document.getElementById('room-list');
    const createRoomBtn = document.getElementById('create-room-btn');
    const newRoomInput = document.getElementById('new-room-name');
    const currentRoomHeader = document.getElementById('current-room');
    const userList = document.getElementById('current-users');
    const userCount = document.getElementById('user-count');

    // 加入默认房间
    joinRoom(currentRoom);

    // 发送消息
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            socket.emit('send_message', {
                room: currentRoom,
                message: message
            });
            messageInput.value = '';
            messageInput.focus();
        }
    }

    // 加入房间
    function joinRoom(room) {
        if (currentRoom) {
            socket.emit('leave', { room: currentRoom });
        }

        currentRoom = room;
        currentRoomHeader.textContent = `#${room}`;
        messagesContainer.innerHTML = '';

        // 更新活动房间样式
        roomLinks.forEach(link => {
            if (link.dataset.room === room) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        socket.emit('join', { room: room });
    }

    // 创建新房间
    function createRoom() {
        const roomName = newRoomInput.value.trim();
        if (roomName) {
            socket.emit('create_room', { room_name: roomName });
            newRoomInput.value = '';
        }
    }

    // 处理接收到的消息
    socket.on('new_message', function(data) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');

        if (data.username === '{{ username }}') {
            messageElement.classList.add('sent');
        } else {
            messageElement.classList.add('received');
        }

        messageElement.innerHTML = `
            <div class="username">${data.username}</div>
            <div class="content">${data.message}</div>
            <div class="timestamp">${data.timestamp}</div>
        `;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });

    // 处理系统消息
    socket.on('system_message', function(data) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('system-message');
        messageElement.innerHTML = `<p>${data.message}</p>`;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    });

    // 更新房间用户列表
    socket.on('update_room_users', function(data) {
        if (data.room === currentRoom) {
            userList.innerHTML = '';
            data.users.forEach(user => {
                const userItem = document.createElement('li');
                userItem.textContent = user;
                userList.appendChild(userItem);
            });
            userCount.textContent = data.users.length;
        }
    });

    // 新房间创建
    socket.on('new_room', function(data) {
        const newRoomItem = document.createElement('li');
        newRoomItem.innerHTML = `<a href="#" class="room-link" data-room="${data.room_name}">#${data.room_name}</a>`;
        roomList.appendChild(newRoomItem);

        // 为新房间链接添加事件监听
        newRoomItem.querySelector('.room-link').addEventListener('click', function(e) {
            e.preventDefault();
            joinRoom(data.room_name);
        });
    });

    // 事件监听器
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    roomLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            joinRoom(this.dataset.room);
        });
    });

    createRoomBtn.addEventListener('click', createRoom);
    newRoomInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            createRoom();
        }
    });

    // 添加注册表单处理（如果存在）
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;

            if (password !== confirmPassword) {
                e.preventDefault();
                alert('两次输入的密码不一致');
            }
        });
    }

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // 移动端菜单
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }

    // 模拟聊天消息
    if (document.querySelector('.chat-preview')) {
        const messages = [
            { type: 'received', username: 'Sarah Miller', text: '有人用过这个应用吗？体验如何？', delay: 5000 },
            { type: 'sent', text: '我用了几天，界面很漂亮，功能也很稳定', delay: 7000 }
        ];

        messages.forEach(msg => {
            setTimeout(() => {
                addMessageToPreview(msg);
            }, msg.delay);
        });
    }

    function addMessageToPreview(message) {
        const messagesContainer = document.querySelector('.chat-messages');

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', message.type);

        if (message.type === 'received') {
            const avatar = document.createElement('div');
            avatar.classList.add('avatar');
            avatar.textContent = message.username.substring(0, 2);
            messageDiv.appendChild(avatar);
        }

        const content = document.createElement('div');
        content.classList.add('content');

        if (message.username) {
            const username = document.createElement('div');
            username.classList.add('username');
            username.textContent = message.username;
            content.appendChild(username);
        }

        const text = document.createElement('div');
        text.classList.add('text');
        text.textContent = message.text;
        content.appendChild(text);

        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        content.appendChild(timestamp);

        messageDiv.appendChild(content);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

});