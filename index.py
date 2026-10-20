import os
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "messenger_clone_secret_123"

# MongoDB কানেকশন
MONGO_URI = os.getenv("MONGO_URI")
db_collection = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI)
        db = client.messenger_video_maker
        db_collection = db.chat_data
    except:
        pass

# ডিফল্ট ডামি ডেটা
fallback_data = {
    "pfp1": "https://i.pravatar.cc/150?img=11", 
    "pfp2": "https://i.pravatar.cc/150?img=5",  
    "name": "Mark Zuckerberg",
    "messages": [
        {"sender": "1", "text": "Hello Mark!"},
        {"sender": "2", "text": "Hi! How are you?"}
    ]
}

def get_data():
    if db_collection is not None:
        data = db_collection.find_one({"_id": "main_chat"})
        if data:
            return data
    return fallback_data

def save_data(data):
    global fallback_data
    if db_collection is not None:
        db_collection.update_one({"_id": "main_chat"}, {"$set": data}, upsert=True)
    else:
        fallback_data = data

# ==================== HTML TEMPLATES ==================== #

CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Messenger Clone</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { margin: 0; font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #000; display: flex; justify-content: center; height: 100vh; overflow: hidden; }
        .messenger-container { background: #fff; width: 100%; max-w-md: 400px; height: 100vh; display: flex; flex-direction: column; position: relative; max-width: 450px; }
        
        .header { display: flex; align-items: center; justify-content: space-between; padding: 10px 15px; border-bottom: 1px solid #e0e0e0; box-shadow: 0 1px 2px rgba(0,0,0,0.05); z-index: 10; background: #fff;}
        .header-left { display: flex; align-items: center; gap: 10px; }
        .back-btn { color: #0084ff; font-size: 20px; }
        .profile-img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
        .user-info { display: flex; flex-direction: column; }
        .user-name { font-weight: 600; font-size: 16px; color: #050505; }
        .active-status { font-size: 12px; color: #65676B; }
        .header-icons i { color: #0084ff; font-size: 20px; margin-left: 15px; }

        .chat-area { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; background: #ffffff; }
        .message-row { display: flex; margin-bottom: 15px; width: 100%; }
        .message-row.me { justify-content: flex-end; }
        .message-row.them { justify-content: flex-start; }
        
        .them-pic { width: 28px; height: 28px; border-radius: 50%; margin-right: 8px; align-self: flex-end; }
        .bubble { max-width: 70%; padding: 10px 14px; border-radius: 18px; font-size: 15px; word-wrap: break-word; line-height: 1.4; }
        .me .bubble { background: #0084ff; color: white; border-bottom-right-radius: 4px; }
        .them .bubble { background: #e4e6eb; color: black; border-bottom-left-radius: 4px; }
        
        .input-area { display: flex; align-items: center; padding: 10px; border-top: 1px solid #e0e0e0; background: #fff; }
        .input-icons i { color: #0084ff; font-size: 20px; margin-right: 12px; }
        .input-box { flex: 1; background: #f0f2f5; border-radius: 20px; padding: 8px 15px; font-size: 15px; border: none; outline: none; }
        .input-right-icon { color: #0084ff; font-size: 20px; margin-left: 12px; }

        .overlay-start { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; justify-content: center; align-items: center; z-index: 100; }
        .start-btn { background: #0084ff; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 10px; cursor: pointer; }
        
        .typing { display: none; align-items: center; gap: 3px; padding: 12px 16px; background: #e4e6eb; border-radius: 18px; max-width: 50px; border-bottom-left-radius: 4px;}
        .dot { width: 6px; height: 6px; background: #90949c; border-radius: 50%; animation: bounce 1.3s linear infinite; }
        .dot:nth-child(2) { animation-delay: -1.1s; }
        .dot:nth-child(3) { animation-delay: -0.9s; }
        @keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-4px); } }

        .seen-indicator { width: 14px; height: 14px; border-radius: 50%; object-fit: cover; align-self: flex-end; margin-top: 2px; display: none; }
    </style>
</head>
<body>

<div class="messenger-container" id="messenger">
    <div class="overlay-start" id="overlay">
        <button class="start-btn" onclick="startAutoChat()">Start Video Record & Chat</button>
    </div>

    <div class="header">
        <div class="header-left">
            <i class="fa-solid fa-arrow-left back-btn"></i>
            <img src="" id="header-pfp" class="profile-img" alt="PFP">
            <div class="user-info">
                <span class="user-name" id="chat-name">Name</span>
                <span class="active-status">Active Now</span>
            </div>
        </div>
        <div class="header-icons">
            <i class="fa-solid fa-phone"></i>
            <i class="fa-solid fa-video"></i>
            <i class="fa-solid fa-circle-info"></i>
        </div>
    </div>

    <div class="chat-area" id="chat-area">
        <div class="message-row them" id="typing-row" style="display: none;">
            <img src="" id="typing-pfp" class="them-pic">
            <div class="typing">
                <div class="dot"></div><div class="dot"></div><div class="dot"></div>
            </div>
        </div>
        
        <div style="display:flex; justify-content: flex-end;">
            <img src="" id="seen-pfp" class="seen-indicator">
        </div>
    </div>

    <div class="input-area">
        <div class="input-icons">
            <i class="fa-solid fa-circle-plus"></i>
            <i class="fa-solid fa-camera"></i>
            <i class="fa-solid fa-image"></i>
            <i class="fa-solid fa-microphone"></i>
        </div>
        <input type="text" class="input-box" id="msg-input" placeholder="Message" readonly>
        <i class="fa-solid fa-thumbs-up input-right-icon" id="send-icon"></i>
    </div>
</div>

<script>
    let chatData = {};
    
    fetch('/api/get_data').then(res => res.json()).then(data => {
        chatData = data;
        document.getElementById('header-pfp').src = data.pfp2;
        document.getElementById('typing-pfp').src = data.pfp2;
        document.getElementById('seen-pfp').src = data.pfp2;
        document.getElementById('chat-name').innerText = data.name;
    });

    function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

    async function startScreenRecord() {
        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
            const chunks = [];
            mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'messenger_video.webm'; a.click();
            };
            mediaRecorder.start();
            return mediaRecorder;
        } catch (err) {
            alert("মোবাইলে স্ক্রিন রেকর্ডার চালু করে Start-এ ক্লিক করুন।");
            return null;
        }
    }

    async function typeText(text) {
        const input = document.getElementById('msg-input');
        const icon = document.getElementById('send-icon');
        icon.classList.remove('fa-thumbs-up');
        icon.classList.add('fa-paper-plane');
        
        for (let i = 0; i < text.length; i++) {
            input.value += text[i];
            await sleep(100); 
        }
        await sleep(400);
        input.value = "";
        icon.classList.remove('fa-paper-plane');
        icon.classList.add('fa-thumbs-up');
    }

    function scrollToBottom() {
        const chat = document.getElementById('chat-area');
        chat.scrollTop = chat.scrollHeight;
    }

    function appendMessage(text, sender) {
        const div = document.createElement('div');
        div.className = sender === "1" ? "message-row me" : "message-row them";
        
        let html = '';
        if(sender === "2") {
            html += `<img src="${chatData.pfp2}" class="them-pic">`;
        }
        html += `<div class="bubble">${text}</div>`;
        
        div.innerHTML = html;
        const chat = document.getElementById('chat-area');
        chat.insertBefore(div, document.getElementById('typing-row'));
        scrollToBottom();
    }

    async function startAutoChat() {
        const recorder = await startScreenRecord();
        document.getElementById('overlay').style.display = 'none';
        
        await sleep(1000);

        for (let msg of chatData.messages) {
            if (msg.sender === "1") {
                await typeText(msg.text);
                appendMessage(msg.text, "1");
            } else {
                document.getElementById('typing-row').style.display = 'flex';
                scrollToBottom();
                let typingTime = msg.text.length * 50 + 800; 
                await sleep(typingTime);
                document.getElementById('typing-row').style.display = 'none';
                appendMessage(msg.text, "2");
            }
            document.getElementById('seen-pfp').style.display = 'none'; 
            await sleep(1200);
        }
        
        document.getElementById('seen-pfp').style.display = 'block';
        scrollToBottom();

        await sleep(3000); 
        if (recorder) recorder.stop();
    }
</script>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Auto Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-5">
    <div class="max-w-3xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <div class="flex justify-between items-center border-b pb-3 mb-4">
            <h2 class="text-2xl font-bold text-blue-600">Admin Panel (Chat Setup)</h2>
            <a href="/" target="_blank" class="bg-green-500 text-white px-4 py-2 rounded">View Chat</a>
        </div>
        
        <form id="chatForm">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block font-bold mb-1">My Profile Picture URL</label>
                    <input type="text" id="pfp1" class="w-full border p-2 rounded" required>
                </div>
                <div>
                    <label class="block font-bold mb-1">Target Profile Picture URL</label>
                    <input type="text" id="pfp2" class="w-full border p-2 rounded" required>
                </div>
            </div>
            
            <div class="mb-4">
                <label class="block font-bold mb-1">Chat Header Name</label>
                <input type="text" id="chatName" class="w-full border p-2 rounded" required>
            </div>

            <div class="mb-4">
                <h3 class="font-bold text-lg mb-2 border-b pb-1">Messages</h3>
                <div id="messages-container"></div>
                <button type="button" onclick="addMsgRow()" class="mt-3 bg-blue-100 text-blue-700 px-3 py-1 rounded shadow">+ Add Message</button>
            </div>

            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold text-lg hover:bg-blue-700">Save Setup</button>
        </form>
    </div>

<script>
    let container = document.getElementById('messages-container');

    function addMsgRow(sender="1", text="") {
        const div = document.createElement('div');
        div.className = "flex gap-2 mb-2 items-center";
        div.innerHTML = `
            <select class="border p-2 rounded w-1/4 msg-sender">
                <option value="1" ${sender==="1"?"selected":""}>Me</option>
                <option value="2" ${sender==="2"?"selected":""}>Them</option>
            </select>
            <input type="text" class="border p-2 rounded w-3/4 msg-text" value="${text}" placeholder="Message text..." required>
            <button type="button" onclick="this.parentElement.remove()" class="bg-red-500 text-white px-3 py-2 rounded">X</button>
        `;
        container.appendChild(div);
    }

    fetch('/api/get_data').then(r=>r.json()).then(data => {
        document.getElementById('pfp1').value = data.pfp1 || "";
        document.getElementById('pfp2').value = data.pfp2 || "";
        document.getElementById('chatName').value = data.name || "Unknown";
        
        if(data.messages) {
            data.messages.forEach(m => addMsgRow(m.sender, m.text));
        } else {
            addMsgRow();
        }
    });

    document.getElementById('chatForm').onsubmit = function(e) {
        e.preventDefault();
        
        let msgs = [];
        document.querySelectorAll('#messages-container > div').forEach(row => {
            msgs.push({
                sender: row.querySelector('.msg-sender').value,
                text: row.querySelector('.msg-text').value
            });
        });

        const payload = {
            pfp1: document.getElementById('pfp1').value,
            pfp2: document.getElementById('pfp2').value,
            name: document.getElementById('chatName').value,
            messages: msgs
        };

        fetch('/api/save_data', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(r => r.json()).then(res => {
            alert("Chat setup saved successfully!");
        });
    };
</script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-200 flex items-center justify-center h-screen">
    <div class="bg-white p-8 rounded shadow-lg max-w-sm w-full">
        <h2 class="text-2xl font-bold mb-5 text-center">Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Password" class="w-full border p-2 mb-4 rounded" required>
            <button class="w-full bg-blue-600 text-white py-2 rounded font-bold">Login</button>
        </form>
        <p class="text-center text-gray-500 mt-4 text-sm">Default Password: <strong>admin123</strong></p>
    </div>
</body>
</html>
"""

# ==================== ROUTES ==================== #

@app.route("/")
def index():
    return render_template_string(CHAT_HTML)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == "admin123":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return "Wrong password", 401
            
    if not session.get("logged_in"):
        return render_template_string(LOGIN_HTML)
        
    return render_template_string(ADMIN_HTML)

@app.route("/api/get_data", methods=["GET"])
def api_get():
    data = get_data()
    if "_id" in data:
        del data["_id"]
    return jsonify(data)

@app.route("/api/save_data", methods=["POST"])
def api_save():
    if not session.get("logged_in"):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    save_data(data)
    return jsonify({"success": True})

# Vercel-এর জন্য application 
application = app

if __name__ == "__main__":
    app.run(debug=True)
