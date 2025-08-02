import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import openai

# 🔐 API 키 설정
os.environ["OPENAI_API_KEY"] = "sk-..."  # ← 본인의 키로 교체
openai.api_key = os.environ["OPENAI_API_KEY"]

# ✅ 네이버 블로그 Access Token (OAuth 2.0 통해 수동 발급 필요)
NAVER_ACCESS_TOKEN = "YOUR_NAVER_ACCESS_TOKEN"

# -----------------------------------------------------------
# [1] 네이버 블로그 본문 크롤링
# -----------------------------------------------------------
def extract_blog_text(blog_url):
    try:
        # Step 1: 블로그 글 ID 추출
        parsed = urlparse(blog_url)
        query = parse_qs(parsed.query)
        blogId = query.get('blogId', [''])[0]
        logNo = query.get('logNo', [''])[0]

        # Step 2: iframe으로 실제 본문 HTML 불러오기
        iframe_url = f"https://blog.naver.com/PostView.nhn?blogId={blogId}&logNo={logNo}"
        res = requests.get(iframe_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        # Step 3: 본문 추출
        main_frame = soup.select_one("iframe#mainFrame")
        if main_frame:
            real_url = "https://blog.naver.com" + main_frame["src"]
            res2 = requests.get(real_url, headers={"User-Agent": "Mozilla/5.0"})
            soup2 = BeautifulSoup(res2.text, "html.parser")
            content = soup2.select_one("div.se-main-container")
            if not content:
                content = soup2.select_one("#postViewArea")
            return content.get_text(strip=True) if content else ""
        else:
            return ""
    except Exception as e:
        print(f"[Error] {blog_url}: {e}")
        return ""

# -----------------------------------------------------------
# [2] 키워드 및 문체 분석 (GPT 기반)
# -----------------------------------------------------------
def analyze_with_gpt(texts):
    combined_text = "\n\n".join(texts)[:8000]  # GPT token 제한 고려
    prompt = f"""
다음은 인기 네이버 블로그 글 모음이야. 이 글들을 바탕으로 공통된 핵심 키워드와 상위 노출을 위한 문체/구조 특징을 알려줘.

1. 자주 등장하는 핵심 키워드 5~7개
2. 문체(예: 친근한 말투, 질문형 제목 등)
3. 글 구성 방식 요약 (예: 서론-질문-본문-결론)

블로그 글 모음:
\"\"\"
{combined_text}
\"\"\"
    """
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()

# -----------------------------------------------------------
# [3] 유사한 스타일의 블로그 글 자동 생성
# -----------------------------------------------------------
def generate_similar_blog(style_analysis, topic="요즘 인기 많은 여행지 추천"):
    prompt = f"""
너는 블로그 마케터야. 아래 스타일 분석을 참고해서 '{topic}'에 대한 블로그 글을 써줘.

스타일 분석:
{style_analysis}

조건:
- 서론-본론-결론 구성
- 글 길이 1200자 이상
- 친근하고 신뢰가는 말투
- 독자가 관심을 가질 만한 포인트 강조

지금 바로 써줘:
"""
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return res.choices[0].message.content.strip()

# -----------------------------------------------------------
# [4] 네이버 블로그 자동 포스팅
# -----------------------------------------------------------
def upload_to_naver_blog(title, content):
    url = "https://openapi.naver.com/blog/writePost.json"
    headers = {
        "Authorization": f"Bearer {NAVER_ACCESS_TOKEN}"
    }
    data = {
        "title": title,
        "contents": content
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("✅ 블로그 업로드 완료!")
    else:
        print("❌ 업로드 실패:", response.text)

# -----------------------------------------------------------
# [5] 전체 실행 파이프라인
# -----------------------------------------------------------
def run_auto_blog_pipeline(blog_urls, topic):
    print("▶ 블로그 본문 크롤링 중...")
    texts = [extract_blog_text(url) for url in blog_urls]
    texts = [t for t in texts if t]

    print("▶ 스타일 및 키워드 분석 중...")
    style_info = analyze_with_gpt(texts)

    print("▶ 자동 글 작성 중...")
    new_article = generate_similar_blog(style_info, topic)

    print("▶ 블로그 업로드 중...")
    upload_to_naver_blog(f"{topic}에 대해 알아보자", new_article)

# -----------------------------------------------------------
# ▶ 실행 예시
# -----------------------------------------------------------
if __name__ == "__main__":
    blog_urls = [
        "https://blog.naver.com/abc123?Redirect=Log&logNo=123456789",
        "https://blog.naver.com/def456?Redirect=Log&logNo=234567890",
        # ... 총 10개 입력
    ]
    user_topic = "가을 제주도 여행지 추천"
    run_auto_blog_pipeline(blog_urls, user_topic)
