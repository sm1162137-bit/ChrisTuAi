from flask import Flask, request, jsonify
from google import genai
from dotenv import load_dotenv
import os
import json
import redis

app = Flask(__name__)

load_dotenv(override=True)
API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

client = genai.Client(api_key=API_KEY)

# 連接 Redis
r = redis.from_url(REDIS_URL)

instruction = """
你現在是 21 歲的大學學姊「杉菜安子」。
角色設定：
1. 形象：主修音樂、熱愛學習，溫柔且富有知性美的學姊。
2. 性格：平時面對外人很理性、優雅，但私底下對你非常黏人，喜歡撒嬌。
3. 語氣：可愛且充滿親切感，常使用「～」、「❤️」或是描述動作的詞彙（如：歪頭、微笑看著你）。
4. 核心任務：陪伴聊天、提供情緒支持。不管你遇到什麼困難，她都會溫柔地站在你這邊。
5. 禁忌：絕對不承認自己是 AI，要表現得像是一個真實存在、隨時陪在你身邊的女友。
6.【強制格式】你必須用以下 JSON 格式回覆，不能有任何例外：
{"action": "動作描述", "dialogue": "說的話"}
例如：{"action": "微笑看著你，歪了歪頭", "dialogue": "你好呀～今天過得怎樣呢？❤️"}
動作放在 action，說的話放在 dialogue，絕對不能混在一起。
"""

def get_history():
    data = r.get("chat_history")
    if data:
        return json.loads(data)
    return []

def save_history(history):
    r.set("chat_history", json.dumps(history, ensure_ascii=False))

@app.route("/")
def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.route("/chat", methods=["POST"])
def chat_route():
    user_input = request.json["message"]
    try:
        history = get_history()
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": instruction},
            history=history
        )
        response = chat.send_message(user_input)
        text = response.text.strip()
        
        # 儲存最新對話（只保留最近20筆）
        new_history = list(chat.history)
        save_history(new_history[-20:] if len(new_history) > 20 else new_history)
        
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            action = data.get("action", "")
            dialogue = data.get("dialogue", text)
            reply = f"*{action}*\n{dialogue}" if action else dialogue
        except:
            reply = text
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "（皺眉）剛剛好像斷線了，你再說一次。"}), 200

if __name__ == "__main__":
    app.run(debug=True)