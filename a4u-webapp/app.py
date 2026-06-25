import os
import re
import json
import time
from datetime import datetime, timezone, timedelta
# [수정 2026-06-25] PDF/DOCX 파싱 + AI 분석 추가
import io
from flask import Flask, request, jsonify, redirect, send_from_directory, session, render_template
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge, HTTPException
from models import db, User, UploadedFile, Resume, ResumeTemplate, JobApplication

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")

load_env()

app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')
app.secret_key = os.environ.get('SECRET_KEY', 'a4u-dev-secret-key-change-in-production')
app.permanent_session_lifetime = timedelta(hours=8)

CORS(app, supports_credentials=True)

# ── DB 설정 ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'a4u.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ── 블루프린트 등록 ───────────────────────────────────────────────────
from admin_routes import admin_bp
from resume_routes import resume_bp
from coaching_routes import coaching_bp

app.register_blueprint(admin_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(coaching_bp)

# ── 어드민 HTML 라우트 ────────────────────────────────────────────────
@app.route('/admin')
@app.route('/admin.html')
def admin_page():
    return render_template('admin.html')

# ── 템플릿 미리보기 ────────────────────────────────────────────────────
@app.route('/api/admin/templates/<int:template_id>/preview')
def preview_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    return t.html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ── 서버 설정 ─────────────────────────────────────────────────────────
PORT = os.environ.get('PORT', 5000)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
ALLOWED_MIMETYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_allowed_mimetype(mimetype):
    return mimetype in ALLOWED_MIMETYPES

# ── 인증 미들웨어 ─────────────────────────────────────────────────────
# 로그인 없이 접근 시 login.html으로 리디렉션하는 보호 페이지 목록
PROTECTED_PAGES = {
    'main.html', # 관리자는 메인 페이지 접근 시 로그아웃
    'dashboard.html', 'builder.html', 'resume.html',
    'timeline.html', 'profile-menu.html', 'select.html'
}

# 어드민 데모 세션이 접근할 경우 자동 로그아웃되는 경로 (사용자 페이지 + 홈)
ADMIN_DEMO_LOGOUT_PATHS = {
    '', 'main.html',
    'dashboard.html', 'builder.html', 'resume.html',
    'timeline.html', 'profile-menu.html', 'select.html'
}

@app.before_request
def require_login():
    path = request.path.lstrip('/')

    # 어드민 데모 세션 격리: is_admin=True AND mode='DEMO'인 경우
    # 사용자 페이지나 홈 접근 시 세션을 clear하고 해당 페이지로 이동
    if session.get('is_admin') and session.get('mode') == 'DEMO':
        if path in ADMIN_DEMO_LOGOUT_PATHS:
            session.clear()
            dest = f'/{path}' if path else '/main.html'
            return redirect(dest)

    # 어드민 페이지 보호: 로그인 필요 + 어드민 권한 필요
    if path in ('admin', 'admin.html'):
        if not session.get('user_id'):
            return redirect('/login.html?next=admin&reason=auth')
        if not session.get('is_admin'):
            return redirect('/dashboard.html')
    # 데모 대시보드 보호: 로그인 필요 + 데모 모드만 접근
    if path == 'demo_dashboard.html':
        if not session.get('user_id'):
            return redirect('/login.html?reason=auth')
        if session.get('mode') != 'DEMO':
            return redirect('/dashboard.html')
    # 일반 보호 페이지: 로그인만 필요
    if path in PROTECTED_PAGES:
        if not session.get('user_id'):
            # main.html은 로그아웃 상태에서 접근 가능해야 함
            if path == 'main.html':
                return
            return redirect(f'/login.html?next={path}&reason=auth')
        # [수정 2026-06-25] 관리자가 사용자 페이지에 접근 시도 시 → 세션 클리어 후 로그인으로 이동
        # [이전 코드] return redirect('/admin')
        if session.get('is_admin'):
            session.clear()
            return redirect(f'/login.html?next={path}&reason=auth')
        # 데모 사용자가 일반 dashboard에 접근 시 → demo_dashboard로 리다이렉트
        if path == 'dashboard.html' and session.get('mode') == 'DEMO':
            return redirect('/demo_dashboard.html')

# ── 기본 라우트 ───────────────────────────────────────────────────────
@app.route('/')
def index():
    return redirect('/main.html')

@app.route('/login')
@app.route('/login.html')
def login_page():
    if session.get('user_id'):
        if session.get('is_admin'):
            return redirect('/admin')
        return redirect('/dashboard.html')
    return render_template('login.html')

@app.route('/main.html')
def main_page():
    return render_template('main.html')

@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/builder.html')
def builder_page():
    return render_template('builder.html')

@app.route('/resume.html')
def resume_page():
    return render_template('resume.html')

@app.route('/timeline.html')
def timeline_page():
    return render_template('timeline.html')

@app.route('/profile-menu.html')
def profile_menu_page():
    return render_template('profile-menu.html')

@app.route('/select.html')
def select_page():
    return render_template('select.html')

@app.route('/demo_dashboard.html')
def demo_dashboard_page():
    return render_template('demo_dashboard.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(BASE_DIR, 'favicon.svg', mimetype='image/svg+xml')

# ── 이력서 템플릿 공개 API ──────────────────────────────────────────
@app.route('/api/templates', methods=['GET'])
def public_templates():
    templates = ResumeTemplate.query.filter_by(is_active=True).all()
    return jsonify(templates=[t.to_dict() for t in templates])

# ── [수정 2026-06-25] 파일에서 텍스트 추출 ──────────────────────────
def _extract_text_from_file(file_path, mime_type):
    text = ''
    try:
        if mime_type == 'application/pdf':
            # pypdf 우선 시도
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    text += (page.extract_text() or '') + '\n'
            except Exception as e1:
                print(f"[upload] pypdf 실패({e1}), pdfminer 시도")
            # pypdf 결과 없으면 pdfminer.six 폴백
            if not text.strip():
                try:
                    from pdfminer.high_level import extract_text as pm_extract
                    text = pm_extract(file_path) or ''
                except Exception as e2:
                    print(f"[upload] pdfminer 도 실패: {e2}")
        elif mime_type in ('application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'application/msword'):
            import docx as docxlib
            doc = docxlib.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + '\n'
    except Exception as e:
        print(f"[upload] 텍스트 추출 실패: {e}")
    return text.strip()


# ── [수정 2026-06-25] 추출 텍스트 AI 분석 ───────────────────────────
def _analyze_resume_with_ai(text):
    """OpenAI → Gemini → 기본값 순서로 이력서 텍스트를 분석해 구조화된 JSON 반환"""
    if not text:
        return None

    # [수정 2026-06-25] experience[] 배열 추가 — 경력사항 자동 채우기 지원
    system_prompt = (
        "당신은 이력서 파싱 전문가입니다. 주어진 이력서 텍스트에서 정보를 추출해 "
        "반드시 아래 JSON 형식으로만 응답하세요. 없는 정보는 빈 문자열 또는 빈 배열로 두세요.\n"
        "experience의 start_date/end_date는 'YYYY-MM' 형식으로, end_date가 현재이면 빈 문자열('')로 두세요.\n"
        'description은 주요 성과·업무를 개행(\n)으로 구분하세요. skills는 기술명 배열입니다.\n'
        '{"name":"","job_title":"","email":"","phone":"","location":"","summary":"",'
        '"skills":[],'
        '"experience":[{"title":"","company":"","start_date":"","end_date":"","description":""}]}'
    )
    user_msg = f"이력서:\n{text[:6000]}"

    openai_key = os.environ.get('OPENAI_API_KEY', '')
    gemini_key = os.environ.get('GEMINI_API_KEY', '')

    raw = None

    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ],
                temperature=0,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            raw = resp.choices[0].message.content
            print(f"[upload] OpenAI 분석 성공")
        except Exception as e:
            print(f"[upload] OpenAI 분석 실패: {e}")

    if raw is None and gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"{system_prompt}\n\n{user_msg}"
            resp = model.generate_content(prompt)
            raw = resp.text
            print(f"[upload] Gemini 분석 성공")
        except Exception as e:
            print(f"[upload] Gemini 분석 실패: {e}")

    if raw:
        try:
            # JSON 블록 추출
            import re as _re
            m = _re.search(r'\{.*\}', raw, _re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as e:
            print(f"[upload] JSON 파싱 실패: {e}, raw={raw[:200]}")

    return None


# ── 파일 업로드 API ───────────────────────────────────────────────────
@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    if session.get('mode') == 'DEMO':
        return jsonify(success=False, status="blocked", message="데모 체험 중에는 이 기능을 사용할 수 없습니다. 일반 계정으로 이용해주세요."), 403
    if 'resumeFile' not in request.files:
        return jsonify(success=False, message='파일이 필요합니다.'), 400

    file = request.files['resumeFile']
    if file.filename == '':
        return jsonify(success=False, message='파일이 선택되지 않았습니다.'), 400

    if file and is_allowed_mimetype(file.mimetype):
        sanitized_original = re.sub(r'[^a-zA-Z0-9._-]', '-', file.filename)
        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}-{sanitized_original}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        uploaded = UploadedFile(
            original_name=file.filename,
            saved_name=filename,
            size=file_size,
            mime_type=file.mimetype
        )
        db.session.add(uploaded)
        db.session.commit()

        # [수정 2026-06-25] 텍스트 추출 + AI 분석
        extracted_text = _extract_text_from_file(file_path, file.mimetype)
        analysis = _analyze_resume_with_ai(extracted_text) if extracted_text else None
        has_analysis = analysis is not None
        print(f"[upload] 텍스트 길이={len(extracted_text)}, AI 분석={'성공' if has_analysis else '실패/미수행'}")

        return jsonify({
            "success": True,
            "originalName": file.filename,
            "savedName": filename,
            "size": file_size,
            "mimeType": file.mimetype,
            "uploadedAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "analysis": analysis,
            "textLength": len(extracted_text)
        })
    else:
        return jsonify(
            success=False,
            message='지원하지 않는 파일 형식입니다. PDF, DOC, DOCX 파일만 업로드할 수 있습니다.'
        ), 400

# ── 오류 핸들러 ───────────────────────────────────────────────────────
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def handle_too_large(e):
    return jsonify(success=False, message=f'파일 크기는 {app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024:.0f}MB를 초과할 수 없습니다.'), 413

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    print(f"An error occurred: {e}")
    return jsonify(success=False, message='알 수 없는 오류가 발생했습니다.'), 500

# ── DB 초기화 및 시드 데이터 ─────────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()

        # ── 컬럼 마이그레이션 (ALTER TABLE) ─────────────────────────
        migrations = [
            "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)",
            "ALTER TABLE uploaded_files ADD COLUMN file_path VARCHAR(500)",
            "ALTER TABLE uploaded_files ADD COLUMN file_type VARCHAR(10)",
            "ALTER TABLE uploaded_files ADD COLUMN original_filename VARCHAR(255)",
            "ALTER TABLE uploaded_files ADD COLUMN resume_analysis TEXT",
            "ALTER TABLE resume_templates ADD COLUMN file_path VARCHAR(500)",
            "ALTER TABLE resume_templates ADD COLUMN file_type VARCHAR(10)",
            "ALTER TABLE resume_templates ADD COLUMN original_filename VARCHAR(255)",
            "ALTER TABLE job_applications ADD COLUMN applied_date VARCHAR(20)",
        ]
        for sql in migrations:
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
            except Exception:
                db.session.rollback()

        # 기본 관리자 계정
        if not User.query.filter_by(email='admin@a4u.com').first():
            admin = User(email='admin@a4u.com', name='관리자', is_admin=True, status='active')
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin1234'))
            db.session.add(admin)

        # 데모 일반 사용자
        demo = User.query.filter_by(email='demo@a4u.com').first()
        if not demo:
            demo = User(email='demo@a4u.com', name='홍길동', is_admin=False, status='active')
            demo.set_password('demo1234')
            db.session.add(demo)
            db.session.flush()
        # 데모 아바타 설정 (항상 최신 경로 유지)
        demo.avatar_url = '/static/avatars/demo_avatar.png'

        db.session.flush()

        # 이력서 템플릿 3종
        if ResumeTemplate.query.count() == 0:
            seed_templates = [
                ResumeTemplate(name='IT 개발자형', description='소프트웨어 개발자를 위한 기술 스택 중심 이력서',
                               category='it', html_content=_default_template('IT 개발자형'), is_active=True),
                ResumeTemplate(name='경영 관리자형', description='프로젝트 관리 및 리더십 경험을 강조한 이력서',
                               category='management', html_content=_default_template('경영 관리자형'), is_active=True),
                ResumeTemplate(name='일반 범용형', description='다양한 직군에 활용 가능한 기본 이력서 템플릿',
                               category='general', html_content=_default_template('일반 범용형'), is_active=True),
            ]
            for t in seed_templates:
                db.session.add(t)
            db.session.flush()

        # 샘플 이력서 3종 시드
        if Resume.query.filter_by(is_sample=True).count() == 0:
            templates = {t.category: t for t in ResumeTemplate.query.all()}
            sample_resumes = [
                Resume(
                    template_id=templates.get('it', ResumeTemplate.query.first()).id,
                    title='[샘플] IT 개발자 이력서',
                    full_name='김개발', email='kim.dev@example.com', phone='010-1234-5678',
                    location='서울시 강남구', job_title='시니어 백엔드 개발자',
                    summary='Python/Java 기반 백엔드 개발 7년 경력. 대용량 트래픽 처리 및 MSA 설계 전문. 스타트업부터 대기업까지 다양한 도메인에서 서비스를 설계하고 운영한 경험 보유.',
                    experience_json=json.dumps([
                        {"company": "(주)테크스타트", "position": "시니어 백엔드 개발자", "start": "2021.03", "end": "현재",
                         "bullets": ["Python/FastAPI 기반 결제 API 서버 개발 (월 500만 트랜잭션 처리)", "Kubernetes 기반 MSA 전환으로 배포 주기 주 1회 → 일 5회 개선", "신규 서비스 개발 리드, 3개월 만에 MAU 10만 달성"]},
                        {"company": "ABCCorp", "position": "백엔드 개발자", "start": "2018.07", "end": "2021.02",
                         "bullets": ["Spring Boot 기반 사내 ERP 시스템 개발 및 유지보수", "DB 쿼리 최적화로 평균 응답시간 3초 → 0.4초 개선", "신입 개발자 3명 멘토링"]}
                    ], ensure_ascii=False),
                    education_json=json.dumps([
                        {"school": "한국대학교", "major": "컴퓨터공학", "start": "2014.03", "end": "2018.02", "degree": "학사"}
                    ], ensure_ascii=False),
                    skills_json=json.dumps(["Python", "Java", "FastAPI", "Spring Boot", "PostgreSQL", "Redis", "Kubernetes", "Docker", "AWS"], ensure_ascii=False),
                    sample_type='it', is_sample=True
                ),
                Resume(
                    template_id=templates.get('management', ResumeTemplate.query.first()).id,
                    title='[샘플] 경영 관리자 이력서',
                    full_name='이매니저', email='lee.manager@example.com', phone='010-9876-5432',
                    location='서울시 서초구', job_title='프로젝트 매니저 / PM',
                    summary='IT 프로젝트 기획·관리 10년 경력. 15명 규모 팀 리더십 경험. 공공·금융 SI 프로젝트 총괄 PM으로 대규모 시스템 구축부터 유지보수까지 전 과정 경험 보유.',
                    experience_json=json.dumps([
                        {"company": "(주)한국시스템통합", "position": "수석 개발자 / PM", "start": "2018.01", "end": "현재",
                         "bullets": ["차세대 금융 시스템 구축 프로젝트 총괄 PM (예산 50억, 개발 인원 20명)", "프로젝트 납기 준수율 95% 유지, 고객 만족도 4.8/5.0 달성", "PMP 자격증 취득 후 사내 PM 교육 과정 설계 및 운영"]},
                        {"company": "글로벌IT컨설팅", "position": "선임 컨설턴트", "start": "2015.06", "end": "2017.12",
                         "bullets": ["공공기관 정보화 사업 컨설팅 (사업비 10억~30억 규모 5건)", "비즈니스 프로세스 개선으로 업무 효율 40% 향상 사례 도출"]}
                    ], ensure_ascii=False),
                    education_json=json.dumps([
                        {"school": "서울경영대학교", "major": "경영학", "start": "2005.03", "end": "2009.02", "degree": "학사"},
                        {"school": "연세대학교 대학원", "major": "MIS(경영정보)", "start": "2009.03", "end": "2011.02", "degree": "석사"}
                    ], ensure_ascii=False),
                    skills_json=json.dumps(["PMP", "Agile/Scrum", "MS Project", "JIRA", "Confluence", "PMBOK", "리스크 관리", "이해관계자 관리"], ensure_ascii=False),
                    sample_type='management', is_sample=True
                ),
                Resume(
                    template_id=templates.get('general', ResumeTemplate.query.first()).id,
                    title='[샘플] 일반 범용 이력서',
                    full_name='박지원', email='park.jiwon@example.com', phone='010-5555-7777',
                    location='경기도 성남시', job_title='마케팅 전문가',
                    summary='디지털 마케팅 5년 경력. SNS·콘텐츠·퍼포먼스 마케팅 전 영역 경험. 스타트업 초기 멤버로 입사해 MAU 0 → 50만 성장을 함께한 그로스 마케터.',
                    experience_json=json.dumps([
                        {"company": "라이프스타일 스타트업", "position": "마케팅 매니저", "start": "2020.04", "end": "현재",
                         "bullets": ["SNS(인스타그램·유튜브) 채널 성장 관리 (팔로워 0 → 15만 달성)", "퍼포먼스 마케팅 운영: 월 광고비 3천만 원 집행, ROAS 450% 유지", "브랜드 협업 캠페인 기획 및 진행 (월 평균 5건)"]},
                        {"company": "광고대행사 A", "position": "AE (Account Executive)", "start": "2018.02", "end": "2020.03",
                         "bullets": ["대형 소비재 브랜드 디지털 광고 캠페인 집행 (분기 예산 2억)", "캠페인 KPI 달성률 평균 120% 초과 달성"]}
                    ], ensure_ascii=False),
                    education_json=json.dumps([
                        {"school": "경기대학교", "major": "광고홍보학", "start": "2013.03", "end": "2017.02", "degree": "학사"}
                    ], ensure_ascii=False),
                    skills_json=json.dumps(["Google Analytics", "Meta Ads", "카카오 광고", "Notion", "Figma", "콘텐츠 기획", "카피라이팅", "데이터 분석"], ensure_ascii=False),
                    sample_type='general', is_sample=True
                ),
            ]
            for r in sample_resumes:
                db.session.add(r)

        db.session.commit()
        print("DB initialized.")


def _default_template(name):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"/><title>{name} 이력서</title>
<style>
body {{ font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 24px; color: #111c2d; }}
h1 {{ color: #3525cd; font-size: 28px; margin-bottom: 4px; }}
.section {{ margin-top: 28px; border-top: 2px solid #e7eeff; padding-top: 16px; }}
.section h2 {{ color: #3525cd; font-size: 14px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }}
.item {{ margin-bottom: 16px; }}
.item-title {{ font-weight: 600; }}
.item-sub {{ color: #6b7280; font-size: 14px; }}
</style>
</head>
<body>
<h1>홍길동</h1>
<p style="color:#6b7280;font-size:14px;">hong@example.com · 010-0000-0000 · 서울시</p>
<div class="section">
  <h2>경력</h2>
  <div class="item">
    <div class="item-title">시니어 개발자 — ABC 회사</div>
    <div class="item-sub">2020.03 ~ 현재</div>
    <ul style="font-size:14px;margin-top:6px;padding-left:18px;color:#374151;">
      <li>주요 업무 내용을 여기에 작성합니다.</li>
    </ul>
  </div>
</div>
<div class="section">
  <h2>학력</h2>
  <div class="item">
    <div class="item-title">한국대학교 컴퓨터공학과</div>
    <div class="item-sub">2014.03 ~ 2018.02 졸업</div>
  </div>
</div>
<div class="section">
  <h2>기술</h2>
  <p style="font-size:14px;">Python, Flask, SQL, JavaScript, React</p>
</div>
</body>
</html>"""


if __name__ == '__main__':
    init_db()
    print(f"Server is running at http://localhost:{PORT}")
    print(f"Admin console: http://localhost:{PORT}/admin")
    app.run(host='0.0.0.0', port=int(PORT), debug=True)
