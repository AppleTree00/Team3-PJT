"""
resume_routes.py — 이력서 CRUD, 인증, 통계 API
Blueprint: /api
"""
import json
import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, Resume, ResumeTemplate, JobApplication, UploadedFile
from werkzeug.utils import secure_filename

resume_bp = Blueprint('resume_bp', __name__, url_prefix='/api')

# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────
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
    return jsonify(success=True, user=user.to_dict())


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
    total_users = User.query.filter_by(is_admin=False).count()
    total_resumes = Resume.query.filter_by(is_sample=False).count()
    total_uploads = UploadedFile.query.count()
    total_applications = JobApplication.query.count()
    submitted = JobApplication.query.filter_by(status='submitted').count()
    accepted = JobApplication.query.filter_by(status='accepted').count()

    sample_it = Resume.query.filter_by(is_sample=True, sample_type='it').count()
    sample_mgmt = Resume.query.filter_by(is_sample=True, sample_type='management').count()
    sample_general = Resume.query.filter_by(is_sample=True, sample_type='general').count()

    return jsonify(
        success=True,
        stats={
            'total_users': total_users,
            'total_resumes': total_resumes,
            'total_uploads': total_uploads,
            'total_applications': total_applications,
            'submitted_applications': submitted,
            'accepted_applications': accepted,
            'samples': {
                'it': sample_it,
                'management': sample_mgmt,
                'general': sample_general,
            }
        }
    )
