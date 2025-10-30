"""Make chat_id, sender_id, sender_name nullable in whatsapp_notifications

Revision ID: 3c4d5e6f7g8h
Revises: 2b3c4d5e6f7g
Create Date: 2025-10-30 03:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c4d5e6f7g8h'
down_revision = '2b3c4d5e6f7g'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('whatsapp_notifications', 'chat_id', nullable=True)
    op.alter_column('whatsapp_notifications', 'sender_id', nullable=True)
    op.alter_column('whatsapp_notifications', 'sender_name', nullable=True)

def downgrade():
    op.alter_column('whatsapp_notifications', 'chat_id', nullable=False)
    op.alter_column('whatsapp_notifications', 'sender_id', nullable=False)
    op.alter_column('whatsapp_notifications', 'sender_name', nullable=False)
