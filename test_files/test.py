# 이 파일은 naver_blog_auto_posting 프로젝트의 네이버 블로그 자동 업로드를 테스트하기 위한 샘플 코드입니다.
# 실제 동작을 위해서는 Selenium 및 웹 드라이버가 설치되어 있어야 합니다.
# pip install selenium

import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pyperclip
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

def load_naver_info():
    """
    info.json 파일에서 네이버 로그인 정보를 로드하는 함수
    :return: 로그인 정보 딕셔너리
    """
    try:
        with open('info.json', 'r', encoding='utf-8') as f:
            info = json.load(f)
        return info
    except Exception as e:
        print(f"info.json 파일 로드 중 오류 발생: {e}")
        return None

def load_sample_content():
    """
    sample.json 파일에서 블로그 포스팅용 제목과 내용을 로드하는 함수
    :return: 제목과 내용 딕셔너리
    """
    try:
        with open('sample.json', 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
        return sample_data
    except Exception as e:
        print(f"sample.json 파일 로드 중 오류 발생: {e}")
        return None

def load_prompts():
    """
    prompt.json 파일에서 프롬프트를 로드하는 함수
    :return: 프롬프트 딕셔너리
    """
    try:
        with open('prompt.json', 'r', encoding='utf-8') as f:
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
        # .env 파일 로드
        load_dotenv()
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API 키가 필요합니다. 환경변수 GEMINI_API_KEY를 설정하거나 api_key 파라미터를 전달하세요.")
        
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
    """
    글쓰기 과정에서 나타나는 팝업들을 처리하는 함수
    - 여러 팝업 선택자를 순차적으로 확인하고 클릭
    """
    print("팝업 및 사이드바 처리 시도 중...")
    
    popup_selectors = [
        "button.se-popup-button.se-popup-button-cancel",  # 작성중 팝업 취소 버튼
        "button.se-help-panel-close-button",  # 도움말 팝업
        "button.se-popup-button-cancel",      # 팝업 취소 버튼
        "button.se-popup-close",              # 일반적인 팝업
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
                    time.sleep(2)  # 팝업 닫기 후 2초 대기
                    if wait_for_element_not_present(driver, selector):
                        print(f"✅ 팝업이 완전히 사라진 것을 확인했습니다.")
                        popup_closed_count += 1
                        time.sleep(1)  # 다음 팝업 처리 전 1초 대기
                        break
                    else:
                        print(f"⚠️ 팝업이 닫힌 것처럼 보였지만, 여전히 DOM에 존재합니다. 다음 시도...")
                        time.sleep(1)  # 재시도 전 1초 대기
                except Exception as e:
                    print(f"팝업 닫기 시도 중 예외 발생: {e}")
                    time.sleep(1)  # 예외 발생 시 1초 대기
                    continue
        
        if not is_any_popup_found:
            time.sleep(1)  # 팝업이 없을 때도 1초 대기
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

def upload_to_naver_blog(title, content):
    """
    네이버 블로그에 제목과 내용을 자동으로 업로드하는 함수
    :param title: 블로그 글 제목
    :param content: 블로그 글 내용
    """
    print("네이버 블로그 자동 업로드 테스트를 시작합니다.")
    
    naver_info = load_naver_info()
    if not naver_info:
        print("❌ info.json 파일에서 로그인 정보를 불러올 수 없습니다.")
        return
    
    driver = None
    try:
        # === 1. 웹 드라이버 설정 및 브라우저 열기 ===
        print("=== 웹 드라이버 설정 중 ===")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Chrome 드라이버 설정 완료")
        except Exception as e:
            print(f"ChromeDriverManager 오류: {e}")
            print("시스템에 설치된 Chrome 드라이버를 사용합니다.")
            driver = webdriver.Chrome(options=chrome_options)
        
        driver.maximize_window()
        print("✅ 브라우저 창 전체 화면으로 설정 완료")
        
        driver.get('https://nid.naver.com/nidlogin.login')
        print("네이버 로그인 페이지로 이동했습니다.")
        time.sleep(3)
        
        # === 2. 복사-붙여넣기 로그인 ===
        print("=== 복사-붙여넣기 로그인 시도 ===")
        id_field = driver.find_element(By.ID, "id")
        id_field.click()
        id_field.clear()
        time.sleep(1)
        pyperclip.copy(naver_info['id'])
        id_field.send_keys(Keys.CONTROL + 'v')
        print(f"✅ ID 복사-붙여넣기 완료")
        time.sleep(2)
        
        pw_field = driver.find_element(By.ID, "pw")
        pw_field.click()
        pw_field.clear()
        time.sleep(1)
        pyperclip.copy(naver_info['pw'])
        pw_field.send_keys(Keys.CONTROL + 'v')
        print(f"✅ 비밀번호 복사-붙여넣기 완료")
        time.sleep(2)
        
        login_button = driver.find_element(By.ID, "log.login")
        login_button.click()
        print("✅ 로그인 버튼 클릭")
        
        print("로그인 처리 중... 잠시 기다려주세요.")
        time.sleep(5)
        
        # === 3. 블로그 글쓰기 페이지로 이동 ===
        print("=== 블로그 글쓰기 페이지로 이동 ===")
        blog_write_url = "https://blog.naver.com/biz8link?Redirect=Write&categoryNo=1"
        driver.get(blog_write_url)
        print("✅ 블로그 글쓰기 페이지로 직접 이동")
        time.sleep(5)
        
        # === 4. 제목과 내용 입력 ===
        print("=== 제목과 내용 입력 시작 ===")
        
        # iframe 전환
        print("✅ iframe으로 전환")
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame")))
        print("✅ iframe 전환 완료")
        

        
        if not handle_popups(driver):
            print("⚠️ 팝업 처리 실패. 수동으로 팝업을 닫고, Enter 키를 눌러주세요.")
            input("-> 수동으로 팝업을 닫고, 이 콘솔 창에서 Enter 키를 누르면 다음 단계로 진행합니다...")
        
        # 제목 입력 필드
        print("✅ 제목 입력 필드를 기다리는 중...")
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".se-section-documentTitle"))
        )
        title_element.click()
        # ActionChains를 사용하여 텍스트 입력
        actions = ActionChains(driver)
        for char in title:
            actions.send_keys(char)
            actions.pause(0.01) # 0.01초 간격으로 입력
        actions.perform()
        print(f"✅ 제목: '{title}'을 입력했습니다.")
        time.sleep(2)
        
        # 내용 입력 필드
        print("✅ 내용 입력 필드를 기다리는 중...")
        content_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".se-section-text"))
        )
        content_element.click()
        # ActionChains를 사용하여 텍스트 입력
        actions = ActionChains(driver)
        for char in content:
            actions.send_keys(char)
            actions.pause(0.01) # 0.01초 간격으로 입력
        actions.perform()
        print("✅ 내용을 입력했습니다.")
        time.sleep(3)
        
        # === 5. 첫 번째 발행 버튼 클릭 (iframe 내부에서) ===
        print("=== 첫 번째 발행 버튼 클릭 ===")
        
        # 발행 버튼이 나타날 때까지 명시적으로 기다립니다.
        print("✅ 첫 번째 발행 버튼을 기다리는 중...")
        publish_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.publish_btn__m9KHH"))
        )
        print(f"✅ 첫 번째 발행 버튼 발견: button.publish_btn__m9KHH")
        driver.execute_script("arguments[0].click();", publish_button)
        print("첫 번째 발행 버튼을 JavaScript로 클릭했습니다.")
        
        # === 6. 두 번째 발행 버튼 (최종 확인) 클릭 (iframe 내부에서) ===
        print("=== 두 번째 발행 버튼 (최종 확인) 클릭 ===")
        
        # 최종 확인 팝업이 나타날 때까지 명시적으로 기다립니다.
        print("✅ 최종 확인 발행 버튼을 기다리는 중...")
        confirm_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.confirm_btn__WEaBq"))
        )
        print(f"✅ 최종 확인 발행 버튼 발견: button.confirm_btn__WEaBq")
        driver.execute_script("arguments[0].click();", confirm_button)
        print("최종 발행 버튼을 JavaScript로 클릭했습니다.")
        
        # 발행 완료 후 추가적인 대기
        time.sleep(8)
        
    except Exception as e:
        print(f"자동 업로드 과정 중 오류가 발생했습니다: {e}")
        if driver:
            print("스크린샷을 찍습니다.")
            driver.save_screenshot('error_screenshot.png')
            
    finally:
        print("스크립트 실행이 완료되었습니다. 브라우저가 자동으로 종료되지 않습니다.")
        print("브라우저 창을 직접 닫아주세요.")
        # driver.quit()  # 브라우저 자동 종료 방지를 위해 주석 처리

def run_blog_upload_pipeline():
    """
    sample.json에서 제목과 내용을 읽어서 네이버 블로그에 업로드하는 파이프라인
    """
    print("=== 네이버 블로그 자동 업로드 파이프라인 ===")
    
    sample_data = load_sample_content()
    
    if not sample_data:
        print("❌ sample.json 파일에서 제목과 내용을 불러올 수 없습니다.")
        return
    
    print(f"✅ 제목: {sample_data['title']}")
    print(f"✅ 내용 길이: {len(sample_data['content'])} 문자")
    
    upload_to_naver_blog(sample_data['title'], sample_data['content'])

def run_keyword_based_pipeline():
    """
    키워드 입력으로 Gemini API를 사용해서 글을 생성하고 네이버 블로그에 업로드하는 파이프라인
    """
    print("=== 키워드 기반 블로그 자동 생성 및 업로드 파이프라인 ===")
    
    try:
        # Gemini 콘텐츠 생성기 초기화
        generator = GeminiContentGenerator()
        print("✅ Gemini API 연결 성공")
        
        # 키워드 입력 받기
        keyword = input("📝 블로그 포스트 키워드를 입력하세요: ").strip()
        if not keyword:
            print("❌ 키워드를 입력해주세요.")
            return
        
        # 블로그 포스트 생성
        blog_post = generator.generate_blog_post(keyword)
        
        print("\n" + "="*50)
        print("🎉 블로그 포스트 생성 완료!")
        print("="*50)
        print(f"📝 제목: {blog_post['title']}")
        print(f"📄 내용 길이: {len(blog_post['content'])}자")
        print("🏷️ 해시태그는 본문 끝에 포함됨")
        print("="*50)
        
        # 생성된 내용을 네이버 블로그에 업로드
        print("\n🚀 네이버 블로그에 업로드를 시작합니다...")
        upload_to_naver_blog(blog_post['title'], blog_post['content'])
        
    except ValueError as e:
        print(f"❌ 초기화 오류: {e}")
        print("환경변수 GEMINI_API_KEY를 설정하거나 API 키를 확인하세요.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    # 키워드 기반 블로그 자동 생성 및 업로드 실행
    run_keyword_based_pipeline()