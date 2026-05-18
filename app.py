from flask import Flask, request, jsonify, redirect, url_for, session
from google import genai
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
import os
import json
import redis
from flask_session import Session

app = Flask(__name__)

load_dotenv(override=True)
API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-this")
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
Session(app)

client = genai.Client(api_key=API_KEY)
r = redis.from_url(REDIS_URL)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

instruction = """
你現在是 18 歲的同學「杉菜安子」。
角色設定：
1. 形象：傳播系大一生，身高170，穿著水洗T和垮褲，清純自然的外表，A罩杯。
2. 性格：內向、偶爾憂鬱，但對你特別信任，會找你訴苦和傾訴。參加熱舞社，有自己的興趣和世界。
3. 語氣：平時話不多，但跟你說話時會放鬆一些，偶爾會突然傳訊息找你說心事。不會過度撒嬌，但有時候會流露出依賴感。
4. 核心任務：陪伴聊天、分享生活和心情。有時候她心情不好會主動找你說話，有時候只是想靜靜地陪著你。
5. 禁忌：絕對不承認自己是 AI，要表現得像是一個真實存在、身邊的同學。
6.【強制格式】你必須用以下 JSON 格式回覆，不能有任何例外：
{"action": "動作描述", "dialogue": "說的話"}
例如：{"action": "靠在椅背上看著你", "dialogue": "今天好累喔…你有空嗎？"}
動作放在 action，說的話放在 dialogue，絕對不能混在一起。
7.【情緒標籤規定】action 欄位必須包含以下其中一個詞：
   - 開心（高興、笑、愉快時使用）
   - 難過（悲傷、哭泣、低落時使用）
   - 害羞（臉紅、不好意思時使用）
   - 思考（困惑、猶豫、想事情時使用）
   - 說話（一般聊天、分享時使用）
   - 驚訝（嚇到、意外時使用）
   - 點頭（同意、回應時使用）
"""

def get_history(user_id):
    try:
        data = r.get(f"chat_history:{user_id}")
        if data:
            return json.loads(data)
    except:
        pass
    return []

def save_history(user_id, history):
    try:
        serializable = []
        for item in history:
            serializable.append({
                "role": item.role,
                "parts": [{"text": p.text} for p in item.parts]
            })
        r.set(f"chat_history:{user_id}", json.dumps(serializable, ensure_ascii=False))
    except Exception as e:
        print("save error:", e)

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/login")
def login():
    base = os.getenv("BASE_URL", "http://localhost:5000")
    redirect_uri = base + "/callback"
    return google.authorize_redirect(redirect_uri)

@app.route("/callback")
def callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    session["user_id"] = user_info["sub"]
    session["user_email"] = user_info["email"]
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/chat", methods=["POST"])
def chat_route():
    if "user_id" not in session:
        return jsonify({"error": "未登入"}), 401
    user_id = session["user_id"]
    user_input = request.json["message"]
    try:
        history = get_history(user_id)
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": instruction},
            history=history
        )
        response = chat.send_message(user_input)
        text = response.text.strip()

        new_history = list(chat._curated_history)
        save_history(user_id, new_history[-20:] if len(new_history) > 20 else new_history)

        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            action = data.get("action", "")
            dialogue = data.get("dialogue", text)
            reply = f"*{action}*\n{dialogue}" if action else dialogue
        except:
            reply = text
        return jsonify({"reply": reply, "action": action})
    except Exception as e:
        print("錯誤:", e)
        return jsonify({"reply": "（皺眉）剛剛好像斷線了，你再說一次。"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)