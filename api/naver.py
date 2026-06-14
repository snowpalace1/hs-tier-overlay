from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # SESE 원칙 적용: 응답 변수 초기화
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
            # 오류 방지 1: Vercel 환경 변수에서 키를 가져올 때 앞뒤의 보이지 않는 공백 제거
            client_id = os.environ.get("NAVER_CLIENT_ID", "").strip()
            client_secret = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
            
            token_params = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state,
                # 오류 방지 2: 토큰 교환 시에도 웹페이지 주소를 명시적으로 다시 한번 전달
                "redirect_uri": "https://snowpalace1.github.io/hs-tier-overlay/"
            }
            
            try:
                # 오류 방지 3: 보안 차단을 피하기 위해 일반 브라우저 통신처럼 User-Agent 헤더 추가
                req_headers = {"User-Agent": "Mozilla/5.0"}
                token_res = requests.get(token_url, params=token_params, headers=req_headers)
                token_json = token_res.json()
                
                if "access_token" in token_json:
                    access_token = token_json["access_token"]
                    
                    user_info_url = "https://openapi.naver.com/v1/nid/me"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "User-Agent": "Mozilla/5.0"
                    }
                    user_res = requests.get(user_info_url, headers=headers)
                    user_json = user_res.json()
                    
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

        # SESE 원칙 적용: 단일 반환 지점
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
