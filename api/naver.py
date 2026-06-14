from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # SESE 원칙 적용: 응답 변수들을 최상단에서 한 번만 초기화합니다.
        status_code = 200
        response_data = {}
        
        # 1. 쿼리 스트링에서 네이버 code와 state 가져오기
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]
        state = query_components.get("state", [None])[0]

        if not code or not state:
            status_code = 400
            response_data = {"error": "코드 또는 state가 전달되지 않았습니다."}
        else:
            # 2. 네이버에 입장권 던지고 Access Token 받아오기
            token_url = "https://nid.naver.com/oauth2.0/token"
            client_id = os.environ.get("NAVER_CLIENT_ID")
            client_secret = os.environ.get("NAVER_CLIENT_SECRET")
            
            token_params = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state
            }
            
            try:
                token_res = requests.get(token_url, params=token_params)
                token_json = token_res.json()
                
                if "access_token" in token_json:
                    access_token = token_json["access_token"]
                    
                    # 3. 진짜 출입증으로 유저의 '치지직(네이버) 닉네임' 조회하기
                    user_info_url = "https://openapi.naver.com/v1/nid/me"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_res = requests.get(user_info_url, headers=headers)
                    user_json = user_res.json()
                    
                    # 네이버 API는 성공 시 resultcode "00"을 반환합니다.
                    if user_json.get("resultcode") == "00":
                        nickname = user_json.get("response", {}).get("nickname")
                        if nickname:
                            response_data = {
                                "status": "success",
                                "nickname": nickname
                            }
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

        # SESE 원칙 적용: 함수의 맨 마지막에서 단 한 번만 응답을 전송합니다.
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
