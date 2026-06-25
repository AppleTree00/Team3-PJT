"""
resume_routes.py — 이력서 CRUD, 인증, 통계 API
Blueprint: /api
"""
import json
import os
import re
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, Resume, ResumeTemplate, JobApplication, UploadedFile
from werkzeug.utils import secure_filename

resume_bp = Blueprint('resume_bp', __name__, url_prefix='/api')

# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────

# [수정 2026-06-25] 이력서 저장 시 HTML 파일 내보내기 + UploadedFile 버전 기록
_HTML_EXPORT_TMPL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8"/>
<title>{full_name} 이력서</title>
<style>
  body{{font-family:'Noto Sans KR',sans-serif;margin:0;padding:32px;color:#1a1a1a;background:#fff;max-width:780px;margin-inline:auto;}}
  h1{{font-size:26px;font-weight:700;margin:0 0 4px;}}
  .subtitle{{font-size:14px;color:#555;margin-bottom:16px;}}
  .contact{{font-size:13px;color:#444;display:flex;flex-wrap:wrap;gap:12px;margin-bottom:24px;border-bottom:2px solid #3b4bdb;padding-bottom:12px;}}
  section{{margin-bottom:28px;}}
  h2{{font-size:15px;font-weight:700;border-bottom:1px solid #e0e0e0;padding-bottom:4px;margin-bottom:12px;color:#3b4bdb;text-transform:uppercase;letter-spacing:.05em;}}
  .summary{{font-size:13px;line-height:1.8;color:#333;}}
  .exp-item{{margin-bottom:16px;}}
  .exp-header{{display:flex;justify-content:space-between;align-items:baseline;}}
  .exp-title{{font-weight:600;font-size:14px;}}
  .exp-company{{font-size:13px;color:#555;}}
  .exp-period{{font-size:12px;color:#888;white-space:nowrap;}}
  .exp-desc{{font-size:13px;color:#444;line-height:1.7;margin-top:4px;white-space:pre-line;}}
  .skills{{display:flex;flex-wrap:wrap;gap:8px;}}
  .skill-tag{{background:#eef0ff;color:#3b4bdb;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}}
  .footer{{font-size:11px;color:#aaa;margin-top:40px;text-align:right;}}
</style>
</head>
<body>
<h1>{full_name}</h1>
<div class="subtitle">{job_title}</div>
<div class="contact">
  {email_html}
  {phone_html}
  {location_html}
</div>
{summary_html}
{experience_html}
{skills_html}
{cover_html}
<div class="footer">생성일: {generated_at} · a4u Resume AI Coaching</div>
</body></html>"""

def _export_resume_html(resume: 'Resume', user: 'User'):
    """이력서를 HTML 파일로 내보내고 UploadedFile 버전 레코드를 생성한다."""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER', '')
        if not upload_folder or not os.path.isdir(upload_folder):
            return

        user_name = re.sub(r'[\\/:*?"<>|]', '', user.name) if user else '사용자'
        existing_count = UploadedFile.query.filter_by(user_id=user.id).count()
        next_ver = existing_count + 1
        dt_str = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        display_name = f"{user_name}_이력서_{dt_str}({next_ver}).html"
        import time as _time
        saved_name = f"{int(_time.time()*1000)}_{display_name}"

        # HTML 렌더링
        skills = resume.get_skills()
        experience = resume.get_experience()

        email_html  = f'<span>✉ {resume.email}</span>' if resume.email else ''
        phone_html  = f'<span>📞 {resume.phone}</span>' if resume.phone else ''
        loc_html    = f'<span>📍 {resume.location}</span>' if resume.location else ''

        summary_html = (f'<section><h2>전문가 요약</h2>'
                        f'<p class="summary">{resume.summary}</p></section>') if resume.summary else ''

        exp_items = []
        for e in experience:
            period = f"{e.get('start_date','')}" + (f" ~ {e.get('end_date','')}" if e.get('end_date') else ' ~ 현재')
            exp_items.append(
                f'<div class="exp-item">'
                f'<div class="exp-header">'
                f'<div><span class="exp-title">{e.get("title","")}</span> '
                f'<span class="exp-company">· {e.get("company","")}</span></div>'
                f'<span class="exp-period">{period}</span>'
                f'</div>'
                f'<div class="exp-desc">{e.get("description","")}</div>'
                f'</div>'
            )
        experience_html = (f'<section><h2>경력 사항</h2>{"".join(exp_items)}</section>') if exp_items else ''

        skill_tags = ''.join(f'<span class="skill-tag">{s}</span>' for s in skills)
        skills_html = (f'<section><h2>보유 기술</h2><div class="skills">{skill_tags}</div></section>') if skills else ''

        # [수정 2026-06-25] 자기소개 3필드 — extra_json 에서 추출해 HTML 내보내기에 포함
        try:
            extra = json.loads(resume.extra_json or '{}')
        except Exception:
            extra = {}
        cover_parts = []
        if extra.get('work_narrative', '').strip():
            cover_parts.append(f'<h3 style="font-size:13px;font-weight:700;margin:0 0 4px;color:#3b4bdb;">직무 수행 경험</h3>'
                               f'<p style="font-size:13px;line-height:1.8;color:#333;white-space:pre-line;">{extra["work_narrative"]}</p>')
        if extra.get('motivation', '').strip():
            cover_parts.append(f'<h3 style="font-size:13px;font-weight:700;margin:8px 0 4px;color:#3b4bdb;">지원 동기</h3>'
                               f'<p style="font-size:13px;line-height:1.8;color:#333;white-space:pre-line;">{extra["motivation"]}</p>')
        if extra.get('aspiration', '').strip():
            cover_parts.append(f'<h3 style="font-size:13px;font-weight:700;margin:8px 0 4px;color:#3b4bdb;">향후 포부</h3>'
                               f'<p style="font-size:13px;line-height:1.8;color:#333;white-space:pre-line;">{extra["aspiration"]}</p>')
        cover_html = (f'<section><h2>자기소개</h2>{"".join(cover_parts)}</section>') if cover_parts else ''

        html_content = _HTML_EXPORT_TMPL.format(
            full_name=resume.full_name or '',
            job_title=resume.job_title or '',
            email_html=email_html, phone_html=phone_html, location_html=loc_html,
            summary_html=summary_html,
            experience_html=experience_html,
            skills_html=skills_html,
            cover_html=cover_html,
            generated_at=datetime.now(timezone.utc).strftime('%Y년 %m월 %d일'),
        )

        file_path = os.path.join(upload_folder, saved_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        rec = UploadedFile(
            user_id=user.id,
            original_name=display_name,
            saved_name=saved_name,
            size=os.path.getsize(file_path),
            mime_type='text/html',
            version_num=next_ver,
            file_kind='export',
            resume_id=resume.id,
        )
        db.session.add(rec)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        print(f'[export_html] 실패: {exc}')


def current_user():
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify(success=False, message='로그인이 필요합니다.'), 401
        return fn(*args, **kwargs)
    return wrapper

def demo_mode_blocked(fn):
    """데모 모드일 경우 쓰기 작업을 차단하는 데코레이터"""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get('mode') == 'DEMO':
            return jsonify(success=False, status="blocked", message="데모 체험 중에는 이 기능을 사용할 수 없습니다. 일반 계정으로 이용해주세요."), 403
        return fn(*args, **kwargs)
    return wrapper

# ─────────────────────────────────────────────
# 인증 API
# ─────────────────────────────────────────────
@resume_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify(success=False, message='이메일과 비밀번호를 입력해주세요.'), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(success=False, message='이메일 또는 비밀번호가 올바르지 않습니다.'), 401

    if user.status != 'active':
        return jsonify(success=False, message='정지된 계정입니다. 관리자에게 문의하세요.'), 403

    session.permanent = True
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = user.is_admin

    if user.is_admin:
        session['mode'] = 'ADMIN'
    elif user.email == 'demo@a4u.com':
        session['mode'] = 'DEMO'
    else:
        session['mode'] = 'GENERAL'

    return jsonify(success=True, user=user.to_dict(), mode=session.get('mode'))


@resume_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify(success=True, message='로그아웃 되었습니다.')


@resume_bp.route('/auth/switch_mode', methods=['GET', 'POST'])
@login_required
def switch_mode():
    """DEMO ↔ GENERAL 모드 전환 (GET: 현재 모드 조회, POST: 전환)"""
    if request.method == 'GET':
        return jsonify(success=True, mode=session.get('mode', 'GENERAL'))
    data = request.get_json(silent=True) or {}
    new_mode = (data.get('mode') or '').upper()
    user = current_user()
    if user.email == 'demo@a4u.com' and new_mode == 'GENERAL':
        return jsonify(success=False, message='데모 계정은 GENERAL 모드로 전환할 수 없습니다.'), 403
    if new_mode not in ('DEMO', 'GENERAL'):
        return jsonify(success=False, message='유효하지 않은 모드입니다. DEMO 또는 GENERAL 중 하나를 입력하세요.'), 400
    session['mode'] = new_mode
    return jsonify(success=True, mode=new_mode, message=f'{"데모" if new_mode == "DEMO" else "일반"} 모드로 전환되었습니다.')


@resume_bp.route('/auth/profile', methods=['PUT'])
@login_required
@demo_mode_blocked
def update_profile():
    """이름·이메일 변경 (현재 비밀번호 확인 필수)"""
    data = request.get_json(silent=True) or {}
    user = current_user()

    current_pw = data.get('current_password', '')
    if not user.check_password(current_pw):
        return jsonify(success=False, message='현재 비밀번호가 올바르지 않습니다.'), 400

    new_name  = data.get('name', '').strip()
    new_email = data.get('email', '').strip().lower()

    if not new_name or not new_email:
        return jsonify(success=False, message='이름과 이메일을 모두 입력해주세요.'), 400

    if new_email != user.email:
        if User.query.filter_by(email=new_email).first():
            return jsonify(success=False, message='이미 사용 중인 이메일입니다.'), 409

    user.name  = new_name
    user.email = new_email
    db.session.commit()

    session['user_name'] = user.name
    return jsonify(success=True, user=user.to_dict())


@resume_bp.route('/auth/change-password', methods=['PUT'])
@login_required
@demo_mode_blocked
def change_password():
    """비밀번호 변경 (현재 비밀번호 + 새 비밀번호)"""
    data = request.get_json(silent=True) or {}
    user = current_user()

    current_pw = data.get('current_password', '')
    new_pw     = data.get('new_password', '')
    confirm_pw = data.get('confirm_password', '')

    if not user.check_password(current_pw):
        return jsonify(success=False, message='현재 비밀번호가 올바르지 않습니다.'), 400
    if len(new_pw) < 6:
        return jsonify(success=False, message='새 비밀번호는 6자 이상이어야 합니다.'), 400
    if new_pw != confirm_pw:
        return jsonify(success=False, message='새 비밀번호와 확인 비밀번호가 일치하지 않습니다.'), 400
    if current_pw == new_pw:
        return jsonify(success=False, message='새 비밀번호가 현재 비밀번호와 동일합니다.'), 400

    user.set_password(new_pw)
    db.session.commit()
    return jsonify(success=True, message='비밀번호가 변경되었습니다.')


@resume_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """비밀번호 찾기 — 임시 비밀번호 발급 (MVP: 화면 표시, 추후 이메일 발송)"""
    import secrets, string
    data  = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify(success=False, message='이메일을 입력해주세요.'), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(success=False, message='가입된 이메일이 아닙니다.'), 404

    alphabet  = string.ascii_letters + string.digits
    temp_pw   = ''.join(secrets.choice(alphabet) for _ in range(10))
    user.set_password(temp_pw)
    db.session.commit()

    return jsonify(success=True, temp_password=temp_pw,
                   message='임시 비밀번호가 발급되었습니다. 로그인 후 즉시 변경해주세요.')


@resume_bp.route('/auth/me', methods=['GET'])
def me():
    user = current_user()
    if not user:
        return jsonify(success=False, message='로그인이 필요합니다.'), 401
    return jsonify(success=True, user=user.to_dict(), mode=session.get('mode', 'GENERAL'))


@resume_bp.route('/auth/admin-demo-login', methods=['POST'])
def admin_demo_login():
    """관리자 데모 전용 로그인 — mode='DEMO'로 세션 설정 후 /admin으로 redirect."""
    from flask import redirect as flask_redirect
    user = User.query.filter_by(email='admin@a4u.com').first()
    if not user:
        # fetch 호출인지 form POST인지 구분
        if request.accept_mimetypes.accept_json:
            return jsonify(success=False, message='관리자 계정이 존재하지 않습니다.'), 404
        return flask_redirect('/login.html?error=no_admin')
    if user.status != 'active':
        if request.accept_mimetypes.accept_json:
            return jsonify(success=False, message='정지된 계정입니다.'), 403
        return flask_redirect('/login.html?error=suspended')

    session.permanent = True
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = True
    session['mode'] = 'DEMO'

    # form POST(브라우저) 방식 → 302 redirect로 쿠키를 안정적으로 전달
    # fetch 방식(Accept: application/json) → JSON 반환 (하위 호환)
    wants_json = (
        request.content_type == 'application/json'
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )
    if wants_json:
        return jsonify(success=True, user=user.to_dict())
    return flask_redirect('/admin')


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@resume_bp.route('/auth/avatar', methods=['POST'])
@login_required
@demo_mode_blocked
def upload_avatar():
    """프로필 이미지 업로드"""
    if 'avatar' not in request.files:
        return jsonify(success=False, message='이미지 파일이 없습니다.'), 400
    f = request.files['avatar']
    if not f.filename or not _allowed_image(f.filename):
        return jsonify(success=False, message='지원하지 않는 파일 형식입니다. (PNG, JPG, GIF, WebP)'), 400

    ext      = f.filename.rsplit('.', 1)[1].lower()
    filename = f'avatar_{current_user().id}_{uuid.uuid4().hex[:8]}.{ext}'
    save_dir = os.path.join(current_app.root_path, 'static', 'avatars')
    os.makedirs(save_dir, exist_ok=True)
    f.save(os.path.join(save_dir, filename))

    user = current_user()
    user.avatar_url = f'/static/avatars/{filename}'
    db.session.commit()
    return jsonify(success=True, avatar_url=user.avatar_url, user=user.to_dict())


@resume_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')

    if not email or not name or not password:
        return jsonify(success=False, message='이름, 이메일, 비밀번호를 모두 입력해주세요.'), 400

    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='이미 등록된 이메일입니다.'), 409

    if len(password) < 6:
        return jsonify(success=False, message='비밀번호는 6자 이상이어야 합니다.'), 400

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session.permanent = True
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['is_admin'] = user.is_admin
    session['mode'] = 'GENERAL'
    return jsonify(success=True, user=user.to_dict()), 201


# ─────────────────────────────────────────────
# 이력서 CRUD API
# ─────────────────────────────────────────────
@resume_bp.route('/resumes', methods=['GET'])
def list_resumes():
    user = current_user()
    uid = user.id if user else None

    # 기본: 사용자 본인 이력서만, ?include_samples=true 시 샘플도 포함
    include_samples = request.args.get('include_samples', 'false').lower() == 'true'
    if uid:
        if include_samples:
            resumes = Resume.query.filter(
                (Resume.user_id == uid) | (Resume.is_sample == True)
            ).order_by(Resume.created_at.desc()).all()
        else:
            resumes = Resume.query.filter_by(user_id=uid).order_by(Resume.created_at.desc()).all()
    else:
        resumes = Resume.query.filter_by(is_sample=True).all()

    return jsonify(success=True, resumes=[r.to_dict() for r in resumes])


@resume_bp.route('/resumes', methods=['POST'])
@login_required
@demo_mode_blocked
def create_resume():
    data = request.get_json(silent=True) or {}
    user = current_user()

    resume = Resume(
        user_id=user.id if user else None,
        template_id=data.get('template_id'),
        title=data.get('title', '새 이력서'),
        full_name=data.get('full_name', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        location=data.get('location', ''),
        job_title=data.get('job_title', ''),
        summary=data.get('summary', ''),
        experience_json=json.dumps(data.get('experience', []), ensure_ascii=False),
        education_json=json.dumps(data.get('education', []), ensure_ascii=False),
        skills_json=json.dumps(data.get('skills', []), ensure_ascii=False),
        extra_json=json.dumps(data.get('extra', {}), ensure_ascii=False),
        sample_type=data.get('sample_type', 'custom'),
        is_sample=False,
    )
    db.session.add(resume)
    db.session.commit()
    # [수정 2026-06-25] 저장 완료 후 HTML 내보내기 + 버전 파일 기록
    user = current_user()
    if user:
        _export_resume_html(resume, user)
    return jsonify(success=True, resume=resume.to_dict()), 201


@resume_bp.route('/resumes/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    # 샘플은 누구나 열람 가능, 본인 이력서만 접근
    if not resume.is_sample and (not user or resume.user_id != user.id):
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    return jsonify(success=True, resume=resume.to_dict())


@resume_bp.route('/resumes/<int:resume_id>', methods=['PUT'])
@login_required
@demo_mode_blocked
def update_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    if resume.is_sample:
        return jsonify(success=False, message='샘플 이력서는 편집할 수 없습니다. 새 이력서를 작성하거나 샘플을 복사해 사용하세요.'), 403
    if resume.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403

    data = request.get_json(silent=True) or {}
    for field in ('title', 'full_name', 'email', 'phone', 'location', 'job_title', 'summary'):
        if field in data:
            setattr(resume, field, data[field])
    if 'experience' in data:
        resume.experience_json = json.dumps(data['experience'], ensure_ascii=False)
    if 'education' in data:
        resume.education_json = json.dumps(data['education'], ensure_ascii=False)
    if 'skills' in data:
        resume.skills_json = json.dumps(data['skills'], ensure_ascii=False)
    if 'extra' in data:
        resume.extra_json = json.dumps(data['extra'], ensure_ascii=False)
    if 'template_id' in data:
        resume.template_id = data['template_id']

    resume.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    # [수정 2026-06-25] 수정 완료 후 HTML 내보내기 + 버전 파일 기록
    user = current_user()
    if user:
        _export_resume_html(resume, user)
    return jsonify(success=True, resume=resume.to_dict())


@resume_bp.route('/resumes/<int:resume_id>', methods=['DELETE'])
@login_required
@demo_mode_blocked
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    user = current_user()
    if resume.is_sample:
        return jsonify(success=False, message='샘플 이력서는 삭제할 수 없습니다.'), 403
    if resume.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    db.session.delete(resume)
    db.session.commit()
    return jsonify(success=True, message='이력서가 삭제되었습니다.')


# ─────────────────────────────────────────────
# 제출 관리 API
# ─────────────────────────────────────────────
@resume_bp.route('/applications', methods=['GET'])
def list_applications():
    user = current_user()
    uid = user.id if user else None
    if uid:
        apps = JobApplication.query.filter_by(user_id=uid).order_by(JobApplication.created_at.desc()).all()
    else:
        apps = []
    return jsonify(success=True, applications=[a.to_dict() for a in apps])


@resume_bp.route('/applications', methods=['POST'])
@login_required
@demo_mode_blocked
def create_application():
    data = request.get_json(silent=True) or {}
    user = current_user()
    app_obj = JobApplication(
        user_id=user.id if user else None,
        resume_id=data.get('resume_id'),
        template_id=data.get('template_id'),
        company=data.get('company', ''),
        position=data.get('position', ''),
        status=data.get('status', 'draft'),
        notes=data.get('notes', ''),
        applied_date=data.get('applied_date') or data.get('applied_at'),
    )
    db.session.add(app_obj)
    db.session.commit()
    return jsonify(success=True, application=app_obj.to_dict()), 201


@resume_bp.route('/applications/<int:app_id>', methods=['PUT'])
@login_required
@demo_mode_blocked
def update_application(app_id):
    app_obj = JobApplication.query.get_or_404(app_id)
    user = current_user()
    if app_obj.user_id != user.id:
        return jsonify(success=False, message='접근 권한이 없습니다.'), 403
    data = request.get_json(silent=True) or {}
    for field in ('company', 'position', 'status', 'notes', 'template_id', 'resume_id', 'applied_date'):
        if field in data:
            setattr(app_obj, field, data[field])
    if data.get('status') == 'submitted' and not app_obj.submitted_at:
        app_obj.submitted_at = datetime.now(timezone.utc)
    app_obj.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, application=app_obj.to_dict())


# ─────────────────────────────────────────────
# 대시보드 통계 API
# ─────────────────────────────────────────────
@resume_bp.route('/stats', methods=['GET'])
def stats():
    user = current_user()
    if not user:
        return jsonify(success=False, message='로그인이 필요합니다.'), 401

    uid = user.id
    user_resumes = Resume.query.filter_by(user_id=uid, is_sample=False).count()
    user_uploads = UploadedFile.query.filter_by(user_id=uid).count()
    user_applications = JobApplication.query.filter_by(user_id=uid).count()
    submitted = JobApplication.query.filter_by(user_id=uid, status='submitted').count()
    accepted = JobApplication.query.filter_by(user_id=uid, status='accepted').count()

    return jsonify(
        success=True,
        stats={
            'total_resumes': user_resumes,
            'total_uploads': user_uploads,
            'total_applications': user_applications,
            'submitted_applications': submitted,
            'accepted_applications': accepted,
        }
    )
