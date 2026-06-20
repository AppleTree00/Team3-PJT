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