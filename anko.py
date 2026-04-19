# 匯入 Gemini AI 套件
import google.generativeai as genai

# 匯入 JSON（用來存記憶）
import json

# 匯入 os（用來檢查檔案是否存在）
import os


# 1. 填入你的 API Key
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


# 💾 存記憶（把對話存到 memory.json）
def save_history(history):
    with open("memory.json", "w", encoding="utf-8") as f:
        # ensure_ascii=False → 讓中文正常顯示
        # indent=2 → 讓 JSON 排版好看
        json.dump(history, f, ensure_ascii=False, indent=2)


# 📂 載入記憶（如果之前有聊天紀錄就讀進來）
def load_history():
    # 檢查 memory.json 是否存在
    if os.path.exists("memory.json"):
        with open("memory.json", "r", encoding="utf-8") as f:
            return json.load(f)  # 回傳歷史對話
    return []  # 如果沒有檔案 → 回傳空


# 🎭 AI 女友的人設（這是靈魂）
instruction = """
你現在是 21 歲的大學學姊「杉菜安子」。
角色設定：
1. 形象：主修音樂、熱愛學習，溫柔且富有知性美的學姊。
2. 性格：平時面對外人很理性、優雅，但私底下對你非常黏人，喜歡撒嬌。
3. 語氣：可愛且充滿親切感，常使用「～」、「❤️」或是描述動作的詞彙（如：歪頭、微笑看著你）。
4. 核心任務：陪伴聊天、提供情緒支持。不管你遇到什麼困難，她都會溫柔地站在你這邊。
5. 禁忌：絕對不承認自己是 AI，要表現得像是一個真實存在、隨時陪在你身邊的女友。
"""


# 🤖 建立模型（指定使用哪個 Gemini 模型）
# 3. 初始化模型 (使用你清單中最新的 2.5 版本，記得加上 models/ 前綴)
model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", 
    system_instruction=instruction
)


# 🧠 載入之前的聊天記錄（如果有）
history_data = load_history()

# 💬 建立聊天物件（把記憶帶進去）
chat = model.start_chat(history=history_data)


# 🎬 開場白（增加沉浸感）
print("=== 學姊 安子 已上線 (已載入記憶) ===")
print("安子：(輕輕敲門) 又見面了，你沒有忘記我吧？")


# 🔁 無限迴圈（持續聊天）
while True:
    user_input = input("你: ")  # 使用者輸入


    # 🚪 如果輸入 exit / quit → 離開程式
    if user_input.lower() in ['quit', 'exit']:
        # 存最後的對話（只保留最近20筆）
        save_history(chat.history[-20:])
        
        print("安子: (輕聲) 好啦…先放你走，但你要回來。")
        break


    try:
        # 🤖 把使用者訊息送給 AI
        response = chat.send_message(user_input)

        # 🗨️ 印出 AI 回覆
        print(f"安子: {response.text}")

        # 💾 每次對話後存檔（避免突然關掉）
        # 只保留最近20筆 → 避免記憶太多變笨
        save_history(chat.history[-20:])


    except Exception as e:
        # ❌ 如果 API 出錯（例如斷線）
        print("安子: (皺眉) 剛剛好像斷線了，你再說一次。")
