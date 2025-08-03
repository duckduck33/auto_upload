from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import GenerateRequest, GenerateResponse, UploadRequest, UploadResponse
from services import GeminiContentGenerator, upload_to_naver_blog
import uvicorn
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio
import sys

app = FastAPI(
    title="네이버 블로그 자동 업로드 API",
    description="키워드로 블로그 글을 생성하고 네이버 블로그에 자동 업로드하는 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 상태 관리 (실제 프로덕션에서는 Redis나 DB 사용 권장)
automation_state = {
    "is_running": False,
    "progress": 0,
    "status": "대기 중",
    "current_step": 0,
    "total_steps": 4,
    "step_description": "대기 중",
    "current_generating_post": None,  # 현재 생성 중인 글 정보
    "print_messages": []  # print 구문 메시지들
}

logs = []
generated_posts = []
current_generating_content = ""  # 현재 생성 중인 콘텐츠

# print 구문을 자동으로 automation_state에 추가하는 클래스
class PrintCapture:
    def __init__(self):
        self.original_stdout = sys.stdout
    
    def write(self, text):
        if text.strip():  # 빈 줄 제외
            automation_state["print_messages"].append({
                "timestamp": datetime.now().isoformat(),
                "message": text.strip(),
                "level": "info"
            })
        self.original_stdout.write(text)  # 원래 콘솔에도 출력
    
    def flush(self):
        self.original_stdout.flush()

# print 구문 캡처 시작
print_capture = PrintCapture()
sys.stdout = print_capture

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "네이버 블로그 자동 업로드 API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate - 키워드로 블로그 글 생성",
            "upload": "/upload - 생성된 글을 네이버 블로그에 업로드",
            "automation": "/automation/* - 자동화 관련 엔드포인트"
        }
    }

@app.post("/automation/start")
async def start_automation(request: Dict[str, Any]):
    """자동화 시작"""
    global current_generating_content
    
    try:
        keyword = request.get("keyword", "")
        post_count = request.get("postCount", 1)
        
        if not keyword:
            return {
                "success": False,
                "message": "키워드가 필요합니다"
            }
        
        # 상태 초기화
        automation_state["is_running"] = True
        automation_state["progress"] = 0
        automation_state["status"] = "자동화 시작 중..."
        automation_state["current_step"] = 0
        automation_state["total_steps"] = 5
        automation_state["step_description"] = "키워드 분석 중..."
        automation_state["print_messages"] = []  # print 메시지 초기화
        
        # 생성 중 상태 설정
        automation_state["current_generating_post"] = {
            "keyword": keyword,
            "started_at": datetime.now().isoformat(),
            "status": "생성 중..."
        }
        current_generating_content = "키워드 분석 중..."
        
        # 비동기로 글 생성 프로세스 시작
        asyncio.create_task(generate_post_process(keyword))
        
        return {
            "success": True,
            "message": "자동화가 시작되었습니다",
            "taskId": "task_001"
        }
        
    except Exception as e:
        automation_state["is_running"] = False
        automation_state["status"] = f"오류: {str(e)}"
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        return {
            "success": False,
            "message": f"자동화 시작 실패: {str(e)}"
        }

@app.post("/automation/stop")
async def stop_automation():
    """자동화 정지"""
    global current_generating_content
    
    try:
        automation_state["is_running"] = False
        automation_state["status"] = "자동화가 정지되었습니다"
        automation_state["progress"] = 0
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        
        return {
            "success": True,
            "message": "자동화가 정지되었습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"자동화 정지 실패: {str(e)}"
        }

@app.get("/automation/status")
async def get_automation_status():
    """자동화 상태 조회"""
    print(f"🔍 상태 조회 요청 - {automation_state['status']} (진행률: {automation_state['progress']}%)")
    return automation_state

@app.get("/automation/logs")
async def get_logs():
    """print 구문 로그 조회"""
    return automation_state["print_messages"]

@app.delete("/automation/logs/clear")
async def clear_logs():
    """로그 지우기"""
    automation_state["print_messages"].clear()
    return {"message": "로그가 지워졌습니다"}

@app.get("/automation/posts")
async def get_generated_posts():
    """생성된 글 조회"""
    print(f"🔍 생성된 글 조회 요청 - 현재 글 개수: {len(generated_posts)}")
    print(f"🔍 저장된 글 목록: {generated_posts}")
    return generated_posts

@app.post("/automation/reset")
async def reset_automation():
    """자동화 상태 초기화"""
    global current_generating_content
    
    automation_state["is_running"] = False
    automation_state["progress"] = 0
    automation_state["status"] = "대기 중"
    automation_state["current_step"] = 0
    automation_state["step_description"] = "대기 중"
    automation_state["current_generating_post"] = None
    current_generating_content = ""
    
    return {
        "success": True,
        "message": "자동화 상태가 초기화되었습니다"
    }

async def generate_post_process(keyword: str):
    """글 생성 프로세스를 비동기로 처리"""
    global current_generating_content
    
    try:
        # 1단계: 키워드 분석
        print(f"🔍 1단계: 키워드 분석 시작")
        automation_state["current_step"] = 1
        automation_state["progress"] = 25
        automation_state["status"] = "키워드 분석 중..."
        automation_state["step_description"] = "키워드 분석 중..."
        current_generating_content = "키워드 분석 중..."
        
        await asyncio.sleep(2)
        print(f"✅ 1단계: 키워드 분석 완료")
        print(f"🔍 현재 상태: {automation_state['status']}")
        
        # 2단계: AI 모델 초기화
        print(f"🔍 2단계: AI 모델 초기화 시작")
        automation_state["current_step"] = 2
        automation_state["progress"] = 50
        automation_state["status"] = "AI 모델 초기화 중..."
        automation_state["step_description"] = "AI 모델 초기화 중..."
        current_generating_content = "AI 모델 초기화 중..."
        
        await asyncio.sleep(2)
        print(f"✅ 2단계: AI 모델 초기화 완료")
        print(f"🔍 현재 상태: {automation_state['status']}")
        
        # 3단계: 콘텐츠 생성
        print(f"🔍 3단계: 콘텐츠 생성 시작")
        automation_state["current_step"] = 3
        automation_state["progress"] = 75
        automation_state["status"] = "콘텐츠 생성 중..."
        automation_state["step_description"] = "콘텐츠 생성 중..."
        current_generating_content = "콘텐츠 생성 중..."
        
        await asyncio.sleep(3)
        print(f"✅ 3단계: 콘텐츠 생성 완료")
        print(f"🔍 현재 상태: {automation_state['status']}")
        
        # 4단계: 글 생성 완료
        print(f"🔍 4단계: 글 생성 완료 시작")
        automation_state["current_step"] = 4
        automation_state["progress"] = 100
        automation_state["status"] = "생성 완료! 포스트 정리 중..."
        automation_state["step_description"] = "생성 완료! 포스트 정리 중..."
        current_generating_content = "생성 완료! 포스트 정리 중..."
        
        # Gemini 콘텐츠 생성기 초기화
        try:
            print(f"🔍 GeminiContentGenerator 초기화 시작...")
            generator = GeminiContentGenerator()
            print(f"✅ GeminiContentGenerator 초기화 성공")
        except Exception as e:
            error_msg = f"GeminiContentGenerator 초기화 실패: {str(e)}"
            print(f"❌ {error_msg}")
            raise e
        
        # 블로그 포스트 생성
        try:
            print(f"🔍 블로그 포스트 생성 시작...")
            blog_post = generator.generate_blog_post(keyword)
            print(f"✅ 블로그 포스트 생성 성공: {blog_post['title']}")
        except Exception as e:
            error_msg = f"블로그 글 생성 실패: {str(e)}"
            print(f"❌ {error_msg}")
            raise e
        
        # 생성된 글 저장
        post_data = {
            "id": f"post_{len(generated_posts) + 1}",
            "title": blog_post['title'],
            "content": blog_post['content'],
            "createdAt": datetime.now().isoformat(),
            "status": "생성 완료"
        }
        generated_posts.append(post_data)
        
        print(f"✅ 생성된 글 저장 완료: {blog_post['title']}")
        print(f"🔍 현재 저장된 글 개수: {len(generated_posts)}")
        print(f"🔍 저장된 글 내용: {post_data}")
        
        # 5단계: 네이버 블로그 자동 업로드
        print(f"🔍 5단계: 네이버 블로그 자동 업로드 시작")
        automation_state["current_step"] = 5
        automation_state["progress"] = 90
        automation_state["status"] = "네이버 블로그 업로드 중..."
        automation_state["step_description"] = "네이버 블로그 업로드 중..."
        current_generating_content = "네이버 블로그 업로드 중..."
        
        try:
            # 네이버 블로그 자동 업로드
            upload_result = upload_to_naver_blog(blog_post['title'], blog_post['content'])
            
            if upload_result["success"]:
                print(f"✅ 네이버 블로그 업로드 성공: {upload_result['data']['url']}")
                # 업로드 성공 시 글 정보 업데이트
                post_data["uploaded"] = True
                post_data["blogUrl"] = upload_result["data"]["url"]
                
            else:
                print(f"❌ 네이버 블로그 업로드 실패: {upload_result['error']}")
                
        except Exception as e:
            print(f"❌ 네이버 블로그 업로드 중 오류: {str(e)}")
        
        # 상태 초기화
        automation_state["is_running"] = False
        automation_state["status"] = "생성 완료"
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        
    except Exception as e:
        error_msg = f"글 생성 프로세스 실패: {str(e)}"
        print(f"❌ {error_msg}")
        
        # 오류가 발생해도 상태를 유지하여 UI에서 확인할 수 있도록 함
        automation_state["status"] = f"오류: {str(e)}"
        automation_state["current_generating_post"] = None
        current_generating_content = ""

@app.get("/automation/generating")
async def get_generating_post():
    """현재 생성 중인 글 조회"""
    return {
        "is_generating": automation_state["is_running"] and automation_state["current_generating_post"] is not None,
        "current_post": automation_state["current_generating_post"],
        "current_content": current_generating_content
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate_blog_post(request: GenerateRequest):
    """키워드를 기반으로 블로그 글을 생성하는 엔드포인트"""
    global current_generating_content
    
    try:
        # 생성 중 상태 설정
        automation_state["current_generating_post"] = {
            "keyword": request.keyword,
            "started_at": datetime.now().isoformat(),
            "status": "생성 중..."
        }
        current_generating_content = ""
        
        # Gemini 콘텐츠 생성기 초기화
        generator = GeminiContentGenerator()
        
        # 실시간 생성 과정 시뮬레이션
        current_generating_content = "키워드 분석 중..."
        await asyncio.sleep(1)
        
        current_generating_content = "AI 모델 초기화 중..."
        await asyncio.sleep(1)
        
        current_generating_content = "콘텐츠 생성 중..."
        await asyncio.sleep(2)
        
        # 블로그 포스트 생성
        blog_post = generator.generate_blog_post(request.keyword)
        
        current_generating_content = "생성 완료! 포스트 정리 중..."
        await asyncio.sleep(1)
        
        # 생성된 글 저장
        post_data = {
            "id": f"post_{len(generated_posts) + 1}",
            "title": blog_post['title'],
            "content": blog_post['content'],
            "createdAt": datetime.now().isoformat()
        }
        generated_posts.append(post_data)
        
        # 생성 중 상태 초기화
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        
        return GenerateResponse(
            success=True,
            data={
                "title": blog_post['title'],
                "content": blog_post['content'],
                "keyword": request.keyword
            }
        )
        
    except ValueError as e:
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        return GenerateResponse(
            success=False,
            error=f"블로그 글 생성 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/upload", response_model=UploadResponse)
async def upload_blog_post(request: UploadRequest):
    """생성된 블로그 글을 네이버 블로그에 업로드하는 엔드포인트"""
    try:
        # 네이버 블로그에 업로드
        result = upload_to_naver_blog(request.title, request.content)
        
        if result["success"]:
            return UploadResponse(
                success=True,
                data=result["data"]
            )
        else:
            return UploadResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        return UploadResponse(
            success=False,
            error=f"블로그 업로드 중 오류가 발생했습니다: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 