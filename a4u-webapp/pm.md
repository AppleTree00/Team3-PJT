# **PROJECT\_MASTER.md: 이력서 AI 코칭 시스템 총괄 관리**

## **1\. 프로젝트 헌법**

**MVP 범위 통제:** 3일 시연을 위해 샘플 3종에 최적화합니다. 범위를 벗어나는 모든 기능은 **'업데이트 예정 메시지'**로 대체합니다.

## **2\. 3일 완성 로드맵 (시연 집중 모드)**

| 일자 | 중점 과제 | 산출물 |
| :---- | :---- | :---- |
| 1일차 | 백엔드 API 및 DB 스키마 | 샘플 기반 고정 스키마(SQLite) |
| 2일차 | 프론트 UI 및 AI 코칭 연동 | 샘플 3종 기반 AI 템플릿 적용 |
| 3일차 | QA 및 최종 시연 리허설 | 예외 처리 및 메시지 호출 정합성 |

## **3\. 에이전트별 핵심 지침**

* **UI (에이전트 A):** 레이아웃 2종 고정, 미구현 버튼 호출 시 사용자 안내 팝업 구현.  
* **Dev (에이전트 B):** 샘플 3종 기반 하드코딩 프롬프트 구성. 추가 데이터 요구 시 JSONB 필드 활용.  
* **QA (에이전트 C):** 샘플 외 예외 케이스(파일 형식, 미지원 기능) 호출 시 에러 메시지 확인.

## **4\. 리스크 및 대응**

구현 불가능한 고도화 기능(업종별 마크다운 업로드 등)은 시연 시 **"시스템 안정화 후 오픈 예정"**으로 안내하여 사용자 기대치를 관리합니다.

## **4-1. 3일차 작업 지시 (시연 전 최종 보완 및 리허설)**

PM 확인 후 아래 작업 카드를 담당자에게 배정하고, 수정 완료 시 체크해 주세요.

### 🛠️ [Task 1] 파일 업로드 예외 처리 강화 (담당: 개발자)
* [ ] 이력서 파일 업로드 `input`에 `accept=".pdf,.docx,.doc"` 명시적 추가.
* [ ] 다른 확장자 유입 시, UI가 멈추지 않고 **커스텀 토스트 알림**을 띄우는 예외 처리(Try-Catch) 추가. (현재 `select.html`에 `showToast` 함수 누락)

### 🎨 [Task 2] 미구현 기능 알림 UX 개선 (담당: UI/UX & 개발자)
* [x] **(완료)** 기존의 윈도우 `alert()` 창 전체 제거.
* [x] **(완료)** 화면 우측 상단 혹은 하단에 깔끔하게 노출되는 **커스텀 토스트 알림(Toast)** 구현 및 적용.
* [x] **(완료)** "준비 중인 기능입니다. 데모 버전에서는 지원하지 않습니다." 문구 통일.

### ⚡ [Task 3] AI 코칭 응답 대기 로딩 처리 (담당: 개발자)
* [x] AI 코칭 요청 클릭 시 "AI 코칭 분석 중..." 로딩 스피너 작동 및 버튼 비활성화(`disabled`).
* [x] 응답 완료 또는 에러 발생 시 로딩 해제.

### 🎤 [Task 4] 최종 시연 리허설 준비 (담당: PM & QA)
* [ ] 3종 샘플 이력서 데이터가 정상적으로 입력되고, AI 피드백이 자연스럽게 연출되는지 최종 동선 체크.

## **5\. 기준**

작업 시 발견된 모든 작업진행을 별도 파일로 관리하고, 반영된 각 에이전트의 md 파일은 업데이트한다.

* 모든 역할자는 코드 작성 또는 수정 시 반드시 해당 파트의 역할 문서(`UI.md`, `dev.md`, `QA.md`, `PROGRESS.md` 등)를 갱신해야 합니다.
* 역할 문서 업데이트 사항은 PM에게 즉시 공유하여 작업 기록 누락을 방지합니다.
* 모든 코드 변경은 반드시 충분한 주석을 포함하여, 후속 고도화 및 기능 개선 시 코드 리뷰와 분석 시간을 절감해야 합니다.

## **5-3. Replit 마이그레이션 세션 작업 기록 (2026-06-24)**

> **도구 전환:** Gemini(VSCode) → Replit Agent 주력으로 전환. 복잡한 맥락 연속성이 필요한 작업은 Replit에서 처리.

### **[T017] Gemini 손상 복구 — admin.html 중복 렌더링**
- **역할 담당:** Dev 에이전트 (B)
- **파일:** `a4u-webapp/admin.html`
- **내용:** Gemini가 공통 파일 분리 작업 중 원본 코드를 삭제하지 않아 사이드바·헤더 각 2개씩 중복 렌더링 발생 → `{% include %}` 태그 이하 하드코딩 블록 전체 제거
- **검증:** `<aside>` 1개, `<header>` 1개, ADMIN CONSOLE 텍스트 1개 서버사이드 확인 ✅
- **관련 문서 업데이트:** `PROGRESS.md` T017, `QA.md` BUG-004, `dev.md` 섹션 9

### **[T018] Gemini 손상 복구 — _head.html tailwind.config 전체 복원**
- **역할 담당:** UI 에이전트 (A)
- **파일:** `a4u-webapp/_head.html`
- **내용:** Gemini가 `tailwind.config` 스크립트 블록 전체 삭제 → 전 페이지 커스텀 색상·폰트·여백 완전 미적용 상태. 팀원 Replit 참고 사이트(`pike.replit.dev`) 원본과 대조하여 전체 복원
- **복원 범위:** colors 51개 토큰, spacing 5종, fontSize 9종, fontFamily 9종, maxWidth, borderRadius, `.tonal-elevation` CSS
- **검증:** 복원 후 main.html 스크린샷 → 참고 사이트와 시각적 완전 일치 ✅
- **관련 문서 업데이트:** `PROGRESS.md` T018, `UI.md` 섹션 6, `report.md` 5.7

### **[T019] Replit 마이그레이션 확정 및 3개 사용자 경로 검증**
- **역할 담당:** Dev 에이전트 (B) + PM
- **내용:** 워크플로우 커맨드 정비, Flask `render_template` 전환, 3개 경로(일반/데모/관리자) 서버사이드 검증
- **관련 문서 업데이트:** `PROGRESS.md` T019, `dev.md` 섹션 8 업데이트

### **[T020] 관리자 데모 세션 어드민 전용 격리**
- **역할 담당:** Dev 에이전트 (B)
- **파일:** `app.py`, `resume_routes.py`
- **내용:**
  1. 관리자 세션 mode: `GENERAL` → `ADMIN` 으로 구분 (`resume_routes.py`)
  2. 관리자가 `/login.html` 재접근 시 `/admin`으로 리다이렉트 (`app.py` login_page)
  3. 관리자가 일반 사용자 페이지 접근 시 세션 삭제(강제 로그아웃) 제거 → 세션 유지 + `/admin` 리다이렉트 (`app.py` require_login)
- **세션 mode 체계 확정:** `ADMIN` / `DEMO` / `GENERAL`
- **검증:** 서버사이드 7개 시나리오 전건 PASS ✅
- **관련 문서 업데이트:** `PROGRESS.md` T020, `QA.md` 섹션 6

### **[T021] 데모 사용자 체험 모드 구현**
- **역할 담당:** Dev 에이전트 (B)
- **파일:** `resume_routes.py`, `app.py`, `login.html`, `demo_dashboard.html`
- **내용:**
  1. `/api/auth/login` 응답에 `mode` 필드 추가 → 프론트엔드가 DEMO 여부를 판별 가능 (`resume_routes.py`)
  2. `login.html` 로그인 성공 핸들러: `data.mode === 'DEMO'` 시 `demo_dashboard.html`로 리다이렉트 (3곳 수정)
  3. `app.py` require_login 미들웨어 확장:
     - `demo_dashboard.html` 미로그인 접근 → `/login.html` 차단
     - `demo_dashboard.html` 비데모 사용자 접근 → `/dashboard.html` 리다이렉트
     - `dashboard.html` 데모 사용자 접근 → `/demo_dashboard.html` 리다이렉트
  4. `demo_dashboard.html` JS: 하드코딩 '데모 사용자' → `/api/auth/me` API 호출로 실제 이름 로드
- **검증:** 서버사이드 7개 시나리오 전건 PASS ✅
  - `DEMO LOGIN` mode=DEMO 반환 / `demo_dashboard.html` 200 OK / `dashboard.html`→demo_dashboard 302
  - 미로그인→demo_dashboard 302 차단 / 어드민→demo_dashboard 302 차단
- **T021-b 추가 보완 (코드리뷰 반영):**
  - `common.js` — `injectDemoBanner()`, `showDemoBlockModal()`, `handleDemoBlock()` 공통 함수 추가
  - `resume_routes.py` — `update_resume`에 `@demo_mode_blocked` 누락분 추가
  - `demo_dashboard.html` — 기존 배너 `id="demo-mode-banner"` 부여 (중복 방지)

### **PM 통제 지침 (강화 적용)**
- **모든 작업은 착수 즉시** `pm.md` 섹션 5-3에 태스크 등록 후 진행
- **완료 즉시** `PROGRESS.md`, 해당 역할 MD(`UI.md` / `dev.md` / `QA.md`), `report.md` 동기 업데이트
- **Replit Agent가 작업 수행 시** 자동으로 관련 모든 문서에 히스토리 로그 기록 의무화
- **Gemini 사용 제한:** 단일 파일·단순 코드 조각에만 허용. 다중 파일·아키텍처·인증 로직은 Replit 전담

---

## **5-2. 최근 개선사항 (2026-06-22)**

### **이름 입력 필드 통합**
* **변경:** `select.html`, `builder.html`의 `성` + `이름` 2칸 → `이름` 단일 칸 통합
* **JS 동기화 완료:** `personalFirstName`/`personalLastName` 변수 및 localStorage 키(`firstName`/`lastName`) → `personalFullName` / `fullName` 으로 전면 교체
* **라벨:** "이름 (NAME)" → "이름"

### **Gemini AI 연동 완성**
* **배경:** 팀 실습 과정에서 확보된 키가 OpenAI + Gemini 이므로, 기존 Anthropic(Claude) 연동을 Gemini로 교체
* **패키지:** `google-generativeai`(deprecated) → `google-genai`
* **호출 우선순위:** OpenAI → Gemini → Mock
* **모델 fallback:** `gemini-2.0-flash` → `gemini-2.0-flash-lite` → `gemini-flash-latest` (쿼터 초과 시 자동 전환)
* **환경변수:** `GEMINI_API_KEY` Replit Secrets 등록 완료
* **주의:** Free Tier 키는 일별 쿼터 제한 — 내일 쿼터 리셋 후 또는 OpenAI 키 추가 시 즉시 실제 AI 응답 시연 가능

### **빌더 ↔ 미리보기 실시간 연동 (팀원 완성)**
* `builder.html` 입력 폼 수정 내용이 우측 미리보기 패널에 실시간 반영되도록 완성됨 (Git 병합 확인)

### **산출물 문서 업데이트 정책 시행**
* 이번 세션부터 모든 기능 변경 시 `PROGRESS.md`, `API_BACKEND.md`, `dev.md`, `UI_FRONTEND.md`, `pm.md` 동기화 의무화
* 기준: `pm.md` 섹션 5 준수

---

## **5-1. 최근 개선사항 (2026-06-20)**

### **어드민 템플릿 등록 시스템 개선**
* **변경 전:** HTML 코드를 직접 텍스트 영역에 입력하여 템플릿 등록
* **변경 후:** 
  - PDF/WORD 파일 직접 업로드 방식으로 전환
  - 등록된 템플릿에 대해 **미리보기 기능** 제공 (새 창에서 파일 표시)
  - **인쇄 기능** 추가 (브라우저 인쇄 다이얼로그 호출)

### **구현 상세**
1. **models.py 변경:**
   - `ResumeTemplate` 모델에 3개 필드 추가:
     - `file_path`: 업로드된 파일 경로
     - `file_type`: 파일 타입 ('pdf' 또는 'docx')
     - `original_filename`: 원본 파일명
   - `html_content` 필드는 호환성 유지를 위해 nullable로 변경

2. **admin_routes.py 변경:**
   - `/api/admin/templates/<id>/upload` (POST): PDF/WORD 파일 업로드 엔드포인트
   - `/api/admin/templates/<id>/file` (GET): 파일 미리보기/다운로드 엔드포인트
   - 파일 저장 위치: `uploads/templates/` 디렉토리
   - 파일명 규칙: `{timestamp}_{template_id}_{original_filename}`
   - 템플릿 삭제 시 연관 파일도 자동 삭제

3. **admin.html 변경:**
   - 템플릿 모달 UI: HTML 입력 필드 제거, PDF/WORD 파일 선택 UI 추가
   - 템플릿 그리드: 파일 등록 상태 표시, 미리보기/인쇄 버튼 추가
   - 새로운 JavaScript 함수:
     - `handleTemplateFileSelect()`: 파일 선택 처리
     - `previewTemplate()`: 새 창에서 파일 미리보기
     - `printTemplate()`: 인쇄 기능 (브라우저 인쇄 다이얼로그)
   - 기존 `saveTemplate()` 함수 업데이트: 파일 업로드 로직 포함

### **사용자 경험 개선**
- 직관적인 파일 드래그&드롭 UI
- 파일 선택 시 크기 정보 표시
- 파일 업로드 진행률 표시
- 등록된 파일 상태를 카드에 명확히 표시

### **사용자 프로필 이미지 업로드 기능 추가 및 QA 완료**
* **개요:** 사용자가 프로필 이미지를 업로드하고 즉각 반영되는 기능 구현.
* **QA 검증 결과 (PASS):**
  - **백엔드 (`/auth/avatar`):** 허용 확장자(PNG, JPG, GIF, WebP) 화이트리스트 검증 적용, 고유 UUID 기반 파일명 생성으로 파일 덮어쓰기 방지, 업로드 폴더 자동 생성(`os.makedirs`) 처리 완료.
  - **프론트엔드:** 프로필 이미지 변경 시 즉시 반영되도록 브라우저 캐시 우회(`?t=Date.now()`) 처리 완료.
  - **폼 동기화 (Real-time Sync):** 입력 폼(이름, 이메일, 전화번호) 수정 시 우측 미리보기 패널에 즉각 반영되도록 양방향 이벤트 리스너 연동 완료.
* **평가:** MVP 시연 기준에 완벽히 부합하며, 보안 및 예외 처리, 사용자 편의성이 안정적으로 적용되었습니다.

### **시스템 환경 및 보안 강화 (2026-06-20)**
* **환경변수 관리 표준화:** `.env.example` 제공 및 `app.py` 내 자동 로드 로직 구현을 통해 개발 환경 일관성 확보.
* **보안 가이드 적용:** `.gitignore`를 통한 DB 파일 및 민감 정보(API 키 등) 유출 방지 설정 완료.
* **간편 로그인 UI 확장:** `login.html` 내 네이버/카카오 로그인 영역 배치 및 미구현 안내 팝업 연결로 시연 준비 완료.

## **6\. 현재 전체 완성도 파악 및 내일(6.22) 중점 과제**
### **현재 진행 상황**
*   **백엔드 (1일차 목표):** `admin_routes.py`를 통해 확인 시, 사용자/템플릿/파일 관리를 위한 핵심 API 및 DB 연동이 완료되었습니다. AI 연동 부분은 환경변수 유무에 따라 실제 AI 호출 또는 Mock 응답을 반환하도록 구현되어 MVP 전략에 부합합니다.
*   **프론트엔드 (2일차 목표):** `main.html`, `dashboard.html` 등 다수의 화면이 구현되어 기본 UI 레이아웃이 완성되었습니다. `select.html`의 이력서 업로드 기능은 하드코딩된 샘플 데이터로 AI 분석 결과를 모방하여, '샘플 3종 기반 AI 템플릿 적용' 목표를 달성했습니다.

### **다음 단계: 3일차 - QA 및 최종 시연 리허설**
1.  **프론트엔드-백엔드 API 연동:** 현재 `admin.html`의 로그인 로직처럼 프론트엔드에 하드코딩된 기능들을 실제 백엔드 API(`admin_routes.py`)와 연동해야 합니다. 이는 '메시지 호출 정합성' 확보의 첫 단계입니다.
2.  **예외 처리 및 QA:** `UI.md`에 명시된 미구현 기능에 대한 `handleUnavailableFeature` 팝업 처리를 적용하고, `QA (에이전트 C)` 지침에 따라 샘플 외 파일 형식 업로드 등 예외 케이스를 테스트하여 시스템 안정성을 확보합니다.
3.  **시연 시나리오 확정:** 샘플 이력서 3종을 사용하여 전체 서비스 플로우(업로드 → AI 분석 결과 확인 → 이력서 빌더 적용)를 최종 점검하고, 데모 리허설을 진행합니다.

## **7\. 기능 중첩 및 누락에 대한 이력 관리 (3일차 QA)**

### **2026-06-19: QA 중 치명적 오류 발견 및 조치**

*   **발견된 문제:**
    *   `dashboard.html`과 `admin.html` 파일에서 Git 병합 충돌(merge conflict)이 발생하여, 사용자 대시보드와 관리자 대시보드의 코드가 서로 뒤섞여 있었습니다.
    *   **(현상 1)** `dashboard.html`에는 관리자 페이지용 통계(`total-users` 등)와 관련 로직이 포함되어 있었습니다.
    *   **(현상 2)** `admin.html`에는 불필요한 로그인 로직이 포함되어 있었고, 로그인 성공 시 사용자 대시보드(`dashboard.html`)로 잘못 이동시키는 오류가 있었습니다.
*   **영향:**
    *   사용자 및 관리자 페이지의 정상적인 기능 테스트가 불가능하며, 역할 분리가 깨져 시연에 치명적인 결함으로 작용합니다.
*   **조치 계획 (3일차 최우선 과제):**
    1.  **`dashboard.html` 수정:** 병합 충돌을 해결하고, 순수한 **사용자 대시보드** 기능만 남도록 코드를 수정했습니다. API 연동 지점을 `/api/stats`로 명확히 했습니다.
    2.  **`admin.html` 수정:** 병합 충돌을 해결하고, **관리자 대시보드** 기능만 남도록 코드를 수정했습니다. 잘못된 로그인 로직을 제거하고, 백엔드 API(`/api/admin/*`)와 정상적으로 연동되도록 구조를 바로잡았습니다.
*   **추후 업데이트 제안 (품질 향상):**
    *   **JavaScript 코드 분리:** 유지보수성 향상을 위해 각 HTML 파일에 포함된 `<script>` 로직을 별도의 `.js` 파일로 분리하는 작업을 제안합니다.
    *   **관리자 로그인 강화:** 현재는 백엔드 세션에 의존하고 있으나, 장기적으로는 별도의 관리자 전용 로그인 페이지를 구현하여 보안을 강화할 수 있습니다.

## **8. 역할별 누락 체크 및 반영**

### **UI 에이전트 (A)**
*   **확인:** `main.html`, `dashboard.html`, `builder.html`, `resume.html`, `select.html`, `timeline.html`, `profile-menu.html`, `admin.html`에 `handleUnavailableFeature()`가 적용되어 있습니다.
*   **누락 체크:**
    *   `dashboard.html`/`admin.html` 병합 충돌 잔여 코드 제거 여부를 재확인합니다.
    *   관리자용 로그인/대시보드 분리 검증을 완료합니다.
    *   입력 폼 제한 안내 메시지(샘플 필드 기준) 적용 여부를 확인합니다.
*   **반영:**
    *   UI 지침 문서는 `UI.md`를 기준으로 삼고, `UI_FRONTEND.md`는 아카이브로 대체합니다.

### **Dev 에이전트 (B)**
*   **확인:** `resume_routes.py`, `coaching_routes.py`, `admin_routes.py`, `models.py`가 핵심 API 및 DB/AI 코칭 요구사항을 커버하고 있습니다.
*   **누락 체크:**
    *   `admin_routes.py`와 `admin.html`의 실제 연동 및 세션 기반 관리자 권한 검증을 확인합니다.
    *   AI 호출 환경변수가 없을 때 Mock 응답이 정상 동작하는지 재확인합니다.
    *   `API_BACKEND.md` 문서와 실제 구현 간 일치 여부를 검증합니다.
*   **반영:**
    *   백엔드 지침 문서는 `dev.md`를 기준으로 삼고, `API_BACKEND.md`는 아카이브로 대체합니다.

### **QA 에이전트 (C)**
*   **확인:** `QA.md`에서 10/10 PASS 결과가 보고되었습니다.
*   **누락 체크:**
    *   관리자 흐름, 세션 만료/비정상 요청, 크로스 브라우저 점검을 추가로 확인합니다.
    *   `QA.md`를 기준으로 문서 통일을 유지하고, `QA_TESTING.md`는 아카이브로 대체합니다.
    *   `report.md`의 QA 요약과 실제 테스트 결과가 일치하는지 검증합니다.
*   **반영:**
    *   추가 테스트 시나리오는 `QA_TESTING.md`에 누적하여 최종 시연 점검 리스트로 유지합니다.

### **PM 보고서 검토 역할**
*   **보고서 일관성 점검:** `report.md`를 PM 핵심 산출물로 보고, `pm.md`, `UI.md`, `dev.md`, `QA.md`, `PROGRESS.md` 간 일관성을 검사합니다.
*   **시연용 요약 반영:** `report.md`에 최신 QA 통과 현황, 병합 충돌 해결 사례, 미구현 기능 팝업 처리 상태를 반영하도록 합니다.
*   **문서 동기화:** 보고서와 진행 현황 문서가 상호 보완되도록 정리합니다.

## **9. 4인 체제 AI-Human 동시 협업 및 충돌 방지 가이드**

4명의 휴먼(PM, 기획, 아키텍처, DB)이 각각 AI 에이전트를 활용하여 동시 다발적으로 코드를 생성할 때 발생하는 Git 병합 충돌 및 사이드 이펙트를 방어하기 위한 '파일 및 도메인 분절 전략'입니다.

### **1) 철저한 파일/도메인 단위 독점권 부여 (분절화)**
각 역할자는 본인에게 할당된 '목표 파일' 외에는 AI에게 수정을 지시할 수 없습니다.
*   **아키텍처 전문가:** 백엔드 코어, API 라우팅, 서버 설정 독점.
    *   `app.py`, `*_routes.py` (예: `main_routes.py`, `resume_routes.py`)
*   **DB 전문가:** 데이터베이스 스키마, 쿼리, 시연용 데이터 로더 독점.
    *   `models.py`, `a4u.db`, 더미 데이터 스크립트
*   **기획/UI 담당:** 프론트엔드 레이아웃, 화면 로직, 스타일 독점.
    *   `templates/*.html` 전체, 클라이언트 사이드 JS
*   **프로젝트 리더 (PM):** 전체 통합, 테스트, 그리고 프로젝트 문서 독점.
    *   `pm.md`, `report.md`, `README.md`, 병합(Merge) 관리

### **2) AI 프롬프팅 통제 규칙**
*   AI에게 지시를 내릴 때 반드시 **수정 허용 파일 범위를 명시**해야 합니다.
    *   *(예: DB 전문가의 지시)* "이력서 더미 데이터를 추가해줘. 단, `models.py` 파일만 수정하고 html 파일이나 라우터 파일은 절대 건드리지 마."

## **[T023] dashboard.html 샘플 데이터 노출 긴급 수정 (2026-06-25)**

> **최고 심각도 오류:** 일반사용자 dashboard.html에 Naver·Kakao·Toss·Coupang 하드코딩 샘플 데이터가 노출되고 있었음. 사용자 본인 데이터와 무관하게 동일한 내용이 항상 표시되는 치명적 UX 오류.

### 수정 항목

| 항목 | 파일 | 이전 상태 | 수정 후 |
|---|---|---|---|
| 지원현황 칸반 | `dashboard.html` | Naver·Kakao·Toss·Coupang 하드코딩 | `/api/applications` API 연동, 빈 상태 안내 |
| 면접 일정 | `dashboard.html` | "Kakao 1차 면접", "Toss 2차 면접" 하드코딩 | interview 상태 지원 항목 API 연동 |
| 내 이력서 목록 | `dashboard.html` | 없음 (미표시) | `/api/resumes` API 연동, is_sample=false 필터 |
| 통계 수치 | `dashboard.html` | console.log만 출력, 화면 미표시 | 이력서 수·지원 건수 실표시 |
| 페이지 제목 | `dashboard.html` | "관리자 대시보드" (오타) | "대시보드" |
| 네비게이션 레이블 | `_navbar.html` | "제출 관리" (select.html과 불일치) | "이력서 등록" |

### 네비게이션 메뉴 최종 구조 (2026-06-25 재정의)
| 메뉴 | 경로 | 비고 |
|---|---|---|
| 로고(a4u) | `main.html` | 홈 |
| 이력서 등록 | `select.html` | 신규 이력서 작성 시작 |
| 이력서 관리 | `resume.html` | 로그인 직후 랜딩 페이지 (B안) |
| 제출관리 | `dashboard.html` | 지원현황 칸반 + 면접일정만 표시 |
- 커리어관리(`timeline.html`) 삭제 — 화면 미구현, `/timeline.html` 접근 시 `/resume.html`로 리다이렉트
- 데모 사용자 로그인 후 랜딩: `demo_dashboard.html` (기존 유지)

### 코드 관리 원칙 (앞으로 전 작업에 적용)
- **코드 삭제 금지**: 기존 코드는 삭제하지 않고 HTML 주석(`<!-- [이전 코드] ... -->`)으로 처리
- **신규 코드만 추가**: 변경 사유와 날짜를 `<!-- [수정 YYYY-MM-DD] 사유 -->` 형태로 명시
- **샘플 데이터 격리 규칙:**
  - `dashboard.html`: 절대 샘플 데이터 미포함. API 호출 시 `include_samples` 파라미터 사용 금지. 프론트에서도 `is_sample=false` 필터 적용
  - `demo_dashboard.html`: `include_samples=true` 사용 가능, 데모 시나리오 전용
  - `resume_routes.py` `/api/resumes`: 파라미터 없이 호출 시 본인 이력서만 반환 (기존 정상 구현)

## **[T022] 3-계정 시연 시나리오 공식 정의 (2026-06-25)**

> 데모 발표 시 아래 3가지 계정 역할로 기능을 구분 시연합니다.

### 계정 1: 일반사용자 (일반 계정)
- **로그인:** 직접 회원가입 또는 기존 계정 (예: demo-general@a4u.com)
- **허용 기능 (Full CRUD):**
  - 이력서 새로 작성, 수정, 삭제
  - AI 코칭 요청 및 결과 확인
  - 파일(PDF/DOCX) 업로드 → AI 코칭 편집 화면 진입
  - 프로필 수정 (이름, 비밀번호, 아바타)
  - 계정 삭제 (회원 탈퇴)
  - 지원 현황 관리 (칸반)
- **진입 화면:** `dashboard.html`

### 계정 2: 사용자데모 (데모 계정)
- **로그인:** demo@a4u.com / demo1234
- **허용 기능 (Read-Only 체험):**
  - 샘플 이력서 3종 읽기
  - "이력서 보완하기" → `builder.html` (샘플 데이터 미리채움, 편집 미리보기 가능)
  - AI 코칭 응답 확인 (읽기 전용)
  - 프로필 조회
- **차단 기능 (메시지 출력):**
  - 새 이력서 작성 → 토스트 메시지 출력, 이동 차단 ✅ (GAP-001 수정 완료)
  - 이력서 저장 → API 403 + 토스트 메시지
  - 프로필 수정/삭제 → 클라이언트 차단
  - 파일 업로드 → API 403
- **진입 화면:** `demo_dashboard.html`

### 계정 3: 관리자데모 (관리자 데모 계정)
- **로그인:** `/api/auth/admin-demo-login` (버튼 클릭, 비밀번호 없음)
- **허용 기능:**
  - 관리자 대시보드(`admin.html`) 전체 조회
  - 사용자 목록 조회
  - 템플릿 목록 조회, 기존 템플릿 **편집** ✅ (GAP-003/004 수정 완료)
- **차단 기능 (메시지 출력):**
  - 새 템플릿 추가 → `blockIfAdminDemo()` 토스트 출력
  - 사용자 계정 수정/삭제 → `blockIfAdminDemo()` 토스트 출력
- **페이지 이탈 규칙:** 관리자 페이지 외 이동 시 세션 자동 정리
- **진입 화면:** `admin.html`

---

## **[T024] 이력서 작성 페이지 대시보드 돌아가기 버튼 오류 수정 (2026-06-25)**

### 원인
| 파일 | 증상 | 원인 |
|---|---|---|
| `select.html` | 버튼 클릭 시 404 오류 | `onclick="/dashboard"` — `.html` 누락 |
| `select.html` | 저장 후 리다이렉트 404 | `window.location.href='/dashboard'` — 동일 |
| `builder.html` | 버튼 클릭 무반응 | `onclick` 속성 자체 누락 |

서버 로그: `GET /dashboard HTTP/1.1 → 404`

### 수정 내용
- 세 곳 모두 `/dashboard.html`로 수정
- DEMO 사용자는 서버(app.py 129행)가 `/demo_dashboard.html`로 자동 리다이렉트
- 초기·일반 사용자는 `/dashboard.html` 정상 진입

### 사용자별 동작
| 사용자 유형 | 이동 경로 |
|---|---|
| 초기 사용자 (데이터 없음) | `/dashboard.html` |
| 일반 사용자 (데이터 있음) | `/dashboard.html` |
| DEMO 사용자 | `/dashboard.html` → 서버 리다이렉트 → `/demo_dashboard.html` |

---

### **3) 타임박스(Time-box) 기반 커밋 및 병합 동기화**
*   **개인 브랜치 작업:** 4명 모두 `main` 브랜치가 아닌 개인 브랜치(`feat/db`, `feat/arch` 등)에서 AI와 작업합니다.
*   **일 2회 정기 병합:** 오후 1시, 오후 5시 등 정해진 시간에만 작업을 멈추고 PM 주도하에 `main`으로 병합(Pull Request)하여 충돌을 일괄 해결합니다. 이 시간 외에는 절대 `main` 브랜치에 푸시하지 않습니다.

---

## **[DEFERRED] 추후 작업 목록 (시연 후 고도화)**

> 내일(2026-06-26) 시연을 위해 즉시 조치하지 않고 추후 작업으로 보류된 항목입니다.

### **[D001] 이력서 항목 필드 정합성 통일 (우선순위: 높음)**

- **등록 일자:** 2026-06-25
- **배경:** 업로드된 이력서 파일에서 파싱되는 데이터, 입력 폼 필드, 미리보기 출력 항목이 섹션별로 불일치가 확인됨.
- **해당 섹션:**
  - 학력 (Education): 파싱 필드명 vs 폼 입력 vs 미리보기 출력 불일치
  - 주소 (Address/Location): 단일 필드로 파싱되나 세부 입력 폼 미구현
  - 자격증 (Certifications): AI 파싱 결과에 포함되나 입력 폼 섹션 없음
  - 활동이력 (Activities): 파싱·입력·출력 항목 제각각
  - 교육이수 (Training/Courses): 별도 섹션 없이 기타로 처리됨
- **작업 내용 (추후):**
  1. AI 파싱 프롬프트에 각 섹션별 필드명 표준화 (snake_case 통일)
  2. `select.html` / `builder.html` 에 학력·자격증·활동이력·교육이수 입력 섹션 추가
  3. `_renderExpToPreview` 방식으로 각 섹션 미리보기 실시간 동기화 구현
  4. `resume_routes.py` — `get_experience()` 패턴으로 각 섹션 getter 추가
  5. `_export_resume_html()` — 신규 섹션 HTML 출력 반영
- **담당:** Dev(B) + UI(A) 협업
- **예상 공수:** 1~2일

### **[D002] 기술 섹션 이후 '다음 섹션' 버튼 제거 (완료)**
- **등록 일자:** 2026-06-25
- **상태:** ✅ 완료 — `select.html` `switchTab()` 함수에서 마지막 섹션(기술) 진입 시 `btnNextSection` 자동 숨김 처리
