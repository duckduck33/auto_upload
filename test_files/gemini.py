import google.generativeai as genai
import os
from typing import Optional
from dotenv import load_dotenv

class GeminiChat:
    def __init__(self, api_key: Optional[str] = None):
        """
        Gemini API 초기화
        
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
        
        # 모델 초기화 (무료 티어용 가벼운 모델)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = None
    
    def start_chat(self):
        """새로운 채팅 세션 시작"""
        self.chat = self.model.start_chat(history=[])
        return self.chat
    
    def ask_question(self, question: str) -> str:
        """
        질문에 대한 답변 받기
        
        Args:
            question: 질문 내용
            
        Returns:
            str: AI의 답변
        """
        try:
            if not self.chat:
                self.start_chat()
            
            response = self.chat.send_message(question)
            return response.text
            
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"
    
    def reset_chat(self):
        """채팅 히스토리 초기화"""
        self.chat = None
        return self.start_chat()

def main():
    """테스트용 메인 함수"""
    try:
        # Gemini 인스턴스 생성
        gemini = GeminiChat()
        
        print("=== Gemini AI 채팅 시작 ===")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
        
        while True:
            # 사용자 입력 받기
            user_input = input("질문: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                print("채팅을 종료합니다.")
                break
            
            if not user_input:
                continue
            
            # AI 답변 받기
            print("\n🤖 AI 답변:")
            response = gemini.ask_question(user_input)
            print(response)
            print("\n" + "="*50 + "\n")
    
    except ValueError as e:
        print(f"초기화 오류: {e}")
        print("환경변수 GEMINI_API_KEY를 설정하거나 API 키를 직접 전달하세요.")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    main() 