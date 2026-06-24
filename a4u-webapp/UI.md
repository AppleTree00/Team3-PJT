# UI.md: 프론트엔드 에이전트 작업 지침

## 1. 목표 및 역할 범위

* **UI/UX 디자인:** 샘플 이력서 3종에 최적화된 2종의 고정 템플릿 UI 구현 및 시각적 일관성 유지.
* **퍼블리싱 (Publishing):** 시연 환경에 최적화된 마크업, 웹 표준 준수, 시니어 사용자를 위한 웹 접근성(가독성 등) 고려.
* **인터랙션 및 스크립트:** 애니메이션(스크립트 효과), DOM 조작, 사용자 인터랙션 이벤트 처리 등 프론트엔드 동적 기능 구현.

## **2\. 주요 기능 및 구현 규칙**

* **UI 템플릿:** 기획된 2종 레이아웃을 HTML/CSS(Tailwind)로 고정 구현.  
* **입력 폼 제한:** 샘플 데이터의 필드와 일치하지 않는 입력 시 "사용 가능한 필드는 \[필드명\]입니다."라고 안내.  
* **미구현 기능 호출:** 모든 미구현 버튼/기능(예: Google, 네이버, 카카오 간편로그인 등)에 대해 다음 함수를 호출하여 팝업 처리.  
  `function handleUnavailableFeature() {`  
      `alert("현재 이 기능은 고도화 단계에 있습니다. 업데이트 이후 사용 가능하니 잠시만 기다려주세요.");`  
  `}`

## **3\. 3일차 마일스톤**

* **1일차:** 로그인 화면 및 기본 이력서 작성 폼 구조 설계.  
* **2일차:** 이력서/지원처 미리보기 화면 구현, AI 코칭 대화창 레이아웃 배치.  
* **3일차:** 전체 페이지 인터랙션 점검 및 미구현 기능 팝업 연결 확인.

## **4. 어드민 템플릿 관리 시스템 (2026-06-20 개선)**

### **개요**
어드민 콘솔에서 PDF/WORD 파일 기반 이력서 템플릿 등록 및 관리 기능 제공.

### **기능**
1. **템플릿 등록:**
   - 템플릿 이름, 카테고리, 설명 입력
   - PDF 또는 WORD(.docx) 파일 업로드
   - 썸네일 이미지 URL 지정 (선택사항)
   - 템플릿 활성화/비활성화 토글

2. **템플릿 관리:**
   - 등록된 템플릿 목록 표시 (카테고리별/활성 상태 표시)
   - **미리보기:** 새 창에서 PDF/WORD 파일 표시
   - **인쇄:** 브라우저 인쇄 다이얼로그를 통한 직접 인쇄
   - **수정:** 템플릿 정보 변경 및 파일 재업로드
   - **삭제:** 템플릿 및 연관 파일 삭제

### **UI 컴포넌트**
- **템플릿 모달:** 파일 선택 UI (드래그&드롭 지원)
- **템플릿 카드:** 파일 등록 상태 배지, 미리보기/인쇄/수정/삭제 버튼
- **파일 선택 피드백:** 선택된 파일명 및 크기 표시

### **기술 스택**
- **프론트엔드:** Tailwind CSS, Vanilla JavaScript (FormData API)
- **파일 업로드:** FormData를 통한 multipart/form-data 전송
- **미리보기:** `window.open()`을 이용한 새 창 열기
- **인쇄:** JavaScript `window.print()` API

---

## **5. 3일차 UI 구현 완료 항목 (2026-06-22~24)**

### 5.1 이력서 빌더 UX 개선
- **진행 바 (Progress Bar):** 빌더 상단에 전체 작성률을 시각적으로 표시
- **브레드크럼 (Breadcrumbs):** '인적사항 > 경력사항 > 보유기술 > 자기소개서' 단계 이동 UI
- **작성률 로직:** 각 섹션 필드 입력 여부 감지 → 진행 바 실시간 업데이트
- **임시 저장:** `localStorage` 활용, 페이지 이탈 후 복원
- **새 이력서 빈 폼:** `?new=true` 파라미터 감지 시 localStorage 초기화 + 폼 공백 상태

### 5.2 이름 필드 단일화
- `성` + `이름` 2칸 → `이름` 단일 입력 (`id="personalFullName"`)
- localStorage 키: `firstName`/`lastName` → `fullName`

### 5.3 Toast 알림으로 alert() 교체 (Task 2 완료)
- 기존 `window.alert()` 전체 제거
- 화면 우측 상단 커스텀 토스트 알림 구현
- 통일 문구: "준비 중인 기능입니다. 데모 버전에서는 지원하지 않습니다."

### 5.4 AI 코칭 로딩 UX (Task 3 완료)
- AI 코칭 버튼 클릭 시 "AI 코칭 분석 중..." 스피너 표시 + 버튼 `disabled`
- 응답 완료/에러 시 로딩 상태 해제

### 5.5 파일 업로드 예외 처리 (Task 1 완료)
- `select.html` `<input accept=".pdf,.docx,.doc">` 명시적 추가
- Try-Catch 기반 예외 처리: UI 멈춤 없이 에러 메시지 노출

---

## **6. Gemini 손상 복구 — tailwind.config 복원 (2026-06-24)**

### 6.1 손상 내용
- **파일:** `a4u-webapp/_head.html`
- **Gemini가 한 것:** `<script id="tailwind-config">` 블록 전체 삭제
- **영향:** `_head.html`은 `{% include '_head.html' %}`로 모든 HTML 페이지에 공유됨. 삭제로 인해 전 페이지의 커스텀 Tailwind 클래스가 무효화:
  - 색상 클래스: `bg-primary`, `text-on-surface`, `bg-surface-container-lowest` 등 51개 토큰 전부
  - 폰트 크기: `font-headline-lg`, `text-display-lg`, `text-label-md` 등
  - 여백: `max-w-max-width`, `px-margin-desktop`, `gap-gutter` 등
  - 외관 컴포넌트: `.tonal-elevation` (카드 그림자)

### 6.2 복원 내용
복원된 `tailwind.config` 구성 요소:

| 카테고리 | 항목 수 | 주요 예시 |
|---|---|---|
| colors | 51개 | `primary: #3525cd`, `on-surface: #111c2d`, `surface-container-lowest: #ffffff` |
| spacing | 5개 | `margin-desktop: 40px`, `gutter: 24px`, `max-width: 1280px` |
| fontSize | 9개 | `display-lg: 48px/700`, `headline-lg: 32px/600`, `label-md: 14px/600` |
| fontFamily | 9개 | 모두 Inter |
| maxWidth | 1개 | `max-width: 1280px` |
| borderRadius | 4개 | DEFAULT~full |
| 추가 CSS | 1개 | `.tonal-elevation { box-shadow: 0px 4px 12px ... }` |

### 6.3 복원 검증
- **방법:** 팀원 Replit 원본 사이트(`pike.replit.dev/main.html`)를 curl로 접근해 `tailwind.config` 블록 추출 → 대조 후 복원
- **시각 확인:** 복원 전/후 main.html 스크린샷 비교 — 참고 사이트와 완전 일치 ✅
- **주의사항:** `_head.html` 수정은 반드시 Replit Agent에서만. 전 페이지에 즉시 영향을 미치는 전역 파일이므로 Gemini 사용 금지