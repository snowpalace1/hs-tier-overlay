from http.server import BaseHTTPRequestHandler
import json
import requests
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status_code = 200
        response_data = {}
        
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]
        state = query_components.get("state", [None])[0]

        if not code or not state:
            status_code = 400
            response_data = {"error": "코드 또는 state가 전달되지 않았습니다."}
        else:
            token_url = "https://nid.naver.com/oauth2.0/token"
            
            # 🔥 Vercel 환경 변수를 무시하고 여기에 직접 키를 적어넣습니다! 🔥
            # 본인의 진짜 Client ID와 Secret을 따옴표 안에 정확히 넣어주세요.
            client_id = "kLCeM46CJDEtQ3gqVGfV"
            client_secret = "SdTTjdGB3G"
            
            token_params = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state
            }
            
            try:
                # 헤더 없이 가장 순수한 형태로 통신 시도
                token_res = requests.get(token_url, params=token_params)
                token_json = token_res.json()
                
                if "access_token" in token_json:
                    access_token = token_json["access_token"]
                    
                    user_info_url = "https://openapi.naver.com/v1/nid/me"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_res = requests.get(user_info_url, headers=headers)
                    user_json = user_res.json()
                    
                    if user_json.get("resultcode") == "00":
                        nickname = user_json.get("response", {}).get("nickname")
                        if nickname:
                            response_data = {"status": "success", "nickname": nickname}
                        else:
                            status_code = 400
                            response_data = {"error": "닉네임을 찾을 수 없습니다."}
                    else:
                        status_code = 400
                        response_data = {"error": "네이버 유저 정보 조회 실패", "details": user_json}
                else:
                    status_code = 400
                    response_data = {"error": "토큰 발급 실패", "details": token_json}
            except Exception as e:
                status_code = 500
                response_data = {"error": f"서버 통신 오류: {str(e)}"}

        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
