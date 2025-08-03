import google.generativeai as genai
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import pyperclip
from typing import Optional
from dotenv import load_dotenv

def load_prompts():
    """prompt.json 파일에서 프롬프트를 로드하는 함수"""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompt.json')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        return prompts
    except Exception as e:
        print(f"prompt.json 파일 로드 중 오류 발생: {e}")
        return None

class GeminiContentGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """
        Gemini API를 사용한 콘텐츠 생성기 초기화
        
        Args:
            api_key: Gemini API 키. None이면 환경변수에서 가져옴
        """
        # API 키 하드코딩
        self.api_key = api_key or "AIzaSyBvNTKAbH0XaL1qaDJkH7JD39nvcjKSdyM"
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        
        # 모델 초기화
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.prompts = load_prompts()
        
        if not self.prompts:
            raise ValueError("prompt.json 파일을 로드할 수 없습니다.")
    
    def generate_title(self, keyword: str) -> str:
        """
        키워드를 기반으로 제목 생성 (하나만 생성)
        
        Args:
            keyword: 키워드
            
        Returns:
            str: 생성된 제목
        """
        try:
            prompt = self.prompts['titlePrompt']['content'].replace('${keyword}', keyword)
            # 하나의 제목만 생성하도록 프롬프트 수정
            prompt += "\n\n중요: 반드시 하나의 제목만 생성해주세요. 여러 개의 제목을 나열하지 마세요."
            response = self.model.generate_content(prompt)
            title = response.text.strip()
            
            # 여러 줄로 나뉘어 있다면 첫 번째 줄만 사용
            if '\n' in title:
                title = title.split('\n')[0].strip()
            
            # 마크다운 형식 제거
            title = title.replace('**', '').replace('*', '').replace('#', '').strip()
            
            return title
        except Exception as e:
            print(f"제목 생성 중 오류: {e}")
            return f"{keyword}에 대한 블로그 포스트"
    
    def generate_content(self, title: str, keyword: str) -> str:
        """
        제목과 키워드를 기반으로 본문 생성 (해시태그 포함)
        
        Args:
            title: 제목
            keyword: 키워드
            
        Returns:
            str: 생성된 본문 (해시태그 포함)
        """
        try:
            # 본문 생성
            content_prompt = self.prompts['contentPrompt']['content']
            content_prompt = content_prompt.replace('${title}', title)
            content_prompt = content_prompt.replace('${keyword}', keyword)
            content_prompt = content_prompt.replace('${outline}', '')  # 빈 문자열로 대체
            
            response = self.model.generate_content(content_prompt)
            content = response.text.strip()
            
            # 해시태그 생성
            tags_prompt = self.prompts['tagsPrompt']['content']
            tags_prompt = tags_prompt.replace('${title}', title)
            tags_prompt = tags_prompt.replace('${outline}', '')  # 빈 문자열로 대체
            
            tags_response = self.model.generate_content(tags_prompt)
            tags = tags_response.text.strip()
            
            # 본문 끝에 해시태그 추가
            full_content = content + "\n\n" + tags
            
            return full_content
        except Exception as e:
            print(f"본문 생성 중 오류: {e}")
            return f"{title}에 대한 내용입니다.\n\n#블로그 #포스팅"
    
    def generate_tags(self, title: str) -> str:
        """
        제목을 기반으로 태그 생성
        
        Args:
            title: 제목
            
        Returns:
            str: 생성된 태그들
        """
        try:
            prompt = self.prompts['tagsPrompt']['content']
            prompt = prompt.replace('${title}', title)
            prompt = prompt.replace('${outline}', '')  # 빈 문자열로 대체
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"태그 생성 중 오류: {e}")
            return "#블로그 #포스팅"
    
    def generate_blog_post(self, keyword: str) -> dict:
        """
        키워드를 기반으로 완전한 블로그 포스트 생성
        
        Args:
            keyword: 키워드
            
        Returns:
            dict: 제목, 내용을 포함한 딕셔너리 (태그는 본문에 포함됨)
        """
        print(f"🔍 키워드 '{keyword}'로 블로그 포스트를 생성하는 중...")
        
        # 1. 제목 생성 (하나만)
        print("📝 제목 생성 중...")
        title = self.generate_title(keyword)
        print(f"✅ 제목: {title}")
        
        # 2. 본문 생성 (해시태그 포함)
        print("📄 본문 생성 중...")
        content = self.generate_content(title, keyword)
        print(f"✅ 본문 길이: {len(content)}자")
        
        return {
            'title': title,
            'content': content
        }

def load_naver_info():
    """info.json 파일에서 네이버 로그인 정보를 로드하는 함수"""
    try:
        info_path = os.path.join(os.path.dirname(__file__), 'info.json')
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        return info
    except Exception as e:
        print(f"info.json 파일 로드 중 오류 발생: {e}")
        return None

def wait_for_element_not_present(driver, selector, timeout=5):
    """지정된 선택자의 요소가 DOM에서 사라질 때까지 기다리는 함수"""
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return True
    except TimeoutException:
        return False

def handle_popups(driver):
    """글쓰기 과정에서 나타나는 팝업들을 처리하는 함수"""
    print("팝업 및 사이드바 처리 시도 중...")
    
    popup_selectors = [
        "button.se-popup-button.se-popup-button-cancel",
        "button.se-help-panel-close-button",
        "button.se-popup-button-cancel",
        "button.se-popup-close",
        "button[aria-label='닫기']",
        "button[data-log='Imot.close']",
    ]
    
    popup_closed_count = 0
    
    for _ in range(5):
        is_any_popup_found = False
        for selector in popup_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].is_displayed():
                is_any_popup_found = True
                try:
                    driver.execute_script("arguments[0].click();", elements[0])
                    print(f"✅ 팝업 닫기 성공: {selector}")
                    time.sleep(2)
                    if wait_for_element_not_present(driver, selector):
                        print(f"✅ 팝업이 완전히 사라진 것을 확인했습니다.")
                        popup_closed_count += 1
                        time.sleep(1)
                        break
                    else:
                        print(f"⚠️ 팝업이 닫힌 것처럼 보였지만, 여전히 DOM에 존재합니다. 다음 시도...")
                        time.sleep(1)
                except Exception as e:
                    print(f"팝업 닫기 시도 중 예외 발생: {e}")
                    time.sleep(1)
                    continue
        
        if not is_any_popup_found:
            time.sleep(1)
            break

    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        print("✅ ESC 키로 팝업 닫기 시도 완료")
        time.sleep(2)
    except:
        print("⚠️ ESC 키로 팝업 닫기 시도 실패")

    if popup_closed_count > 0:
        print(f"총 {popup_closed_count}개의 팝업을 성공적으로 닫았습니다.")
        return True
    else:
        print("⚠️ 팝업을 닫을 버튼을 찾지 못했거나 닫히지 않았습니다.")
        return False

def upload_to_naver_blog(title: str, content: str) -> dict:
    """네이버 블로그에 제목과 내용을 자동으로 업로드하는 함수"""
    print("네이버 블로그 자동 업로드를 시작합니다.")
    
    naver_info = load_naver_info()
    if not naver_info:
        return {"success": False, "error": "info.json 파일에서 로그인 정보를 불러올 수 없습니다."}
    
    driver = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print("🔍 이제부터 업로드를 진행합니다...")
            # 웹 드라이버 설정
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                # 레일웨이 환경에 맞는 Chrome 옵션 추가
                chrome_options.add_argument("--headless")  # 헤드리스 모드
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                
                # Docker에서 설치한 ChromeDriver 사용
                service = Service("/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ Chrome 드라이버 설정 완료")
            except Exception as e:
                print(f"ChromeDriver 오류: {e}")
                # 대체 방법으로 시도
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    print(f"Chrome 드라이버 초기화 실패: {e2}")
                    raise e2
        
            driver.maximize_window()
            
            # 자동화 감지 방지
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get('https://nid.naver.com/nidlogin.login')
            time.sleep(5)  # 대기 시간 증가
        
            # 직접 입력 방식으로 로그인 (헤드리스 환경 대응)
            id_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "id")))
            id_field.click()
            id_field.clear()
            time.sleep(2)
            # 직접 입력
            for char in naver_info['id']:
                id_field.send_keys(char)
                time.sleep(0.1)
            time.sleep(3)
            
            pw_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pw")))
            pw_field.click()
            pw_field.clear()
            time.sleep(2)
            # 직접 입력
            for char in naver_info['pw']:
                pw_field.send_keys(char)
                time.sleep(0.1)
            time.sleep(3)
            
            login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "log.login")))
            login_button.click()
            time.sleep(8)  # 로그인 후 대기 시간 증가
        
            # 블로그 글쓰기 페이지로 이동 (아이디로 자동 추측)
            blog_id = naver_info['id']
            blog_write_url = f"https://blog.naver.com/{blog_id}?Redirect=Write&categoryNo=1"
            driver.get(blog_write_url)
            time.sleep(8)  # 페이지 로딩 대기 시간 증가
        
            # iframe 전환
            WebDriverWait(driver, 15).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
            
            if not handle_popups(driver):
                print("⚠️ 팝업 처리 실패")
        
            # 제목 입력
            title_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".se-section-documentTitle"))
            )
            title_element.click()
            time.sleep(2)
            actions = ActionChains(driver)
            for char in title:
                actions.send_keys(char)
                actions.pause(0.05)  # 타이핑 속도 증가
            actions.perform()
            time.sleep(3)
        
            # 내용 입력
            content_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".se-section-text"))
            )
            content_element.click()
            time.sleep(2)
            actions = ActionChains(driver)
            for char in content:
                actions.send_keys(char)
                actions.pause(0.03)  # 타이핑 속도 증가
            actions.perform()
            time.sleep(5)
        
            # 첫 번째 발행 버튼 클릭
            publish_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.publish_btn__m9KHH"))
            )
            driver.execute_script("arguments[0].click();", publish_button)
            time.sleep(3)
            
            # 두 번째 발행 버튼 (최종 확인) 클릭
            confirm_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.confirm_btn__WEaBq"))
            )
            driver.execute_script("arguments[0].click();", confirm_button)
            
            time.sleep(10)  # 발행 완료 대기 시간 증가
            
            print("✅ 네이버 블로그 업로드 성공!")
            blog_id = naver_info['id']
            return {"success": True, "data": {"title": title, "url": f"https://blog.naver.com/{blog_id}"}}
            
        except Exception as e:
            retry_count += 1
            print(f"❌ 업로드 시도 {retry_count} 실패: {e}")
            
            if driver:
                try:
                    driver.save_screenshot(f'error_screenshot_retry_{retry_count}.png')
                except:
                    pass
                driver.quit()
                driver = None
            
            if retry_count < max_retries:
                print(f"🔄 {retry_count}초 후 재시도합니다...")
                time.sleep(retry_count * 2)  # 재시도 간격 증가
                continue
            else:
                print(f"❌ 최대 재시도 횟수({max_retries})에 도달했습니다.")
                return {"success": False, "error": f"블로그 업로드 실패: {str(e)}"}
        
 