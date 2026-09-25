"""add user_sessions table for session tracking, termination, and duration extension

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.Text(), nullable=False),
        sa.Column("code_type", sa.Text(), nullable=False, server_default="time_code"),
        sa.Column("code_value", sa.Text(), nullable=True),
        sa.Column("client_label", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_user_sessions"),
        sa.UniqueConstraint("session_token", name="uq_user_sessions_session_token"),
    )
    op.create_index("ix_user_sessions_id", "user_sessions", ["id"])
    op.create_index("ix_user_sessions_session_token", "user_sessions", ["session_token"])
    op.create_index("ix_user_sessions_status", "user_sessions", ["status"])


def downgrade() -> None:
    op.drop_table("user_sessions")
