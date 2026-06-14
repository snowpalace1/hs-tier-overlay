from http.server import BaseHTTPRequestHandler
import urllib.parse
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # SESE 원칙 적용: 상태 코드와 이동할 주소 변수를 최상단에서 단 한 번만 초기화합니다.
        status_code = 200
        redirect_target = None
        error_message = None

        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = query_components.get("code", [None])[0]
        state = query_components.get("state", [None])[0]

        if not code or not state:
            status_code = 400
            error_message = "네이버 인증 코드 또는 state가 전달되지 않았습니다."
        else:
            client_id = "kLCeM46CJDEtQ3gqVGfV"
            client_secret = "SdTTjdGB3G"

            token_url = "https://nid.naver.com/oauth2.0/token"
            token_params = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state,
                # 🔥 핵심 수정 사항! 네이버 설정 및 index.html과 완벽하게 동일한 주소를 씁니다. 🔥
                "redirect_uri": "https://hs-tier-overlay.vercel.app/api/naver"
            }

            try:
                token_res = requests.get(token_url, params=token_params)
                token_json = token_res.json()

                if "access_token" in token_json:
                    access_token = token_json["access_token"]
                    
                    user_info_url = "https://openapi.naver.com/v1/nid/me"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    user_res = requests.get(user_info_url, headers=headers)
                    user_json = user_res.json()

                    if user_json.get("resultcode") == "00":
                        nickname = user_json.get("response", {}).get("nickname", "")
                        if nickname:
                            # 성공 시: 닉네임을 URL에 담아 깃허브 프론트엔드로 튕겨 보냅니다.
                            encoded_nickname = urllib.parse.quote(nickname)
                            status_code = 302
                            redirect_target = f"https://snowpalace1.github.io/hs-tier-overlay/?naver_name={encoded_nickname}"
                        else:
                            status_code = 400
                            error_message = "닉네임을 찾을 수 없습니다."
                    else:
                        status_code = 400
                        error_message = f"유저 정보 조회 실패: {user_json}"
                else:
                    status_code = 400
                    error_message = f"토큰 발급 실패: {token_json}"
            except Exception as e:
                status_code = 500
                error_message = f"서버 백엔드 통신 오류: {str(e)}"

        # SESE 원칙 적용: 함수의 맨 마지막에서 단 한 번만 응답을 보냅니다.
        if status_code == 302 and redirect_target:
            # 깃허브 웹페이지로 유저 화면을 이동시킵니다.
            self.send_response(302)
            self.send_header('Location', redirect_target)
            self.end_headers()
        else:
            # 실패 시 까만 텍스트가 아닌 커다란 HTML 글씨로 에러를 보여줍니다.
            self.send_response(status_code)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_error = f"<h1>네이버 인증 오류</h1><p>{error_message}</p>"
            self.wfile.write(html_error.encode('utf-8'))
