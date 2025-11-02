"""remove_whatsapp_notifications_table

Revision ID: 8h9i0j1k2l3m
Revises: 7g8h9i0j1k2l
Create Date: 2025-11-02 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8h9i0j1k2l3m'
down_revision = '7g8h9i0j1k2l'
branch_labels = None
depends_on = None

def upgrade():
    # Удаляем индексы
    op.drop_index('ix_whatsapp_notifications_chat_id', table_name='whatsapp_notifications')
    op.drop_index('ix_whatsapp_notifications_sender_id', table_name='whatsapp_notifications')
    op.drop_index('ix_whatsapp_notifications_message_timestamp', table_name='whatsapp_notifications')
    op.drop_index('ix_whatsapp_notifications_processing_status', table_name='whatsapp_notifications')
    
    # Удаляем таблицу
    op.drop_table('whatsapp_notifications')

def downgrade():
    # Создаем таблицу заново
    op.create_table('whatsapp_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('receipt_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('chat_id', sa.String(), nullable=True),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processing_status', sa.String(), server_default='new', nullable=False),
        sa.Column('message_timestamp', sa.DateTime(timezone=False), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=False), server_default='now()', nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаем индексы
    op.create_index('ix_whatsapp_notifications_processing_status', 'whatsapp_notifications', ['processing_status'])
    op.create_index('ix_whatsapp_notifications_message_timestamp', 'whatsapp_notifications', ['message_timestamp'])
    op.create_index('ix_whatsapp_notifications_sender_id', 'whatsapp_notifications', ['sender_id'])
    op.create_index('ix_whatsapp_notifications_chat_id', 'whatsapp_notifications', ['chat_id'])
