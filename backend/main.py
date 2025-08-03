from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import GenerateRequest, GenerateResponse, UploadRequest, UploadResponse
from services import GeminiContentGenerator, upload_to_naver_blog
import uvicorn
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
import json
import asyncio
import sys

app = FastAPI(
    title="네이버 블로그 자동 업로드 API",
    description="키워드로 블로그 컨텐츠을 생성하고 네이버 블로그에 자동 업로드하는 API",
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
    "current_generating_post": None,  # 현재 생성 중인 컨텐츠 정보
    "print_messages": []  # print 구문 메시지들
}

logs = []
generated_posts = []
current_generating_content = ""  # 현재 생성 중인 콘텐츠

# 한국 시간대 설정
KST = timezone(timedelta(hours=9))

# print 구문을 자동으로 automation_state에 추가하는 함수
def add_to_logs(message: str):
    automation_state["print_messages"].append({
        "timestamp": datetime.now(KST).isoformat(),
        "message": message,
        "level": "info"
    })

@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "네이버 블로그 자동 업로드 API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate - 키워드로 블로그 컨텐츠 생성",
            "upload": "/upload - 생성된 컨텐츠을 네이버 블로그에 업로드",
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
        automation_state["total_steps"] = 3
        automation_state["step_description"] = "AI 모델 초기화 중..."
        automation_state["print_messages"] = []  # print 메시지 초기화
        
        # 생성 중 상태 설정
        automation_state["current_generating_post"] = {
            "keyword": keyword,
            "started_at": datetime.now(KST).isoformat(),
            "status": "생성 중..."
        }
        current_generating_content = "AI 모델 초기화 중..."
        
        # 비동기로 컨텐츠 생성 프로세스 시작
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
    """생성된 컨텐츠 조회"""
    print(f"🔍 생성된 컨텐츠 조회 요청 - 현재 컨텐츠 개수: {len(generated_posts)}")
    print(f"🔍 저장된 컨텐츠 목록: {generated_posts}")
    return generated_posts

@app.get("/automation/generating")
async def get_generating_post():
    """생성 중인 컨텐츠 조회"""
    print(f"🔍 생성 중인 컨텐츠 조회 요청")
    print(f"🔍 current_generating_post: {automation_state['current_generating_post']}")
    print(f"🔍 current_generating_content: {current_generating_content}")
    
    if automation_state["current_generating_post"]:
        return {
            "keyword": automation_state["current_generating_post"]["keyword"],
            "startedAt": automation_state["current_generating_post"]["started_at"],
            "status": automation_state["current_generating_post"]["status"],
            "isGenerating": automation_state["is_running"]
        }
    return None

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
    """컨텐츠 생성 프로세스를 비동기로 처리"""
    global current_generating_content
    
    try:
        # 1단계: AI 모델 초기화
        print(f"🔍 1단계: AI 모델 초기화 시작 (키워드: {keyword})")
        add_to_logs(f"🔍 1단계: AI 모델 초기화 시작 (키워드: {keyword})")
        automation_state["current_step"] = 1
        automation_state["progress"] = 33
        automation_state["status"] = f"AI 모델 초기화 중... (키워드: {keyword})"
        automation_state["step_description"] = f"AI 모델 초기화 중... (키워드: {keyword})"
        current_generating_content = f"AI 모델 초기화 중... (키워드: {keyword})"
        
        # Gemini 콘텐츠 생성기 초기화
        try:
            generator = GeminiContentGenerator()
        except Exception as e:
            error_msg = f"AI 모델 초기화 실패: {str(e)}"
            print(f"❌ {error_msg}")
            add_to_logs(f"❌ {error_msg}")
            raise e
        
        await asyncio.sleep(2)
        print(f"✅ 1단계: AI 모델 초기화 완료 (키워드: {keyword})")
        add_to_logs(f"✅ 1단계: AI 모델 초기화 완료 (키워드: {keyword})")
        
        # 2단계: 블로그 컨텐츠 생성
        print(f"🔍 2단계: 블로그 컨텐츠 생성 시작")
        add_to_logs("🔍 2단계: 블로그 컨텐츠 생성 시작")
        automation_state["current_step"] = 2
        automation_state["progress"] = 66
        automation_state["status"] = "블로그 컨텐츠 생성 중..."
        automation_state["step_description"] = "블로그 컨텐츠 생성 중..."
        current_generating_content = "블로그 컨텐츠 생성 중..."
        
        # 블로그 컨텐츠 생성
        try:
            blog_post = generator.generate_blog_post(keyword)
        except Exception as e:
            error_msg = f"블로그 컨텐츠 생성 실패: {str(e)}"
            print(f"❌ {error_msg}")
            add_to_logs(f"❌ {error_msg}")
            raise e
        
        # 생성된 컨텐츠 저장
        post_data = {
            "id": f"post_{len(generated_posts) + 1}",
            "title": blog_post['title'],
            "content": blog_post['content'],
            "createdAt": datetime.now(KST).isoformat(),
            "status": "생성 완료"
        }
        generated_posts.append(post_data)
        

        print(f"✅ 2단계: 블로그 컨텐츠 생성 완료")
        add_to_logs("✅ 2단계: 블로그 컨텐츠 생성 완료")
        
        # 3단계: 네이버 블로그 업로드
        print(f"🔍 3단계: 네이버 블로그 업로드 시작")
        add_to_logs("🔍 3단계: 네이버 블로그 업로드 시작")
        automation_state["current_step"] = 3
        automation_state["progress"] = 100
        automation_state["status"] = "네이버 블로그 업로드 중..."
        automation_state["step_description"] = "네이버 블로그 업로드 중..."
        current_generating_content = "네이버 블로그 업로드 중..."
        await asyncio.sleep(2)       
        # 네이버 블로그 자동 업로드
        try:
            upload_result = upload_to_naver_blog(blog_post['title'], blog_post['content'])
            
            if upload_result["success"]:
                # 업로드 성공 시 컨텐츠 정보 업데이트
                post_data["uploaded"] = True
                post_data["blogUrl"] = upload_result["data"]["url"]
                
        except Exception as e:
            print(f"❌ 네이버 블로그 업로드 중 오류: {str(e)}")
            add_to_logs(f"❌ 네이버 블로그 업로드 중 오류: {str(e)}")
        
        await asyncio.sleep(2)
        print(f"✅ 3단계: 네이버 블로그 업로드 완료")
        add_to_logs("✅ 3단계: 네이버 블로그 업로드 완료")
        
        # 상태 초기화
        automation_state["is_running"] = False
        automation_state["status"] = "생성 완료"
        automation_state["current_generating_post"] = None
        current_generating_content = ""
        
    except Exception as e:
        error_msg = f"컨텐츠 생성 프로세스 실패: {str(e)}"
        print(f"❌ {error_msg}")
        add_to_logs(f"❌ {error_msg}")
        
        # 오류가 발생해도 상태를 유지하여 UI에서 확인할 수 있도록 함
        automation_state["status"] = f"오류: {str(e)}"
        automation_state["current_generating_post"] = None
        current_generating_content = ""



@app.post("/generate", response_model=GenerateResponse)
async def generate_blog_post(request: GenerateRequest):
    """키워드를 기반으로 블로그 컨텐츠을 생성하는 엔드포인트"""
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
        
        # 생성된 컨텐츠 저장
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
            error=f"블로그 컨텐츠 생성 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/upload", response_model=UploadResponse)
async def upload_blog_post(request: UploadRequest):
    """생성된 블로그 컨텐츠을 네이버 블로그에 업로드하는 엔드포인트"""
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

@app.post("/naver/save-credentials")
async def save_naver_credentials(request: Dict[str, Any]):
    """네이버 로그인 정보 저장"""
    try:
        naver_id = request.get("naverId", "")
        naver_pw = request.get("naverPw", "")
        
        if not naver_id or not naver_pw:
            return {
                "success": False,
                "message": "네이버 아이디와 비밀번호가 필요합니다"
            }
        
        # info.json 파일에 저장
        info_data = {
            "id": naver_id,
            "pw": naver_pw
        }
        
        import os
        info_path = os.path.join(os.path.dirname(__file__), 'info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "네이버 로그인 정보가 저장되었습니다"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"네이버 로그인 정보 저장 실패: {str(e)}"
        }

@app.get("/naver/get-credentials")
async def get_naver_credentials():
    """네이버 로그인 정보 조회"""
    try:
        import os
        info_path = os.path.join(os.path.dirname(__file__), 'info.json')
        
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            return {
                "success": True,
                "data": {
                    "naverId": info_data.get("id", ""),
                    "hasPassword": bool(info_data.get("pw", ""))
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "naverId": "",
                    "hasPassword": False
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"네이버 로그인 정보 조회 실패: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 