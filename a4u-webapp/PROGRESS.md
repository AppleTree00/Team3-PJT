# 작업 진행 현황 (자동 관리 파일)

> 최종 업데이트: 2026-06-20

## 완료된 작업

### [T001] DB 스키마 확장 ✅
- `models.py` — Resume, JobApplication 모델 추가 (샘플 3종 고정 스키마 + extra_json 확장 필드)
- 샘플 이력서 3종 시드: IT 개발자형(김개발), 경영 관리자형(이매니저), 일반 범용형(박지원)
- 데모 계정 추가: demo@a4u.com / demo1234

### [T002] 핵심 API 엔드포인트 ✅
- `resume_routes.py` 신규 생성 (Blueprint: /api)
  - POST /api/auth/login — 이메일/비밀번호 세션 로그인
  - GET  /api/auth/me — 현재 사용자 조회
  - POST /api/auth/logout — 로그아웃
  - POST /api/auth/register — 신규 가입
  - GET  /api/resumes — 이력서 목록 (샘플 + 본인)
  - POST /api/resumes — 이력서 생성
  - GET  /api/resumes/<id> — 이력서 조회
  - PUT  /api/resumes/<id> — 이력서 수정 (인증 필요)
  - DELETE /api/resumes/<id> — 이력서 삭제 (인증 필요)
  - GET  /api/applications — 제출 목록
  - POST /api/applications — 제출 생성
  - PUT  /api/applications/<id> — 제출 수정
  - GET  /api/stats — 대시보드 통계

### [T003] AI 코칭 API ✅
- `coaching_routes.py` 신규 생성
  - POST /api/coaching — Few-shot 3종 프롬프트 기반 코칭
  - GET  /api/coaching/samples — 지원 가능한 샘플 타입 목록
  - OpenAI(gpt-4o-mini) → Anthropic(claude-3-haiku) → Mock 순서로 Fallback
  - 미지원 타입: 422 + "고도화 단계" 안내 메시지

### [T004] 프론트엔드 팝업 + API 연동 ✅
- 전체 6개 페이지에 `handleUnavailableFeature()` 적용:
  - main.html, dashboard.html, builder.html, resume.html, timeline.html, profile-menu.html
- dashboard.html: /api/stats 실시간 연동, 버튼별 동작 연결
- builder.html: /api/resumes 저장 연동, /api/coaching AI 코칭 연동
- profile-menu.html: 로그아웃 → /api/auth/logout, 나머지 메뉴 팝업
- resume.html: /api/resumes 목록 연동, 인쇄 버튼 동작

### [T005] QA 점검 ✅ (10/10 PASS)
| 시나리오 | 결과 |
|----------|------|
| 지원하지 않는 파일 형식 업로드 → 400 | PASS |
| PDF 파일 업로드 → 200 | PASS |
| 인증 없이 이력서 수정 → 401 | PASS |
| AI 코칭 샘플 3종(it/management/general) → 200 | PASS |
| AI 코칭 미지원 타입 → 422 + 안내 메시지 | PASS |
| 통계 API → 200 | PASS |
| 이력서 목록 샘플 3종 확인 | PASS |
| demo 로그인 → 200 | PASS |
| 잘못된 비밀번호 → 401 | PASS |
| 코칭 빈 텍스트 → 400 | PASS |

### [T006] 어드민 템플릿 관리 시스템 ✅ (2026-06-20)
- **HTML 텍스트 입력 → PDF/WORD 파일 업로드 방식으로 전환**
- `models.py` ResumeTemplate 모델 확장:
  - `file_path`: 업로드된 파일 경로
  - `file_type`: 파일 타입 ('pdf' 또는 'docx')
  - `original_filename`: 원본 파일명
  - `html_content`: nullable 변경 (호환성 유지)
- `admin_routes.py` 새로운 엔드포인트:
  - POST `/api/admin/templates/<id>/upload` — PDF/WORD 파일 업로드
  - GET `/api/admin/templates/<id>/file` — 파일 미리보기/다운로드
  - DELETE 로직 개선: 파일 자동 삭제
- `admin.html` UI/UX 개선:
  - 파일 선택 UI (드래그&드롭 지원)
  - **미리보기 기능** — 새 창에서 파일 표시
  - **인쇄 기능** — 브라우저 인쇄 다이얼로그
  - 파일 업로드 상태 표시 및 피드백
  - JavaScript 함수 추가:
    - `handleTemplateFileSelect()`: 파일 검증 및 표시
    - `previewTemplate()`: 미리보기
    - `printTemplate()`: 인쇄
  - `saveTemplate()` 업데이트: 파일 업로드 로직 통합

### [T007] Git 환경 설정 (.gitignore) ✅ (2026-06-20)
- 루트 폴더에 `.gitignore` 파일 생성 및 설정 적용 (.vs, .vscode, *.db, *.sqlite, *.sqlite3, __pycache__, *.pyc 제외)

## 미구현 / 업데이트 예정
- Google OAuth 로그인 (현재: 이메일/비밀번호 세션 방식)
- 이력서 PDF 다운로드 (현재: 팝업 안내)
- 드래그앤드롭 캔반 보드 (현재: UI만 표시)
- 커리어 타임라인 일정 추가 (현재: 팝업 안내)
- 포트폴리오/경력관리 메뉴 (현재: 팝업 안내)

## 계정 정보
| 계정 | 이메일 | 비밀번호 | 권한 |
|------|--------|----------|------|
| 관리자 | admin@a4u.com | admin1234 | 어드민 |
| 데모 | demo@a4u.com | demo1234 | 일반 |

## 주요 파일
| 파일 | 역할 |
|------|------|
| app.py | Flask 앱 진입점, DB 초기화, 블루프린트 등록 |
| models.py | SQLAlchemy 모델 (User, Resume, JobApplication, ResumeTemplate, UploadedFile, SchemaMigration) |
| resume_routes.py | 인증 + 이력서 CRUD + 통계 API |
| coaching_routes.py | AI 코칭 API (Few-shot 3종) |
| admin_routes.py | 어드민 대시보드 API |
| admin.html | 어드민 대시보드 UI |
