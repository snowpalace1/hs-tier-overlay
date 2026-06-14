import os
import requests
from supabase import create_client, Client

# 1. 깃허브 금고(Secrets)에서 꺼내오기
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

REGIONS = ["AP", "US", "EU"]
leaderboard_cache = {}

def fetch_leaderboards():
    print("블리자드 서버에서 하스스톤 리더보드 데이터를 가져옵니다...")
    for region in REGIONS:
        # 블리자드 공식 홈페이지의 퍼블릭 API 주소
        api_url = f"https://hearthstone.blizzard.com/ko-kr/api/community/leaderboardsData?region={region}&leaderboardId=standard"
        try:
            response = requests.get(api_url)
            data = response.json()
            rows = data.get("leaderboard", {}).get("rows", [])
            
            for row in rows:
                account_id = row.get("accountid") # 예: Rex#1234
                rank = int(row.get("rank"))
                
                if not account_id:
                    continue
                    
                # 닉네임만 추출하고 소문자로 변환 (예: Rex#1234 -> rex)
                nickname = account_id.split("#")[0].lower()
                
                # 중복 닉네임일 경우 더 높은 등수(작은 숫자) 저장
                if nickname in leaderboard_cache:
                    leaderboard_cache[nickname] = min(leaderboard_cache[nickname], rank)
                else:
                    leaderboard_cache[nickname] = rank
                    
            print(f"[{region}] 지역 데이터 수집 완료")
        except Exception as e:
            print(f"[{region}] 데이터 수집 실패: {e}")

def update_supabase():
    print(f"총 {len(leaderboard_cache)}명의 전설 유저 데이터를 DB에 업데이트합니다...")
    
    data_to_insert = []
    for nickname, rank in leaderboard_cache.items():
        data_to_insert.append({"nickname": nickname, "rank": rank})
    
    # 1000개씩 끊어서 Supabase에 밀어넣기 (무료 서버 과부하 방지)
    chunk_size = 1000
    for i in range(0, len(data_to_insert), chunk_size):
        chunk = data_to_insert[i:i + chunk_size]
        try:
            # upsert: 기존에 있는 닉네임이면 등수 업데이트, 없는 닉네임이면 새로 추가
            supabase.table("leaderboard").upsert(chunk).execute()
        except Exception as e:
            print(f"DB 업데이트 중 오류: {e}")
            
    print("Supabase DB 업데이트가 완벽하게 끝났습니다!")

if __name__ == "__main__":
    fetch_leaderboards()
    update_supabase()
