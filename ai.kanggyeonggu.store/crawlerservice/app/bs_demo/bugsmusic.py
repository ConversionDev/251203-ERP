import requests
from bs4 import BeautifulSoup
import json
import re
import sys
import io
from urllib.parse import urljoin

# Windows 콘솔 인코딩 문제 해결
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def crawl_bugs_chart():
    """
    벅스뮤직 실시간 차트를 크롤링하여 곡 정보를 JSON 형태로 반환
    """
    url = "https://music.bugs.co.kr/chart/track/realtime/total?wl_ref=M_contents_03_01"
    
    # 헤더 설정 (브라우저로 인식되도록)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # 웹페이지 요청
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 차트 테이블 찾기
        chart_table = soup.find('table', class_='list trackList byChart')
        
        if not chart_table:
            print("차트 테이블을 찾을 수 없습니다.")
            return []
        
        # 곡 정보 리스트
        songs = []
        
        # tbody 내의 tr 태그들 찾기
        tbody = chart_table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = chart_table.find_all('tr')[1:]  # 헤더 제외
        
        for idx, row in enumerate(rows, 1):
            try:
                song_data = {}
                
                # 순위 추출
                rank_cell = row.find('td', class_='ranking')
                if rank_cell:
                    rank_text = rank_cell.get_text(strip=True)
                    # 숫자만 추출
                    rank_match = re.search(r'\d+', rank_text)
                    song_data['rank'] = int(rank_match.group()) if rank_match else idx
                else:
                    song_data['rank'] = idx
                
                # 제목 추출
                title_cell = row.find('p', class_='title')
                if title_cell:
                    title_link = title_cell.find('a')
                    song_data['title'] = title_link.get_text(strip=True) if title_link else title_cell.get_text(strip=True)
                else:
                    # 대체 방법: td에서 직접 찾기
                    title_td = row.find('td', class_='left')
                    if title_td:
                        title_link = title_td.find('a')
                        song_data['title'] = title_link.get_text(strip=True) if title_link else "제목 없음"
                    else:
                        song_data['title'] = "제목 없음"
                
                # 아티스트 추출
                artist_cell = row.find('p', class_='artist')
                if artist_cell:
                    artist_links = artist_cell.find_all('a')
                    if artist_links:
                        artists = [link.get_text(strip=True) for link in artist_links]
                        song_data['artist'] = ', '.join(artists)
                    else:
                        song_data['artist'] = artist_cell.get_text(strip=True)
                else:
                    song_data['artist'] = "아티스트 없음"
                
                # 앨범 추출
                album_cell = row.find('p', class_='album')
                if album_cell:
                    album_link = album_cell.find('a')
                    song_data['album'] = album_link.get_text(strip=True) if album_link else album_cell.get_text(strip=True)
                else:
                    song_data['album'] = "앨범 없음"
                
                # 이미지 URL 추출 (선택사항)
                img_cell = row.find('td', class_='albumImg')
                if img_cell:
                    img_tag = img_cell.find('img')
                    if img_tag and img_tag.get('src'):
                        song_data['image_url'] = urljoin(url, img_tag['src'])
                
                # 데이터가 유효한 경우에만 추가
                if song_data.get('title') and song_data['title'] != "제목 없음":
                    songs.append(song_data)
                
            except Exception as e:
                print(f"행 {idx} 처리 중 오류: {e}")
                continue
        
        return songs
        
    except requests.RequestException as e:
        print(f"웹페이지 요청 오류: {e}")
        return []
    except Exception as e:
        print(f"크롤링 오류: {e}")
        return []

def print_chart_json():
    """
    차트 데이터를 JSON 형태로 터미널에 출력
    """
    print("벅스뮤직 실시간 차트 크롤링 시작...")
    
    chart_data = crawl_bugs_chart()
    
    if chart_data:
        # JSON 형태로 예쁘게 출력
        result = {
            "chart_type": "bugs_realtime",
            "total_count": len(chart_data),
            "songs": chart_data
        }
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n총 {len(chart_data)}곡의 차트 정보를 수집했습니다.")
    else:
        print("차트 데이터를 가져올 수 없습니다.")

if __name__ == "__main__":
    print_chart_json()
