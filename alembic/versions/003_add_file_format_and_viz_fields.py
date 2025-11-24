"""Add file format and viz fields

Revision ID: 003
Revises: 002
Create Date: 2025-10-30

"""
from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("music_generations", sa.Column("file_format", sa.String(), nullable=True))  # e.g., 'mp3', 'simple_mp4'
    op.add_column("music_generations", sa.Column("instrument_pic", sa.String(), nullable=True))  # Path/URL
    op.add_column("music_generations", sa.Column("instrument_video", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("music_generations", "instrument_video")
    op.drop_column("music_generations", "instrument_pic")
    op.drop_column("music_generations", "file_format")