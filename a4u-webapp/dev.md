# dev.md: 백엔드 에이전트 작업 지침

## 1. 목표

샘플 3종 기반 데이터 처리를 위한 Flask 서버 구축 및 AI 코칭 연동.

## **2\. 주요 기능 및 구현 규칙**

* **DB 스키마:** SQLite 사용. 샘플 3종에 맞춘 고정 스키마 및 확장 가능한 JSONB 필드 활용.  
* **파일 업로드:** PDF/WORD 외 형식 업로드 시 400 에러와 함께 "지원하지 않는 파일 형식" 응답 반환.  
* **AI 코칭:** 샘플 3종에 대한 Few-shot Prompting 적용. 샘플 이외의 케이스는 정중한 안내 메시지 반환.  
* **통계/메모:** 단순 카운트 기반 대시보드 API 구현.

## **3\. 3일차 마일스톤**

* **1일차:** SQLite DB 테이블 생성 및 구글 로그인/파일 업로드 API 구현.  
* **2일차:** 지원 적합성 검토 로직(간단 키워드 매칭) 및 AI 코칭 API 연결.  
* **3일차:** 운영자 메모 및 서비스 통계 API 연동, 최종 시스템 테스트.

## **4. 템플릿 파일 업로드 API (2026-06-20 개선)**

### **새로운 엔드포인트**

#### **POST /api/admin/templates/<id>/upload**
- **목적:** PDF/WORD 파일 기반 이력서 템플릿 업로드
- **요청:** `multipart/form-data` (파일 필드명: `file`)
- **응답:**
  ```json
  {
    "success": true,
    "message": "파일이 업로드되었습니다.",
    "template": { ...템플릿 객체... }
  }
  ```
- **검증:**
  - 파일 타입: PDF(.pdf), WORD(.docx)만 허용
  - 파일명 안전화: `werkzeug.utils.secure_filename()` 사용
  - 파일명 규칙: `{timestamp}_{template_id}_{original_filename}`
  - 저장 경로: `uploads/templates/` 디렉토리
- **에러 처리:**
  - 지원하지 않는 파일: 400 에러 + "PDF 또는 WORD 파일만 업로드 가능합니다."
  - 파일 누락: 400 에러 + "파일이 업로드되지 않았습니다."

#### **GET /api/admin/templates/<id>/file**
- **목적:** 등록된 템플릿 파일 미리보기/다운로드
- **응답:** 파일 바이너리 (MIME 타입 자동 설정)
- **에러 처리:**
  - 파일 없음: 404 에러 + "파일을 찾을 수 없습니다."

### **모델 변경사항 (models.py)**
- **ResumeTemplate 테이블:**
  - `file_path` (String, 500): 업로드된 파일 경로
  - `file_type` (String, 10): 파일 타입 ('pdf' 또는 'docx')
  - `original_filename` (String, 255): 원본 파일명
  - `html_content`: nullable로 변경 (하위 호환성)

### **delete_template() 업데이트**
- 템플릿 삭제 시 연관 파일도 자동 삭제
- 파일 삭제 실패 시 로그 남기고 계속 진행

## **5. 프로필 관리 API (2026-06-20 추가)**

### 신규 엔드포인트
| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/auth/profile` | PUT | 이름/이메일 수정. Body: `{name, email, current_password}` |
| `/api/auth/change-password` | PUT | 비밀번호 변경. Body: `{current_password, new_password}` |
| `/api/auth/reset-password` | POST | 임시 비밀번호 발급. Body: `{email}` |
| `/api/auth/avatar` | POST | 프로필 이미지 업로드. `multipart/form-data`, 필드명: `avatar` |

### DB 마이그레이션 패턴
- `app.py`의 `init_db()` 내 `migrations` 리스트에 `ALTER TABLE` SQL 문자열 추가
- try/except로 감싸 중복 실행 시 무시 (컬럼이 이미 있으면 패스)
- User 모델 사용 전에 실행되어야 하므로 `db.create_all()` 직후에 위치

```python
migrations = [
    "ALTER TABLE user ADD COLUMN avatar_url VARCHAR(500)",
    # 새 컬럼 추가 시 여기에 append
]
for sql in migrations:
    try:
        db.session.execute(text(sql))
        db.session.commit()
    except Exception:
        db.session.rollback()
```

## **6. Gemini AI 연동 (2026-06-22 업데이트)**

### 패키지 변경
- **제거:** `google-generativeai` (공식 deprecated)
- **추가:** `google-genai` (`from google import genai`)

### coaching_routes.py 변경사항
- `_call_anthropic()` → `_call_gemini()` 대체
- 환경변수: `ANTHROPIC_API_KEY` → `GEMINI_API_KEY`
- 모델 fallback 순서: `gemini-2.0-flash` → `gemini-2.0-flash-lite` → `gemini-flash-latest`
- AI 호출 우선순위: OpenAI → Gemini → Mock

### 주의사항
- Free Tier Gemini 키는 `generate_content_free_tier_requests` 일별 한도 있음 (초과 시 429 에러)
- 429 발생 시 다음 모델로 자동 fallback, 모두 실패 시 Mock 응답 반환
- `GEMINI_API_KEY`는 Replit Secrets에 등록 완료 (2026-06-22)

## **7. 버그 수정 내역 (2026-06-24)**

### BUG-001: 이력서 목록 샘플 혼재 (HIGH) ✅
- **파일:** `resume_routes.py` — `list_resumes()`
- **원인:** 항상 샘플 3종 + 사용자 이력서를 합산 반환하여 사용자가 본인 이력서 구분 불가
- **수정:** 기본은 `user_id=현재사용자`인 이력서만 반환. 샘플이 필요한 페이지(예: select.html)는 `?include_samples=true` 파라미터 추가 사용

### BUG-002: 제출처 applied_date 저장 안됨 (MEDIUM) ✅
- **파일:** `models.py`, `resume_routes.py`, `app.py`
- **원인:** `JobApplication` 모델에 `applied_date` 컬럼 없어 POST/PUT 시 완전히 무시됨
- **수정:**
  - `models.py`: `applied_date = Column(String(20))` 추가
  - `app.py` `init_db()`: `ALTER TABLE job_application ADD COLUMN applied_date VARCHAR(20)` 마이그레이션 등록
  - `resume_routes.py`: create/update 라우트에서 `applied_date` 읽기·저장 반영

### BUG-003: 샘플 이력서 편집 에러 메시지 불명확 (LOW) ✅
- **파일:** `resume_routes.py` — `update_resume()`
- **원인:** `is_sample=True`인 경우 `user_id` 불일치 403만 반환 → 사용자에게 원인 불명확
- **수정:** `is_sample` 체크를 `user_id` 체크 앞에 추가. `{"error": "샘플 이력서는 편집할 수 없습니다"}` 403 명확히 반환

## **8. Replit 배포 환경 (2026-06-24)**

### 진입점 구조
- `main.py` (루트): `sys.path`에 `a4u-webapp` 추가 → `from app import app, init_db` → `init_db()` → `app.run(host='0.0.0.0', port=5000)`
- `a4u-webapp/app.py`: Flask 팩토리, Blueprint 등록, DB 초기화 함수 포함

### Replit 환경 설정
- Nix 모듈: `python-3.11` (3.12는 Replit Free Tier에서 미지원)
- 워크플로우: `python main.py`
- Secrets 등록 완료: `SESSION_SECRET`, `GEMINI_API_KEY`