"""Initial WhatsApp notifications schema

Revision ID: 1a2b3c4d5e6f
Create Date: 2025-10-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'whatsapp_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=False),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('raw_data', JSONB, nullable=False),
        sa.Column('processing_status', sa.String(), nullable=False, server_default='new'),
        sa.Column('message_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('receipt_id')
    )
    op.create_index('ix_whatsapp_notifications_chat_id', 'whatsapp_notifications', ['chat_id'])
    op.create_index('ix_whatsapp_notifications_sender_id', 'whatsapp_notifications', ['sender_id'])
    op.create_index('ix_whatsapp_notifications_message_timestamp', 'whatsapp_notifications', ['message_timestamp'])
    op.create_index('ix_whatsapp_notifications_processing_status', 'whatsapp_notifications', ['processing_status'])

def downgrade():
    op.drop_table('whatsapp_notifications')
