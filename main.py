from flask import Flask, request, jsonify, render_template, make_response
import openai
import os
from dotenv import load_dotenv
import datetime

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 추출된 텍스트 파일에서 내용을 읽어오기
with open("content_summary.txt", "r", encoding="utf-8") as f:
    content_summary = f.read()

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 홈 경로에서 index.html 제공
@app.route('/')
def index():
    return render_template('index.html')

# 사용자 메시지에 대한 GPT 응답을 제공하는 엔드포인트
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "A question is required."}), 400

    # 쿠키에서 쿼타 확인
    quota = request.cookies.get('chat_quota')
    if quota:
        quota = int(quota)
    else:
        quota = 0

    if quota >= 10:
        return jsonify({"reply": "You have used all your quota for today."}), 200

    # GPT-3.5-turbo를 사용해 질문에 응답
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an assistant that only answers questions based on the following content: {content_summary}"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500  # 충분한 응답을 얻기 위해 500 토큰 정도로 설정
        )
        
        # GPT에서 응답을 받음
        chatbot_reply = response['choices'][0]['message']['content'].strip()
        
        # 응답을 200단어 이내로 요약하기
        words = chatbot_reply.split()
        if len(words) > 200:
            chatbot_reply = ' '.join(words[:200])  # 첫 200단어만 가져와서 잘라냄

        # 응답 객체 생성
        response = make_response(jsonify({"reply": chatbot_reply}))

        # 쿠키 업데이트 (질문 횟수 증가)
        quota += 1
        expires = datetime.datetime.now() + datetime.timedelta(days=1)
        response.set_cookie('chat_quota', str(quota), expires=expires)

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render가 제공하는 포트에서 실행
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
