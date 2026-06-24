# QA.md: QA 에이전트 작업 지침

## 1. 목표

3일 시연용 시나리오에 대한 기능 검증 및 예외 케이스 처리 방어.

## **2\. 주요 검증 규칙**

* **시나리오 테스트:** 준비된 샘플 3종 데이터를 입력하여 모든 기능(작성, 코칭, 미리보기) 정상 작동 여부 확인.  
* **예외 처리 방어:** 미구현 기능 호출 시 팝업 메시지 노출 확인.  
* **파일 검증:** PDF/WORD 파일 이외의 파일 업로드 시 시스템 안정성 확인.

## **3\. 3일차 마일스톤**

* **1일차:** 검증 시나리오 작성 및 API 엔드포인트 수동 테스트.  
* **2일차:** UI/UX 결합 테스트 및 AI 코칭 답변 일관성 검토 (→ **[진행 완료]** 상세 내용은 `a4u-webapp/QA_REPORT.md` 참고 및 pm.md에 Task 배정 완료).  
* **3일차:** 최종 리허설, 예외 상황에 대한 시스템 대응 가이드 문서화.

---


## **4. 일반 계정 전체 플로우 QA 결과 (2026-06-24) ✅ 전건 PASS**

### 4.1 테스트 범위
회원가입 → 로그인 → 이력서 작성 → AI 코칭 → 저장 → 제출지원 → 새 이력서 작성 → 기존 이력서 수정/저장

### 4.2 정상 확인 항목
| 플로우 | 결과 |
|---|---|
| 회원가입 (`POST /api/auth/register`) | PASS |
| 로그인 / 로그아웃 (`POST /api/auth/login,logout`) | PASS |
| 새 이력서 생성 — 전체 섹션 입력 (`POST /api/resumes`) | PASS |
| 이력서 단건 조회 (`GET /api/resumes/{id}`) | PASS |
| 이력서 수정/저장 (`PUT /api/resumes/{id}`) | PASS |
| AI 코칭 (`POST /api/coaching` — mock 모드 정상) | PASS |
| 작성률 — 프론트 JS 자체 계산 (별도 API 불필요) | PASS |
| 제출처 생성 (`POST /api/applications`) | PASS |
| 제출처 목록 조회 (`GET /api/applications`) | PASS |
| 제출처 상태 업데이트 (`PUT /api/applications/{id}`) | PASS |
| 새 이력서 작성 시 빈 폼으로 시작 | PASS |
| 기존 이력서 목록 조회 후 수정/재저장 | PASS |

### 4.3 발견 및 수정 완료된 버그
| ID | 심각도 | 현상 | 조치 |
|---|---|---|---|
| BUG-001 | HIGH | `GET /api/resumes` 에서 사용자 이력서에 샘플 3개 혼재 | 기본은 사용자 이력서만 반환, `?include_samples=true` 파라미터로 선택 포함 가능하도록 수정 |
| BUG-002 | MEDIUM | `POST /api/applications` 시 `applied_date` 필드 무시 | 모델에 `applied_date VARCHAR(20)` 추가, DB ALTER TABLE 마이그레이션, 라우트 반영 |
| BUG-003 | LOW | 샘플 이력서 편집 시도 시 에러 메시지 불명확 | `is_sample=True` 체크 추가, "샘플 이력서는 편집할 수 없습니다" 명확한 403 반환 |

### 4.4 잔여 참고사항 (버그 아님)
- AI 코칭: `GEMINI_API_KEY` / `OPENAI_API_KEY` 미설정 시 Mock 모드 동작 (의도된 Fallback)
- 제출처 `submitted_at`: status=`submitted` 변경 시에만 자동 기록 (설계 사양)
- Tailwind CDN 경고: 기능 무관, 프로덕션 배포 시 빌드 방식으로 전환 권장

## 4. 기능별 테스트 결과 (2026-06-24)

### 4.1. 이력서 빌더 - AI 코칭 기능 확장
*   **테스트 범위:** '자기소개서' 섹션에 추가된 AI 코칭 기능 검증.
*   **테스트 시나리오:**
    1.  '자기소개서' 입력 후 'AI 코칭' 버튼 클릭.
    2.  로딩 상태(스피너) 및 버튼 비활성화 확인.
    3.  AI 코칭 모달창 출력 및 내용 확인.
    4.  '내용 적용하기' 버튼 클릭.
    5.  '자기소개서' `textarea`가 '개선 후' 내용으로 정상 업데이트되는지 확인.
    6.  기존 '전문가 요약' AI 코칭 기능이 영향을 받지 않는지 교차 확인.
*   **결과:** **PASS**
*   **비고:** `summary-coaching-btn`, `cover-letter-coaching-btn` 등 명확한 ID를 사용하고, 코칭 대상을 `coachingTargetId` 변수로 관리하는 리팩토링 덕분에 기능이 명확하고 안정적으로 동작함을 확인했습니다. 확장성 높은 좋은 구조입니다.

