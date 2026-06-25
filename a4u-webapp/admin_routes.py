import os
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, session, current_app
from models import db, User, ResumeTemplate, UploadedFile, SchemaMigration, DailyUsage
from sqlalchemy import text, inspect

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# ── 인증 ─────────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify(success=False, message='인증이 필요합니다.'), 401
        return f(*args, **kwargs)
    return decorated

def demo_mode_blocked(f):
    """데모 모드일 경우 쓰기 작업을 차단하는 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('mode') == 'DEMO':
            return jsonify(success=False, status="blocked", message="데모 모드에서는 관리자 작업을 수행할 수 없습니다."), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        session.permanent = True
        return jsonify(success=True, message='로그인 성공')
    return jsonify(success=False, message='비밀번호가 올바르지 않습니다.'), 401


@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    return jsonify(success=True)


@admin_bp.route('/check', methods=['GET'])
def admin_check():
    return jsonify(authenticated=bool(session.get('is_admin')))


# ── 통계 ─────────────────────────────────────────────────────────────

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    total_users = User.query.count()
    active_users = User.query.filter_by(status='active').count()
    total_files = UploadedFile.query.count()
    total_templates = ResumeTemplate.query.filter_by(is_active=True).count()
    total_migrations = SchemaMigration.query.filter_by(status='applied').count()

    from sqlalchemy import func
    from datetime import timedelta
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_users_week = User.query.filter(User.created_at >= week_ago).count()
    new_files_week = UploadedFile.query.filter(UploadedFile.uploaded_at >= week_ago).count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # [수정 2026-06-25] 일일 사용량 현황 추가
    import os as _os
    daily_limit = int(_os.environ.get('DAILY_API_LIMIT', '100'))
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    today_row = DailyUsage.query.filter_by(date=today_str).first()
    today_count = today_row.count if today_row else 0
    recent_usage = [u.to_dict() for u in DailyUsage.query.order_by(DailyUsage.date.desc()).limit(7).all()]

    return jsonify(
        total_users=total_users,
        active_users=active_users,
        total_files=total_files,
        total_templates=total_templates,
        total_migrations=total_migrations,
        new_users_week=new_users_week,
        new_files_week=new_files_week,
        recent_users=[u.to_dict() for u in recent_users],
        daily_usage=dict(today=today_count, limit=daily_limit, recent=recent_usage)
    )


# ── 회원 관리 ─────────────────────────────────────────────────────────

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    from models import Resume
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    query = User.query
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    users_data = []
    for u in pagination.items:
        d = u.to_dict()
        d['resume_count'] = Resume.query.filter_by(user_id=u.id, is_sample=False).count()
        users_data.append(d)

    return jsonify(
        users=users_data,
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())


@admin_bp.route('/users', methods=['POST'])
@admin_required
@demo_mode_blocked
def create_user():
    data = request.get_json()
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify(success=False, message='이미 사용 중인 이메일입니다.'), 400
    user = User(
        email=data.get('email'),
        name=data.get('name'),
        is_admin=data.get('is_admin', False),
        status=data.get('status', 'active')
    )
    user.set_password(data.get('password', 'changeme123'))
    db.session.add(user)
    db.session.commit()
    return jsonify(success=True, user=user.to_dict()), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
@demo_mode_blocked
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return jsonify(success=False, message='이미 사용 중인 이메일입니다.'), 400
        user.email = data['email']
    if 'status' in data:
        user.status = data['status']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, user=user.to_dict())


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
@demo_mode_blocked
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(success=True)


# ── 이력서 템플릿 관리 ────────────────────────────────────────────────

@admin_bp.route('/templates', methods=['GET'])
@admin_required
def list_templates():
    templates = ResumeTemplate.query.order_by(ResumeTemplate.created_at.desc()).all()
    return jsonify(templates=[t.to_dict() for t in templates])


@admin_bp.route('/templates/<int:template_id>', methods=['GET'])
@admin_required
def get_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    return jsonify(t.to_dict())


@admin_bp.route('/templates', methods=['POST'])
@admin_required
@demo_mode_blocked
def create_template():
    data = request.get_json()
    t = ResumeTemplate(
        name=data.get('name'),
        description=data.get('description', ''),
        category=data.get('category', 'general'),
        html_content=data.get('html_content', ''),
        thumbnail_url=data.get('thumbnail_url', ''),
        is_active=data.get('is_active', True)
    )
    db.session.add(t)
    db.session.commit()
    return jsonify(success=True, template=t.to_dict()), 201


@admin_bp.route('/templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    data = request.get_json()
    for field in ['name', 'description', 'category', 'html_content', 'thumbnail_url', 'is_active']:
        if field in data:
            setattr(t, field, data[field])
    t.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(success=True, template=t.to_dict())


@admin_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@admin_required
@demo_mode_blocked
def delete_template(template_id):
    t = ResumeTemplate.query.get_or_404(template_id)
    # 파일 삭제
    if t.file_path and os.path.exists(t.file_path):
        try:
            os.remove(t.file_path)
        except:
            pass
    db.session.delete(t)
    db.session.commit()
    return jsonify(success=True)


@admin_bp.route('/templates/<int:template_id>/upload', methods=['POST'])
@admin_required
@demo_mode_blocked
def upload_template_file(template_id):
    """PDF/WORD 파일 업로드 및 템플릿 등록"""
    from werkzeug.utils import secure_filename
    
    t = ResumeTemplate.query.get_or_404(template_id)
    
    if 'file' not in request.files:
        return jsonify(success=False, message='파일이 업로드되지 않았습니다.'), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message='파일을 선택해주세요.'), 400
    
    # 파일 타입 검증 (PDF, DOCX만 허용)
    allowed_extensions = {'pdf', 'docx'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return jsonify(success=False, message='PDF 또는 WORD 파일만 업로드 가능합니다.'), 400
    
    # uploads 디렉토리 생성
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'templates')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 파일명 안전화
    filename = secure_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{template_id}_{filename}"
    filepath = os.path.join(upload_dir, filename)
    
    # 기존 파일 삭제
    if t.file_path and os.path.exists(t.file_path):
        try:
            os.remove(t.file_path)
        except:
            pass
    
    # 파일 저장
    file.save(filepath)
    
    # DB 업데이트
    t.file_path = filepath
    t.file_type = file_ext
    t.original_filename = secure_filename(file.filename)
    t.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify(success=True, message='파일이 업로드되었습니다.', template=t.to_dict())


@admin_bp.route('/templates/<int:template_id>/file', methods=['GET'])
@admin_required
def get_template_file(template_id):
    """템플릿 파일 다운로드/미리보기"""
    from flask import send_file
    
    t = ResumeTemplate.query.get_or_404(template_id)
    
    if not t.file_path or not os.path.exists(t.file_path):
        return jsonify(success=False, message='파일을 찾을 수 없습니다.'), 404
    
    return send_file(
        t.file_path,
        as_attachment=False,
        mimetype='application/pdf' if t.file_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


# ── 이력서 관리 ──────────────────────────────────────────────────────

@admin_bp.route('/resumes', methods=['GET'])
@admin_required
def list_all_resumes():
    from models import Resume
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    sample_filter = request.args.get('is_sample', '')

    query = Resume.query
    if search:
        query = query.filter(Resume.title.ilike(f'%{search}%'))
    if sample_filter == 'true':
        query = query.filter_by(is_sample=True)
    elif sample_filter == 'false':
        query = query.filter_by(is_sample=False)

    pagination = query.order_by(Resume.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    resumes_data = []
    for r in pagination.items:
        d = r.to_dict()
        # 작성자 이름 추가
        if r.user_id:
            user = User.query.get(r.user_id)
            d['author_name'] = user.name if user else '알 수 없음'
        else:
            d['author_name'] = '시스템'
        resumes_data.append(d)

    return jsonify(
        resumes=resumes_data,
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/resumes/<int:resume_id>', methods=['DELETE'])
@admin_required
@demo_mode_blocked
def delete_resume(resume_id):
    from models import Resume
    r = Resume.query.get_or_404(resume_id)
    if r.is_sample:
        return jsonify(success=False, message='샘플 이력서는 삭제할 수 없습니다.'), 400
    db.session.delete(r)
    db.session.commit()
    return jsonify(success=True)


# ── 파일 관리 ─────────────────────────────────────────────────────────

@admin_bp.route('/files', methods=['GET'])
@admin_required
def list_files():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')

    query = UploadedFile.query
    if search:
        query = query.filter(UploadedFile.original_name.ilike(f'%{search}%'))

    pagination = query.order_by(UploadedFile.uploaded_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        files=[f.to_dict() for f in pagination.items],
        total=pagination.total,
        pages=pagination.pages,
        current_page=page
    )


@admin_bp.route('/files/<int:file_id>', methods=['DELETE'])
@admin_required
@demo_mode_blocked
def delete_file(file_id):
    f = UploadedFile.query.get_or_404(file_id)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, f.saved_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(f)
    db.session.commit()
    return jsonify(success=True)


# ── AI 스키마 콘솔 ────────────────────────────────────────────────────

@admin_bp.route('/schema/tables', methods=['GET'])
@admin_required
def get_schema():
    inspector = inspect(db.engine)
    tables = {}
    for table_name in inspector.get_table_names():
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col.get('nullable', True)
            })
        tables[table_name] = columns
    return jsonify(tables=tables)


@admin_bp.route('/schema/generate', methods=['POST'])
@admin_required
def generate_migration():
    data = request.get_json()
    natural_language = data.get('description', '')

    gemini_key = os.environ.get('GEMINI_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    method = 'rule-based'
    sql = ''

    if gemini_key:
        sql = _call_gemini_for_sql(natural_language, db)
        if not sql.startswith('-- Gemini 오류'):
            method = 'gemini'
        else:
            error_comment = sql
            sql = _rule_based_sql_parser(natural_language, db)
            sql = f"-- Gemini 호출 실패, 규칙 기반 생성으로 전환\n{error_comment}\n\n{sql}"
            method = 'rule-based'
    elif openai_key:
        sql = _call_openai_for_sql(natural_language, db)
        if not sql.startswith('-- OpenAI 오류'):
            method = 'openai'
        else:
            error_comment = sql
            sql = _rule_based_sql_parser(natural_language, db)
            sql = f"-- OpenAI 호출 실패, 규칙 기반 생성으로 전환\n{error_comment}\n\n{sql}"
            method = 'rule-based'
    else:
        sql = _rule_based_sql_parser(natural_language, db)
        method = 'rule-based'

    return jsonify(
        success=True,
        natural_language=natural_language,
        suggested_sql=sql,
        ai_used=(method in ('gemini', 'openai')),
        method=method
    )


@admin_bp.route('/schema/apply', methods=['POST'])
@admin_required
@demo_mode_blocked
def apply_migration():
    data = request.get_json()
    sql_query = data.get('sql_query', '').strip()
    description = data.get('description', '자동 마이그레이션')
    natural_language = data.get('natural_language', '')

    if not sql_query:
        return jsonify(success=False, message='SQL이 비어 있습니다.'), 400

    migration = SchemaMigration(
        description=description,
        natural_language=natural_language,
        sql_query=sql_query,
        applied_by='admin'
    )

    try:
        with db.engine.connect() as conn:
            for statement in sql_query.split(';'):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        migration.status = 'applied'
        migration.applied_at = datetime.now(timezone.utc)
        db.session.add(migration)
        db.session.commit()
        return jsonify(success=True, migration=migration.to_dict())
    except Exception as e:
        migration.status = 'failed'
        migration.error_message = str(e)
        db.session.add(migration)
        db.session.commit()
        return jsonify(success=False, message=str(e), migration=migration.to_dict()), 500


@admin_bp.route('/schema/migrations', methods=['GET'])
@admin_required
def list_migrations():
    migrations = SchemaMigration.query.order_by(SchemaMigration.created_at.desc()).limit(50).all()
    return jsonify(migrations=[m.to_dict() for m in migrations])


def _get_schema_str(db_instance) -> str:
    """현재 DB 스키마를 문자열로 반환"""
    try:
        inspector_obj = inspect(db_instance.engine)
        schema_info = {}
        for table_name in inspector_obj.get_table_names():
            cols = [f"{c['name']} {c['type']}" for c in inspector_obj.get_columns(table_name)]
            schema_info[table_name] = cols
        return json.dumps(schema_info, ensure_ascii=False, indent=2)
    except Exception:
        return '{}'


def _build_ai_prompt(description: str, schema_str: str) -> str:
    return f"""현재 SQLite 데이터베이스 스키마:
{schema_str}

다음 요청을 SQLite DDL/DML 문으로 변환해주세요:
"{description}"

규칙:
- SQLite 문법을 사용하세요 (ALTER TABLE ... ADD COLUMN, CREATE TABLE, CREATE INDEX 등)
- SQL 문만 반환하고 설명 텍스트는 생략하세요
- 세미콜론(;)으로 끝내세요
- 여러 문장이면 줄바꿈으로 구분하세요"""


def _call_gemini_for_sql(description: str, db_instance) -> str:
    gemini_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_key:
        return '-- Gemini 오류: GEMINI_API_KEY 없음'
    try:
        from google import genai
        from google.genai import types
        schema_str = _get_schema_str(db_instance)
        prompt = _build_ai_prompt(description, schema_str)
        client = genai.Client(api_key=gemini_key)
        models_to_try = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash']
        last_error = None
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(max_output_tokens=600, temperature=0.2)
                )
                sql = response.text.strip()
                # 마크다운 코드블록 제거
                if sql.startswith('```'):
                    sql = '\n'.join(sql.split('\n')[1:])
                if sql.endswith('```'):
                    sql = '\n'.join(sql.split('\n')[:-1])
                return sql.strip()
            except Exception as e:
                last_error = e
                continue
        return f'-- Gemini 오류: {last_error}'
    except Exception as e:
        return f'-- Gemini 오류: {e}'


def _call_openai_for_sql(description: str, db_instance) -> str:
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        return '-- OpenAI 오류: OPENAI_API_KEY 없음'
    try:
        import openai
        schema_str = _get_schema_str(db_instance)
        prompt = _build_ai_prompt(description, schema_str)
        client = openai.OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=600,
            temperature=0.2
        )
        sql = response.choices[0].message.content.strip()
        if sql.startswith('```'):
            sql = '\n'.join(sql.split('\n')[1:])
        if sql.endswith('```'):
            sql = '\n'.join(sql.split('\n')[:-1])
        return sql.strip()
    except Exception as e:
        return f'-- OpenAI 오류: {e}'


def _rule_based_sql_parser(description: str, db_instance=None) -> str:
    """
    한국어 자연어 → SQLite DDL 규칙 기반 파서
    지원: ADD COLUMN / DROP COLUMN / RENAME COLUMN / CREATE TABLE / DROP TABLE / CREATE INDEX
    """
    import re

    text = description.strip()

    # ── 현재 DB 테이블 목록 로드 ─────────────────────────────────────
    known_tables = []
    if db_instance:
        try:
            insp = inspect(db_instance.engine)
            known_tables = insp.get_table_names()
        except Exception:
            pass

    # re.ASCII 사용: \w = [a-zA-Z0-9_] 만 매칭, 한글 제외
    ASCII = re.ASCII

    # ── 테이블명 추출 ─────────────────────────────────────────────────
    found_table = None
    # 1) 알려진 테이블명과 직접 매칭 (ASCII 모드: 한글 suffix 분리)
    for t in known_tables:
        if re.search(rf'\b{re.escape(t)}\b', text, re.IGNORECASE | ASCII):
            found_table = t
            break
    # 2) "X 테이블", "X에", "X의" 패턴 (한글 경계를 ASCII \b로 처리)
    if not found_table:
        m = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:테이블|에|의)', text, ASCII)
        if m:
            found_table = m.group(1)

    table = found_table or 'TABLE_NAME'

    # ── SQL 타입 추출 ─────────────────────────────────────────────────
    # VARCHAR(...) 는 \b가 ) 뒤에서 작동 안 하므로 분리 처리
    type_rx = re.compile(
        r'(VARCHAR\s*\(\s*\d+\s*\))'                              # VARCHAR(n)
        r'|\b(TEXT|INTEGER|INT|REAL|FLOAT|DOUBLE|'
        r'BOOLEAN|BOOL|DATETIME|DATE|TIMESTAMP|BLOB|NUMERIC)\b',
        re.IGNORECASE | ASCII
    )
    type_match = type_rx.search(text)
    sql_type = None
    if type_match:
        sql_type = (type_match.group(1) or type_match.group(2)).upper()

    # 한국어 타입 키워드
    if not sql_type:
        if any(k in text for k in ['문자열', '문자', '텍스트', '스트링']):
            sql_type = 'TEXT'
        elif any(k in text for k in ['정수형', '정수', '숫자', '번호', '카운트']):
            sql_type = 'INTEGER'
        elif any(k in text for k in ['실수', '소수', '부동']):
            sql_type = 'REAL'
        elif any(k in text for k in ['날짜시간', '타임스탬프', '일시']):
            sql_type = 'DATETIME'
        elif '날짜' in text:
            sql_type = 'DATE'
        elif any(k in text for k in ['불리언', '불린', '논리', '참거짓']):
            sql_type = 'BOOLEAN'
        else:
            sql_type = 'TEXT'

    # ── 제약조건 추출 ─────────────────────────────────────────────────
    not_null = bool(re.search(r'NOT\s*NULL|필수|NULL\s*불가|NULL\s*아님', text, re.IGNORECASE))
    unique   = bool(re.search(r'\bUNIQUE\b|고유|유일|중복\s*불가', text, re.IGNORECASE | ASCII))

    default_val = None
    dm = re.search(r'\bDEFAULT\s+([^\s,;]+)', text, re.IGNORECASE | ASCII)
    if dm:
        default_val = dm.group(1)
    else:
        dm2 = re.search(r'기본\s*값?\s*[:=]?\s*(\S+)', text)
        if dm2:
            raw = dm2.group(1)
            # 숫자나 따옴표로 시작하는 경우만 기본값으로 인정
            if re.match(r'^[\d\'"]', raw):
                default_val = raw

    constraints = ''
    if not_null:
        constraints += ' NOT NULL'
    if unique:
        constraints += ' UNIQUE'
    if default_val:
        constraints += f' DEFAULT {default_val}'

    # ── 컬럼명 추출 ──────────────────────────────────────────────────
    SQL_KW = {
        'ALTER', 'TABLE', 'ADD', 'COLUMN', 'DROP', 'CREATE', 'INDEX', 'ON',
        'NOT', 'NULL', 'DEFAULT', 'UNIQUE', 'PRIMARY', 'KEY', 'INTEGER',
        'TEXT', 'VARCHAR', 'REAL', 'BOOLEAN', 'DATETIME', 'DATE', 'INT',
        'FLOAT', 'BLOB', 'TIMESTAMP', 'NUMERIC', 'DOUBLE', 'SELECT', 'FROM',
        'WHERE', 'RENAME', 'TO', 'IF', 'EXISTS', 'AUTOINCREMENT',
        'CURRENT_TIMESTAMP', 'BOOL',
    }
    # 타입 매칭된 단어들도 제외
    type_words = set()
    if type_match:
        type_words = {w.upper() for w in re.split(r'[\s()]', (type_match.group(1) or type_match.group(2))) if re.match(r'[A-Za-z]', w)}

    exclude = SQL_KW | type_words | {t.upper() for t in known_tables}

    # 테이블명 이후 텍스트에서 컬럼명 추출 (더 정확한 위치 기반)
    table_pos = text.lower().find(found_table.lower()) if found_table else 0
    search_text = text[table_pos + len(found_table):] if found_table and table_pos >= 0 else text

    candidates = [w for w in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', search_text, ASCII)
                  if w.upper() not in exclude]
    # 전체 텍스트에서도 시도 (테이블 뒤에 없을 경우 대비)
    if not candidates:
        candidates = [w for w in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', text, ASCII)
                      if w.upper() not in exclude]

    found_col = candidates[0] if candidates else 'column_name'

    # ── 두 번째 컬럼명 (RENAME용) ────────────────────────────────────
    new_col = candidates[1] if len(candidates) > 1 else 'new_column_name'
    # "full_name으로" 패턴: 컬럼명이 한글 조사에 붙어있는 경우
    rename_m = re.search(r'\b([a-zA-Z_][a-zA-Z0-9_]*)(?:으로|로)\b', text, ASCII)
    if rename_m:
        new_col = rename_m.group(1)
    else:
        rename_m2 = re.search(r'(?:->|to\s+)([a-zA-Z_][a-zA-Z0-9_]*)\b', text, re.IGNORECASE | ASCII)
        if rename_m2:
            new_col = rename_m2.group(1)

    # ── 동작 판별 ─────────────────────────────────────────────────────
    is_drop_col    = bool(re.search(r'컬럼\s*삭제|컬럼\s*제거|필드\s*삭제|열\s*삭제|DROP\s+COLUMN', text, re.IGNORECASE))
    is_drop_table  = bool(re.search(r'테이블\s*삭제|테이블\s*제거|DROP\s+TABLE', text, re.IGNORECASE)) and not is_drop_col
    is_rename_col  = bool(re.search(r'이름\s*변경|컬럼명\s*변경|컬럼\s*이름|RENAME', text, re.IGNORECASE))
    is_create_idx  = bool(re.search(r'인덱스|INDEX', text, re.IGNORECASE))
    is_create_tbl  = bool(re.search(r'테이블\s*생성|테이블\s*만들|새\s*테이블|CREATE\s+TABLE', text, re.IGNORECASE)) and not is_drop_col

    # ── SQL 생성 ──────────────────────────────────────────────────────
    header = f'-- 규칙 기반 생성 | 입력: "{description}"\n'

    if is_create_idx:
        idx_name = f'idx_{table}_{found_col}'
        return f'{header}CREATE INDEX {idx_name} ON {table}({found_col});'

    if is_create_tbl:
        return (
            f'{header}'
            f'CREATE TABLE {table} (\n'
            f'  id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            f'  -- 필요한 컬럼을 추가하세요\n'
            f'  created_at DATETIME DEFAULT CURRENT_TIMESTAMP\n'
            f');'
        )

    if is_drop_table:
        return f'{header}DROP TABLE IF EXISTS {table};'

    if is_drop_col:
        return f'{header}ALTER TABLE {table} DROP COLUMN {found_col};'

    if is_rename_col:
        return f'{header}ALTER TABLE {table} RENAME COLUMN {found_col} TO {new_col};'

    # 기본: ADD COLUMN
    return f'{header}ALTER TABLE {table} ADD COLUMN {found_col} {sql_type}{constraints};'
