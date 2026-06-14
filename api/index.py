from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # SESE 원칙 적용: 응답에 사용할 변수들을 미리 초기화합니다.
        status_code = 200
        response_data = {}
        
        # 1. 쿼리 스트링(주소창)에서 임시 입장권(code) 가져오기
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]

        if not code:
            status_code = 400
            response_data = {"error": "코드가 전달되지 않았습니다."}
        else:
            # 2. 블리자드에 입장권 던지고 Access Token(진짜 출입증) 받아오기
            token_url = "https://oauth.battle.net/token"
            auth_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://snowpalace1.github.io/hs-tier-overlay/",
                "client_id": os.environ.get("BNET_CLIENT_ID"),
                "client_secret": os.environ.get("BNET_CLIENT_SECRET") # 환경 변수에서 마스터키를 꺼내옵니다.
            }
            
            try:
                token_res = requests.post(token_url, data=auth_data)
                token_json = token_res.json()
                
                if "access_token" in token_json:
                    access_token = token_json["access_token"]
                    
                    # 3. 진짜 출입증으로 유저의 '배틀태그' 조회하기
                    user_info_url = "https://oauth.battle.net/userinfo"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_res = requests.get(user_info_url, headers=headers)
                    user_json = user_res.json()
                    
                    if "battletag" in user_json:
                        response_data = {
                            "status": "success", 
                            "battletag": user_json["battletag"]
                        }
                    else:
                        status_code = 400
                        response_data = {"error": "배틀태그를 찾을 수 없습니다.", "details": user_json}
                else:
                    status_code = 400
                    response_data = {"error": "토큰 발급 실패", "details": token_json}
            except Exception as e:
                status_code = 500
                response_data = {"error": f"서버 통신 오류: {str(e)}"}

        # SESE 원칙 적용: 함수의 맨 마지막에서 단 한 번만 응답을 전송합니다. (Single Exit)
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') # 프론트엔드에서 데이터를 읽을 수 있도록 허용
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
