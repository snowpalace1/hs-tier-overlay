from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 쿼리 스트링(주소창)에서 code 가져오기
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]

        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code provided")
            return

        # 2. 블리자드에 입장권(code) 던지고 닉네임(배틀태그) 받기
        token_url = "https://oauth.battle.net/token"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://snowpalace1.github.io/hs-tier-overlay/",
            "client_id": os.environ.get("BNET_CLIENT_ID"),
            "client_id": os.environ.get("BNET_CLIENT_SECRET") # <- 요건 잠시 후 설정!
        }
        
        # ... (이하 인증 로직은 다음 단계에서 상세히 완성하겠습니다)
