"""Phase 2: agents, evms_snapshots, geofence_zones

Revision ID: 002
Revises: 001
Create Date: 2026-03-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # ── agent_conversations ────────────────────────────────────────────────
    op.create_table(
        "agent_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_type", sa.Enum("gongsa", "pumjil", "anjeon", "gumu", name="agent_type"), nullable=False),
        sa.Column("title",  sa.String(200), nullable=True),
        sa.Column("status", sa.Enum("active", "closed", name="conversation_status"), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_conversations_project", "agent_conversations", ["project_id"])
    op.create_index("ix_agent_conversations_user",    "agent_conversations", ["user_id"])

    # ── agent_messages ─────────────────────────────────────────────────────
    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role",     sa.String(20),  nullable=False),
        sa.Column("content",  sa.Text,        nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_proactive", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_agent_messages_conversation", "agent_messages", ["conversation_id"])

    # ── evms_snapshots ─────────────────────────────────────────────────────
    op.create_table(
        "evms_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id",       postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("snapshot_date",    sa.Date, nullable=False, index=True),
        sa.Column("total_budget",     sa.Float, nullable=True),
        sa.Column("planned_progress", sa.Float, nullable=True),
        sa.Column("actual_progress",  sa.Float, nullable=True),
        sa.Column("pv",  sa.Float, nullable=True),
        sa.Column("ev",  sa.Float, nullable=True),
        sa.Column("ac",  sa.Float, nullable=True),
        sa.Column("spi", sa.Float, nullable=True),
        sa.Column("cpi", sa.Float, nullable=True),
        sa.Column("eac", sa.Float, nullable=True),
        sa.Column("etc", sa.Float, nullable=True),
        sa.Column("notes",       sa.Text, nullable=True),
        sa.Column("detail_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_evms_snapshots_project_date", "evms_snapshots", ["project_id", "snapshot_date"])

    # ── geofence_zones ─────────────────────────────────────────────────────
    op.create_table(
        "geofence_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id",  postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name",        sa.String(100), nullable=False),
        sa.Column("zone_type",   sa.String(50),  nullable=False),
        sa.Column("coordinates", postgresql.JSONB, nullable=False),
        sa.Column("radius_m",    sa.Float, nullable=True),
        sa.Column("is_active",   sa.Boolean, server_default="true", nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_geofence_zones_project", "geofence_zones", ["project_id"])


def downgrade():
    op.drop_table("geofence_zones")
    op.drop_table("evms_snapshots")
    op.drop_table("agent_messages")
    op.drop_table("agent_conversations")
    op.execute("DROP TYPE IF EXISTS agent_type")
    op.execute("DROP TYPE IF EXISTS conversation_status")
