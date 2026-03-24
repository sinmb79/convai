"""Initial schema with all Phase 1 tables

Revision ID: 001
Revises:
Create Date: 2026-03-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # users
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.Enum('admin', 'site_manager', 'supervisor', 'worker', name='user_role'), nullable=False, server_default='site_manager'),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('kakao_user_key', sa.String(100), unique=True, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_kakao_user_key', 'users', ['kakao_user_key'])

    # client_profiles (before projects since projects FK to this)
    op.create_table(
        'client_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('report_frequency', sa.String(20), nullable=False, server_default='weekly'),
        sa.Column('template_config', JSONB, nullable=True),
        sa.Column('contact_info', JSONB, nullable=True),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # projects
    op.create_table(
        'projects',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('client_profile_id', UUID(as_uuid=True), sa.ForeignKey('client_profiles.id'), nullable=True),
        sa.Column('construction_type', sa.Enum('road', 'sewer', 'water', 'bridge', 'site_work', 'other', name='construction_type'), nullable=False, server_default='other'),
        sa.Column('contract_amount', sa.BigInteger, nullable=True),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('location_address', sa.Text, nullable=True),
        sa.Column('location_lat', sa.Float, nullable=True),
        sa.Column('location_lng', sa.Float, nullable=True),
        sa.Column('weather_grid_x', sa.Integer, nullable=True),
        sa.Column('weather_grid_y', sa.Integer, nullable=True),
        sa.Column('status', sa.Enum('planning', 'active', 'suspended', 'completed', name='project_status'), nullable=False, server_default='planning'),
        sa.Column('owner_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_projects_code', 'projects', ['code'])

    # wbs_items
    op.create_table(
        'wbs_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('wbs_items.id'), nullable=True),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('level', sa.Integer, nullable=False, server_default='1'),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('design_qty', sa.Float, nullable=True),
        sa.Column('unit_price', sa.Float, nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # tasks
    op.create_table(
        'tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wbs_item_id', UUID(as_uuid=True), sa.ForeignKey('wbs_items.id'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('planned_start', sa.Date, nullable=True),
        sa.Column('planned_end', sa.Date, nullable=True),
        sa.Column('actual_start', sa.Date, nullable=True),
        sa.Column('actual_end', sa.Date, nullable=True),
        sa.Column('progress_pct', sa.Float, nullable=False, server_default='0'),
        sa.Column('is_milestone', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_critical', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('early_start', sa.Date, nullable=True),
        sa.Column('early_finish', sa.Date, nullable=True),
        sa.Column('late_start', sa.Date, nullable=True),
        sa.Column('late_finish', sa.Date, nullable=True),
        sa.Column('total_float', sa.Integer, nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # task_dependencies
    op.create_table(
        'task_dependencies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('predecessor_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('successor_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dependency_type', sa.Enum('FS', 'SS', 'FF', 'SF', name='dependency_type'), nullable=False, server_default='FS'),
        sa.Column('lag_days', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # daily_reports
    op.create_table(
        'daily_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_date', sa.Date, nullable=False),
        sa.Column('weather_summary', sa.String(100), nullable=True),
        sa.Column('temperature_high', sa.Float, nullable=True),
        sa.Column('temperature_low', sa.Float, nullable=True),
        sa.Column('workers_count', JSONB, nullable=True),
        sa.Column('equipment_list', JSONB, nullable=True),
        sa.Column('work_content', sa.Text, nullable=True),
        sa.Column('issues', sa.Text, nullable=True),
        sa.Column('input_source', sa.Enum('kakao', 'web', 'api', name='input_source'), nullable=False, server_default='web'),
        sa.Column('raw_kakao_input', sa.Text, nullable=True),
        sa.Column('ai_generated', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.Enum('draft', 'confirmed', 'submitted', name='daily_report_status'), nullable=False, server_default='draft'),
        sa.Column('confirmed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pdf_s3_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_daily_reports_date', 'daily_reports', ['report_date'])

    # daily_report_photos
    op.create_table(
        'daily_report_photos',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('daily_report_id', UUID(as_uuid=True), sa.ForeignKey('daily_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('s3_key', sa.String(500), nullable=False),
        sa.Column('caption', sa.String(200), nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # reports (weekly/monthly)
    op.create_table(
        'reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_type', sa.Enum('weekly', 'monthly', name='report_type'), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('content_json', JSONB, nullable=True),
        sa.Column('ai_draft_text', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('draft', 'reviewed', 'submitted', name='report_status'), nullable=False, server_default='draft'),
        sa.Column('pdf_s3_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # inspection_requests
    op.create_table(
        'inspection_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wbs_item_id', UUID(as_uuid=True), sa.ForeignKey('wbs_items.id'), nullable=True),
        sa.Column('inspection_type', sa.String(50), nullable=False),
        sa.Column('requested_date', sa.Date, nullable=False),
        sa.Column('location_detail', sa.String(200), nullable=True),
        sa.Column('checklist_items', JSONB, nullable=True),
        sa.Column('result', sa.Enum('pass', 'fail', 'conditional_pass', name='inspection_result'), nullable=True),
        sa.Column('inspector_name', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('ai_generated', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('status', sa.Enum('draft', 'sent', 'completed', name='inspection_status'), nullable=False, server_default='draft'),
        sa.Column('pdf_s3_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # quality_tests
    op.create_table(
        'quality_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wbs_item_id', UUID(as_uuid=True), sa.ForeignKey('wbs_items.id'), nullable=True),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('test_date', sa.Date, nullable=False),
        sa.Column('location_detail', sa.String(200), nullable=True),
        sa.Column('design_value', sa.Float, nullable=True),
        sa.Column('measured_value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('result', sa.Enum('pass', 'fail', name='quality_result'), nullable=False),
        sa.Column('lab_name', sa.String(100), nullable=True),
        sa.Column('report_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # weather_data
    op.create_table(
        'weather_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('forecast_date', sa.Date, nullable=False),
        sa.Column('forecast_type', sa.Enum('short_term', 'medium_term', 'observed', name='forecast_type'), nullable=False),
        sa.Column('temperature_high', sa.Float, nullable=True),
        sa.Column('temperature_low', sa.Float, nullable=True),
        sa.Column('precipitation_mm', sa.Float, nullable=True),
        sa.Column('wind_speed_ms', sa.Float, nullable=True),
        sa.Column('weather_code', sa.String(20), nullable=True),
        sa.Column('raw_data', JSONB, nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # weather_alerts
    op.create_table(
        'weather_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('alert_date', sa.Date, nullable=False),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Enum('warning', 'critical', name='alert_severity'), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_acknowledged', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # permit_items
    op.create_table(
        'permit_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permit_type', sa.String(100), nullable=False),
        sa.Column('authority', sa.String(100), nullable=True),
        sa.Column('required', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('deadline', sa.Date, nullable=True),
        sa.Column('status', sa.Enum('not_started', 'submitted', 'in_review', 'approved', 'rejected', name='permit_status'), nullable=False, server_default='not_started'),
        sa.Column('submitted_date', sa.Date, nullable=True),
        sa.Column('approved_date', sa.Date, nullable=True),
        sa.Column('document_s3_key', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # rag_sources
    op.create_table(
        'rag_sources',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('source_type', sa.Enum('kcs', 'law', 'regulation', 'guideline', name='rag_source_type'), nullable=False),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('file_s3_key', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # rag_chunks (with pgvector)
    op.create_table(
        'rag_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('rag_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    # Add vector column separately (pgvector syntax)
    op.execute("ALTER TABLE rag_chunks ADD COLUMN IF NOT EXISTS embedding vector(1024)")
    op.execute("CREATE INDEX IF NOT EXISTS rag_chunks_embedding_idx ON rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # alert_rules
    op.create_table(
        'alert_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('rule_name', sa.String(100), nullable=False),
        sa.Column('condition', JSONB, nullable=True),
        sa.Column('channels', JSONB, nullable=True),
        sa.Column('recipients', JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # work_type_library
    op.create_table(
        'work_type_library',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('weather_constraints', JSONB, nullable=True),
        sa.Column('default_checklist', JSONB, nullable=True),
        sa.Column('is_system', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Seed default work types
    op.execute("""
        INSERT INTO work_type_library (code, name, category, weather_constraints, is_system) VALUES
        ('CONCRETE', '콘크리트 타설', 'concrete', '{"min_temp": 5, "no_rain": true}', true),
        ('REBAR', '철근 공사', 'concrete', '{"no_rain": false}', true),
        ('FORMWORK', '거푸집 공사', 'concrete', '{"max_wind": 14}', true),
        ('HIGH_WORK', '고소 작업', 'safety', '{"max_wind": 10}', true),
        ('CRANE', '크레인 작업', 'safety', '{"max_wind": 10}', true),
        ('EARTHWORK', '토공 (절토/성토)', 'earthwork', '{"no_rain": true}', true),
        ('EXCAVATION', '굴착 공사', 'earthwork', '{"no_rain": true}', true),
        ('PIPE_BURIAL', '관로 매설', 'utilities', '{"no_rain": false}', true),
        ('ASPHALT', '아스팔트 포장', 'road', '{"min_temp": 10, "no_rain": true}', true),
        ('COMPACTION', '다짐 공사', 'earthwork', '{"no_rain": true}', true)
        ON CONFLICT (code) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table('work_type_library')
    op.drop_table('alert_rules')
    op.drop_table('rag_chunks')
    op.drop_table('rag_sources')
    op.drop_table('permit_items')
    op.drop_table('weather_alerts')
    op.drop_table('weather_data')
    op.drop_table('quality_tests')
    op.drop_table('inspection_requests')
    op.drop_table('reports')
    op.drop_table('daily_report_photos')
    op.drop_table('daily_reports')
    op.drop_table('task_dependencies')
    op.drop_table('tasks')
    op.drop_table('wbs_items')
    op.drop_table('projects')
    op.drop_table('client_profiles')
    op.drop_table('users')

    # Drop enums
    for enum in ['user_role', 'construction_type', 'project_status', 'dependency_type',
                 'input_source', 'daily_report_status', 'report_type', 'report_status',
                 'inspection_result', 'inspection_status', 'quality_result',
                 'forecast_type', 'alert_severity', 'permit_status', 'rag_source_type']:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
