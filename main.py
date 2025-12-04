<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Hunter Pro CRM</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-dark: #1A1F36;
            --cyan: #00D9FF;
            --green: #00B894;
            --red: #FF7675;
            --white: #FFFFFF;
            --gray-light: #B2BAC2;
        }
        * {
            box-sizing: border-box;
        }
        html, body {
            margin: 0;
            padding: 0;
            font-family: 'Cairo', sans-serif;
            background: var(--primary-dark);
            color: var(--white);
            min-height: 100vh;
            width: 100%;
            overflow-x: hidden;
        }
        body {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            width: 100%;
            margin: 20px 0;
        }
        .btn {
            background: var(--cyan);
            color: var(--primary-dark);
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            margin: 8px 0;
            width: 100%;
            font-size: 16px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #00a3cc;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: none;
            margin: 8px 0;
            font-size: 16px;
            font-family: inherit;
        }
        #admin-chat-container, #campaigns-section, #extractor-container {
            width: 100%;
            max-width: 800px;
            margin-top: 20px;
        }
        #admin-chat-messages, .chat-messages {
            height: 50vh;
            max-height: 500px;
            overflow-y: auto;
            background: #343541;
            padding: 16px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .chat-message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 15px;
            line-height: 1.5;
            word-break: break-word;
        }
        .chat-message.user {
            background: #00B894;
            color: #fff;
            align-self: flex-end;
        }
        .chat-message.bot {
            background: #444654;
            color: #fff;
            align-self: flex-start;
        }
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            background: #444654;
            border-radius: 8px;
            width: fit-content;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #fff;
            border-radius: 50%;
            animation: blink 1.2s infinite;
        }
        @keyframes blink {
            0%, 60%, 100% { opacity: 0.2; }
            30% { opacity: 1; }
        }
        .chat-input-form {
            display: flex;
            gap: 8px;
            padding: 12px;
            background: #202123;
            border-radius: 0 0 8px 8px;
        }
        .chat-input-form textarea {
            flex: 1;
            background: #40414f;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 12px;
            resize: none;
            font-family: inherit;
            font-size: 16px;
            max-height: 120px;
        }
        .chat-input-form .send-btn {
            background: #00B894;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 0 20px;
            font-size: 20px;
            cursor: pointer;
        }
        textarea {
            width: 100%;
            border-radius: 8px;
            padding: 10px;
            border: none;
            resize: vertical;
        }
        .campaign-card {
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            text-align: right;
        }

        /* ====== Responsive: جميع الأجهزة ====== */
        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 10px;
            }
            .card {
                padding: 15px;
                margin: 10px 0;
            }
            .btn {
                font-size: 18px;
                padding: 14px;
            }
            input, textarea {
                font-size: 18px;
                padding: 14px;
            }
            #admin-chat-messages, .chat-messages {
                height: 40vh;
                padding: 12px;
            }
            .chat-message {
                font-size: 16px;
            }
        }

        @media (min-width: 601px) and (max-width: 1024px) {
            .container {
                padding: 15px;
            }
            .card {
                padding: 18px;
            }
            .btn {
                font-size: 17px;
                padding: 13px;
            }
            input, textarea {
                font-size: 17px;
                padding: 13px;
            }
        }

        @media (min-width: 1025px) {
            .container {
                padding: 20px;
            }
            .card {
                padding: 20px;
            }
            .btn {
                font-size: 16px;
                padding: 12px;
            }
            input, textarea {
                font-size: 16px;
                padding: 12px;
            }
        }
    </style>
</head>
<body>

    <!-- شاشة 1: تسجيل الدخول -->
    <div id="login-form" class="card">
        <h2>🔐 تسجيل الدخول</h2>
        <!-- زرار Google OAuth -->
        <button class="btn" onclick="loginWithGoogle()">دخول بـ Google</button>
        <hr style="margin: 15px 0; border: none; border-top: 1px solid rgba(255,255,255,0.2);">
        <input id="email" placeholder="البريد الإلكتروني" value="admin@example.com"><br>
        <input id="password" type="password" placeholder="كلمة السر" value="admin123"><br>
        <button class="btn" onclick="login()">دخول يدوي</button>
    </div>

    <!-- شاشة 2: لوحة التحكم -->
    <div id="dashboard" class="container" style="display:none;">
        <h2>🎯 لوحة تحكم Hunter Pro</h2>

        <!-- أزرار الأدمن فقط -->
        <div id="admin-only" style="display:none;">
            <button class="btn" onclick="toggleChat()">💬 شات الأدمن</button>
            <button class="btn" onclick="toggleExtractor()">📱 استخراج أرقام</button>
        </div>

        <!-- أزرار اليوزر العادي -->
        <div id="user-only" style="display:none;">
            <button class="btn" onclick="showCampaigns()">📤 حملاتى</button>
        </div>

        <!-- شات الأدمن (نفس GPT) -->
        <div id="admin-chat-container" class="card">
            <div class="chat-header">
                <span>💬 شات الأدمن الذكي</span>
                <button onclick="toggleChat()" style="background:none;border:none;color:#fff;float:left;font-size:20px;">✖</button>
            </div>
            <div id="admin-chat-messages" class="chat-messages"></div>
            <div id="typing-indicator" class="typing-indicator"><span></span><span></span><span></span></div>
            <form id="chat-form" class="chat-input-form" onsubmit="sendMessage(event)">
                <textarea id="chat-input" placeholder="اكتب رسالتك هنا..." rows="1" autofocus></textarea>
                <button type="submit" class="send-btn">➤</button>
            </form>
        </div>

        <!-- استخراج الأرقام -->
        <div id="extractor-container" class="card" style="display:none;">
            <h3>📤 استخراج أرقام من نص</h3>
            <textarea id="extract-text" rows="4" placeholder="انسخ النص اللي فيه أرقام هنا..."></textarea><br>
            <button class="btn" onclick="extractPhones()">استخراج</button>
            <div id="extract-result" style="margin-top:10px;"></div>
        </div>

        <!-- حملات اليوزر -->
        <div id="campaigns-section" class="card" style="display:none;">
            <h3>📤 حملاتى</h3>
            <button class="btn" onclick="showCreateCampaign()">➕ إنشاء حملة جديدة</button>
            <div id="create-campaign-form" style="display:none;margin-top:15px;text-align:right;">
                <input id="campaign-name" placeholder="اسم الحملة" style="width:100%;margin-bottom:10px;"><br>
                <textarea id="campaign-message" rows="3" placeholder="نص الرسالة" style="width:100%;margin-bottom:10px;"></textarea><br>
                <input type="file" id="campaign-media" accept="image/*,video/*" style="margin-bottom:10px;"><br>
                <button class="btn" onclick="createCampaign()">إنشاء الحملة</button>
            </div>
            <div id="campaigns-list" style="margin-top:20px;"></div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        let token = "";
        let ws = null;
        const chatHistory = JSON.parse(localStorage.getItem("adminChat") || "[]");

        // ====== دخول بـ Google ======
        async function loginWithGoogle() {
            // محاكاة دخول بـ Google – في الحقيقة تستخدم Google OAuth
            const email = prompt("أدخل بريدك الإلكتروني (محاكاة):");
            if (!email) return;
            const res = await fetch("/api/login", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ email: email, password: "google" })
            });
            const data = await res.json();
            if (data.access_token) {
                token = data.access_token;
                const payload = JSON.parse(atob(token.split('.')[1]));
                document.getElementById("login-form").style.display = "none";
                document.getElementById("dashboard").style.display = "block";

                if (payload.sub === "admin@example.com") {
                    document.getElementById("admin-only").style.display = "block";
                } else {
                    document.getElementById("user-only").style.display = "block";
                }
                connectWebSocket();
                renderHistory();
            } else {
                alert("❌ بيانات خاطئة");
            }
        }

        // ====== دخول يدوي ======
        async function login() {
            const res = await fetch("/api/login", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value
                })
            });
            const data = await res.json();
            if (data.access_token) {
                token = data.access_token;
                const payload = JSON.parse(atob(token.split('.')[1]));
                document.getElementById("login-form").style.display = "none";
                document.getElementById("dashboard").style.display = "block";

                if (payload.sub === "admin@example.com") {
                    document.getElementById("admin-only").style.display = "block";
                } else {
                    document.getElementById("user-only").style.display = "block";
                }
                connectWebSocket();
                renderHistory();
            } else {
                alert("❌ بيانات خاطئة");
            }
        }

        // ====== توصيل WebSocket ======
        function connectWebSocket() {
            ws = new WebSocket(`wss://${location.host}/ws/admin-chat`);
            ws.onmessage = e => {
                document.getElementById('typing-indicator').style.display = 'none';
                addMessageToUI('bot', e.data);
                chatHistory.push({role: 'bot', text: e.data});
                localStorage.setItem('adminChat', JSON.stringify(chatHistory));
            };
        }

        // ====== عرض سجل المحادثة ======
        function renderHistory() {
            const box = document.getElementById('admin-chat-messages');
            box.innerHTML = "";
            chatHistory.forEach(msg => addMessageToUI(msg.role, msg.text));
        }

        // ====== إضافة رسالة للواجهة ======
        function addMessageToUI(role, text) {
            const box = document.getElementById('admin-chat-messages');
            const div = document.createElement('div');
            div.className = `chat-message ${role}`;
            div.innerHTML = marked.parse(text);
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        // ====== إرسال رسالة ======
        async function sendMessage(e) {
            e.preventDefault();
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text || !ws) return;

            if (text.startsWith('/')) {
                document.getElementById('typing-indicator').style.display = 'flex';
                const res = await fetch('/api/admin-command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({ command: text })
                });
                const data = await res.json();
                document.getElementById('typing-indicator').style.display = 'none';
                addMessageToUI('bot', data.reply);
                chatHistory.push({role: 'bot', text: data.reply});
                localStorage.setItem('adminChat', JSON.stringify(chatHistory));
            } else {
                document.getElementById('typing-indicator').style.display = 'flex';
                addMessageToUI('user', text);
                chatHistory.push({role: 'user', text});
                localStorage.setItem('adminChat', JSON.stringify(chatHistory));
                ws.send(text);
            }
            input.value = '';
            input.style.height = 'auto';
        }

        // ====== تبديل الشات ======
        function toggleChat() {
            const box = document.getElementById('admin-chat-container');
            box.style.display = box.style.display === 'none' ? 'block' : 'none';
        }

        // ====== تبديل استخراج الأرقام ======
        function toggleExtractor() {
            const box = document.getElementById('extractor-container');
            box.style.display = box.style.display === 'none' ? 'block' : 'none';
        }

        // ====== عرض الحملات ======
        function showCampaigns() {
            document.getElementById('campaigns-section').style.display = 'block';
            loadUserCampaigns();
        }

        // ====== عرض نموذج إنشاء الحملة ======
        function showCreateCampaign() {
            document.getElementById('create-campaign-form').style.display = 'block';
        }

        // ====== إنشاء الحملة ======
        async function createCampaign() {
            const name = document.getElementById('campaign-name').value.trim();
            const message = document.getElementById('campaign-message').value.trim();
            const fileInput = document.getElementById('campaign-media');
            const file = fileInput.files[0];
            if (!name || !message) return alert("أكمل البيانات");

            const formData = new FormData();
            formData.append("name", name);
            formData.append("message", message);
            formData.append("user_id", "user");
            if (file) formData.append("media", file);

            const res = await fetch('/api/create-campaign', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            const data = await res.json();
            alert(data.reply);
            loadUserCampaigns();
            document.getElementById('create-campaign-form').style.display = 'none';
            fileInput.value = "";
        }

        // ====== تحميل حملات اليوزر ======
        async function loadUserCampaigns() {
            const res = await fetch('/api/my-campaigns', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            const listBox = document.getElementById('campaigns-list');
            listBox.innerHTML = "";
            if (data.campaigns.length === 0) {
                listBox.innerHTML = "<p>لا توجد حملات حتى الآن</p>";
                return;
            }
            data.campaigns.forEach(c => {
                const div = document.createElement('div');
                div.className = "campaign-card";
                div.innerHTML = `
                    <strong>${c.name}</strong><br>
                    <small>${c.message.substring(0, 50)}...</small><br>
                    <small>الحالة: ${c.status} | تم الإرسال: ${c.sent_count} | تم التسليم: ${c.delivered_count}</small><br>
                    <button class="btn" onclick="sendCampaign('${c.id}')">إرسال الآن</button>
                    <button class="btn" onclick="deleteCampaign('${c.id}')">🗑️ حذف</button>
                `;
                listBox.appendChild(div);
            });
        }

        // ====== إرسال الحملة ======
        async function sendCampaign(campaignId) {
            if (!confirm("سيتم إرسال الحملة فعليًا – متأكد؟")) return;
            const res = await fetch('/api/send-campaign', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ campaign_id: campaignId })
            });
            const data = await res.json();
            alert(data.reply);
            loadUserCampaigns();
        }

        // ====== حذف الحملة ======
        async function deleteCampaign(campaignId) {
            if (!confirm("سيتم حذف الحملة نهائيًا – متأكد؟")) return;
            const res = await fetch('/api/delete-campaign', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ campaign_id: campaignId })
            });
            const data = await res.json();
            alert(data.reply);
            loadUserCampaigns();
        }

        // ====== استخراج الأرقام ======
        async function extractPhones() {
            const text = document.getElementById('extract-text').value;
            const res = await fetch('/api/extract-phones', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ text })
            });
            const data = await res.json();
