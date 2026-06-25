# QA 결과 보고서: 3일 시연용 시나리오 검증 및 개선안

**수신:** PM (Project Manager)  
**발신:** QA 에이전트  
**일자:** 3일차 마일스톤 중 2일차 완료 시점  
**상태:** **부분 조건부 통과 (Conditional Pass)** - *주요 예외 처리 및 UX 개선 필요*

---

## 1. 종합 검증 결과 요약

| 검증 영역 | 테스트 케이스 | 결과 | 비고 |
| :--- | :--- | :--- | :--- |
| **시나리오 테스트** | 3종 샘플 데이터 입력 및 흐름 검증 | **PASS** | 작성 -> AI 코칭 -> 미리보기 정상 동작 |
| **예외 처리 방어** | 미구현 기능 클릭 시 안내 처리 | **WARN** | 브라우저 기본 `alert` 노출로 시연 UI 품질 저하 |
| **파일 검증** | PDF/WORD 외 타 확장자 업로드 시 방어 | **FAIL** | 타 파일 업로드 시 콘솔 에러 발생 및 UI 멈춤 현상 관찰 |
| **AI 코칭 답변** | 피드백 일관성 및 UX 응답 대기 처리 | **WARN** | 로딩 상태 표시 미흡으로 중복 클릭 위험 존재 |

---

## 2. 발견된 주요 결함 (Defects)

### 🚨 [결함 1] PDF/WORD 외 다른 파일 업로드 시 시스템 크래시 (Critical)
* **현상:** `.png`, `.txt` 등 허용되지 않은 파일 업로드 시, 에러 메시지 없이 화면이 멈춤.
* **개선안:** `accept=".pdf,.doc,.docx"` 속성 적용 및 예외 처리 모달 추가.

### ⚠️ [결함 2] 미구현 기능 호출 시 브라우저 기본 Alert 노출 (Major)
* **현상:** "템플릿 변경", "이력서 다운로드" 등 미구현 버튼 클릭 시 투박한 브라우저 `window.alert()` 노출.
* **개선안:** 커스텀 토스트(Toast) 알림 UI로 대체.

### ⚠️ [결함 3] AI 코칭 생성 중 로딩 상태 표시(Spinner) 미흡 (Minor)
* **현상:** AI 응답 대기 시간(3~5초) 동안 로딩 상태가 보이지 않아 중복 클릭 유발.
* **개선안:** 로딩 스피너 활성화 및 버튼 `disabled` 처리.

---

## [T022] 3-계정 시연 시나리오 갭 분석 보고 (2026-06-25)

> **분석 대상:** 일반사용자 / 사용자데모 / 관리자데모 3계정 시나리오 전체  
> **기준 문서:** `pm.md` T022 시나리오 스펙

### 분석 계정별 진입/차단 스펙

| 계정 | 로그인 | 진입 화면 | 핵심 제약 |
|---|---|---|---|
| 일반사용자 | 회원가입/일반 계정 | `dashboard.html` | Full CRUD 가능 |
| 사용자데모 | demo@a4u.com / demo1234 | `demo_dashboard.html` | 새 이력서 작성 차단, 저장 차단 |
| 관리자데모 | admin-demo-login 버튼 | `admin.html` | 템플릿 추가·사용자 수정/삭제 차단, 편집 허용 |

### 식별된 갭 및 수정 현황

| 갭 ID | 심각도 | 현상 | 조치 내용 | 상태 |
|---|---|---|---|---|
| **GAP-001** | HIGH | `demo_dashboard.html` "새 이력서 작성" → `<a href="builder.html">` 이동 (차단 없음) | `<button onclick="blockNewResume()">` 변경 + `blockNewResume()` 함수 추가 | ✅ 수정 완료 |
| **GAP-002** | — | "이력서 보완하기" → 빈 빌더 우려 | `builder.html` 자체에 샘플 데이터 하드코딩 → 정상 동작 확인 | ℹ️ 수정 불필요 |
| **GAP-003** | MEDIUM | `admin.html` `openTemplateModal()` — 기존 템플릿 편집도 `blockIfAdminDemo()` 차단 | `if (!t && blockIfAdminDemo()) return;` 조건 분리 | ✅ 수정 완료 |
| **GAP-004** | MEDIUM | `admin_routes.py` `update_template` — `@demo_mode_blocked` 불필요 적용 | 데코레이터 제거 | ✅ 수정 완료 |

### 기존 정상 구현 확인 항목 (13건)

| # | 항목 | 위치 | 결과 |
|---|---|---|---|
| 1 | 사용자데모 이력서 저장 서버 차단 | `resume_routes.py` `@demo_mode_blocked` | ✅ |
| 2 | 사용자데모 이력서 생성 서버 차단 | `resume_routes.py` `@demo_mode_blocked` | ✅ |
| 3 | 사용자데모 파일 업로드 서버 차단 | `resume_routes.py` `@demo_mode_blocked` | ✅ |
| 4 | 사용자데모 프로필 수정 클라이언트 차단 | `profile-menu.html` `blockIfDemo()` L399·L434·L514 | ✅ |
| 5 | 관리자데모 사용자 생성 서버 차단 | `admin_routes.py` `create_user` `@demo_mode_blocked` | ✅ |
| 6 | 관리자데모 사용자 수정 서버 차단 | `admin_routes.py` `update_user` `@demo_mode_blocked` | ✅ |
| 7 | 관리자데모 사용자 삭제 서버 차단 | `admin_routes.py` `delete_user` `@demo_mode_blocked` | ✅ |
| 8 | 관리자데모 사용자 수정/삭제 클라이언트 차단 | `admin.html` `blockIfAdminDemo()` in `saveUser·deleteUser` | ✅ |
| 9 | 관리자데모 템플릿 추가 서버 차단 | `admin_routes.py` `create_template` `@demo_mode_blocked` | ✅ |
| 10 | 관리자데모 템플릿 삭제 서버 차단 | `admin_routes.py` `delete_template` `@demo_mode_blocked` | ✅ |
| 11 | 사용자데모 배너 표시 | `demo_dashboard.html` + `common.js` `injectDemoBanner` | ✅ |
| 12 | 403 응답 시 회원가입 유도 모달 | `common.js` `handleDemoBlock()` | ✅ |
| 13 | 일반사용자 이력서 Full CRUD | `resume_routes.py` 세션 인증 기반 | ✅ |

### 통합 테스트 체크리스트 (시연 전 수동 확인)

**계정 1 — 일반사용자**
- [ ] 회원가입 → 로그인 → `dashboard.html` 진입
- [ ] 이력서 새로 작성 → 저장 → 목록 표시
- [ ] 기존 이력서 수정 → 저장
- [ ] AI 코칭 요청 → 응답 표시
- [ ] 이력서 삭제
- [ ] 프로필 수정 (이름·비밀번호·아바타)
- [ ] 로그아웃

**계정 2 — 사용자데모 (demo@a4u.com / demo1234)**
- [ ] 로그인 → `demo_dashboard.html` + 데모 배너 표시
- [ ] "새 이력서 작성" 클릭 → 이동 차단 + 토스트 ← GAP-001 검증
- [ ] "이력서 보완하기" 클릭 → 샘플 빌더 진입
- [ ] 빌더 필드 수정 → 미리보기 실시간 연동
- [ ] 빌더 저장 시도 → 차단 메시지
- [ ] 샘플 이력서 3종 카드 표시
- [ ] 프로필 수정 시도 → 차단 메시지

**계정 3 — 관리자데모**
- [ ] `admin-demo-login` → `admin.html` 진입
- [ ] 기존 템플릿 편집 버튼 → 모달 열림 (차단 안 됨) ← GAP-003 검증
- [ ] 기존 템플릿 편집 저장 → 성공 ← GAP-004 검증
- [ ] 새 템플릿 추가 → 차단 메시지 (편집과 구분)
- [ ] 사용자 수정/삭제 → 차단 메시지

### 결론

| 분류 | 건수 |
|---|---|
| 발견·수정 완료 갭 | 3건 (GAP-001·003·004) |
| 정상 판정 (수정 불필요) | 1건 (GAP-002) |
| 기존 정상 구현 확인 | 13건 |

**T022 갭 수정 완료. 통합 테스트 체크리스트 수동 검증 후 시연 준비 완료.**
