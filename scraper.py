import os
import requests
from supabase import create_client, Client
import time

# 1. 깃허브 금고(Secrets)에서 꺼내오기
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

REGIONS = ["AP", "US", "EU"]
leaderboard_cache = {}

def fetch_leaderboards():
    print("블리자드 서버에서 하스스톤 리더보드 데이터를 가져옵니다...")
    for region in REGIONS:
        page = 1
        total_pages = 1 # 초기값
        
        while page <= total_pages:
            api_url = f"https://hearthstone.blizzard.com/ko-kr/api/community/leaderboardsData?region={region}&leaderboardId=standard&page={page}"
            try:
                response = requests.get(api_url)
                data = response.json()
                
                # 첫 페이지에서 전체 페이지 수(totalPages)를 파악합니다
                if page == 1:
                    total_pages = data.get("leaderboard", {}).get("pagination", {}).get("totalPages", 1)
                    print(f"[{region}] 총 {total_pages} 페이지 데이터를 수집 시작...")
                    
                rows = data.get("leaderboard", {}).get("rows", [])
                
                for row in rows:
                    account_id = row.get("accountid")
                    rank = int(row.get("rank"))
                    
                    if not account_id:
                        continue
                        
                    nickname = account_id.split("#")[0].lower()
                    
                    if nickname in leaderboard_cache:
                        leaderboard_cache[nickname] = min(leaderboard_cache[nickname], rank)
                    else:
                        leaderboard_cache[nickname] = rank
                        
                # 다음 페이지로 넘어갑니다
                page += 1
                
                # 블리자드 서버가 공격으로 오해하지 않도록 아주 살짝(0.1초) 대기합니다
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[{region}] {page}페이지 데이터 수집 실패: {e}")
                break

        print(f"[{region}] 지역 데이터 수집 완료")

def update_supabase():
    print(f"총 {len(leaderboard_cache)}명의 전설 유저 데이터를 DB에 업데이트합니다...")
    
    data_to_insert = []
    for nickname, rank in leaderboard_cache.items():
        data_to_insert.append({"nickname": nickname, "rank": rank})
    
    # 1000개씩 끊어서 Supabase에 밀어넣기
    chunk_size = 1000
    for i in range(0, len(data_to_insert), chunk_size):
        chunk = data_to_insert[i:i + chunk_size]
        try:
            supabase.table("leaderboard").upsert(chunk).execute()
        except Exception as e:
            print(f"DB 업데이트 중 오류: {e}")
            
    print("Supabase DB 업데이트가 완벽하게 끝났습니다!")

if __name__ == "__main__":
    fetch_leaderboards()
    update_supabase()
