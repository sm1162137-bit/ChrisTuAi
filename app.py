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
"""

def get_history():
    try:
        data = r.get("chat_history")
        if data:
            return json.loads(data)
    except:
        pass
    return []

def save_history(history):
    try:
        serializable = []
        for item in history:
            serializable.append({
                "role": item.role,
                "parts": [{"text": p.text} for p in item.parts]
            })
        r.set("chat_history", json.dumps(serializable, ensure_ascii=False))
    except Exception as e:
        print("save error:", e)



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
        new_history = list(chat._curated_history)
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
        print("錯誤:", e)
        return jsonify({"reply": "（皺眉）剛剛好像斷線了，你再說一次。"}), 200

if __name__ == "__main__":
    app.run(debug=True)