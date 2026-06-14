from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 통신 성공(200) 상태 코드와 함께 JSON 형식으로 응답할 것임을 명시합니다.
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        # 클라이언트에게 보낼 확인용 메시지입니다.
        response_data = {
            "status": "success",
            "message": "백엔드 API 서버가 성공적으로 구축되었습니다!"
        }
        
        # 한글 깨짐을 방지하며 데이터를 전송하고 함수를 종료합니다.
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
