import google.generativeai as genai

# 填入你的 Key
genai.configure(api_key="你的KEY")

# 使用最基礎的模型嘗試
model = genai.GenerativeModel('gemini-1.5-flash')

try:
    response = model.generate_content("你好")
    print("連線成功！AI說：", response.text)
except Exception as e:
    print("連線還是失敗了，錯誤是：", e)