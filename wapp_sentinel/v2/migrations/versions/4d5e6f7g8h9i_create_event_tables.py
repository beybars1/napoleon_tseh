"""Create tables for WhatsApp event types

Revision ID: 4d5e6f7g8h9i
Revises: 3c4d5e6f7g8h
Create Date: 2025-10-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4d5e6f7g8h9i'
down_revision = '3c4d5e6f7g8h'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'outgoing_api_message',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer()),
        sa.Column('id_message', sa.String()),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('chat_id', sa.String()),
        sa.Column('sender', sa.String()),
        sa.Column('chat_name', sa.String()),
        sa.Column('sender_name', sa.String()),
        sa.Column('text', sa.Text()),
        sa.Column('raw_data', postgresql.JSONB()),
    )
    op.create_table(
        'incoming_message',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer()),
        sa.Column('id_message', sa.String()),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('chat_id', sa.String()),
        sa.Column('sender', sa.String()),
        sa.Column('chat_name', sa.String()),
        sa.Column('sender_name', sa.String()),
        sa.Column('type_message', sa.String()),
        sa.Column('deleted_message_type', sa.String()),
        sa.Column('deleted_message_stanza_id', sa.String()),
        sa.Column('raw_data', postgresql.JSONB()),
    )
    op.create_table(
        'incoming_call',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer()),
        sa.Column('from_id', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('id_message', sa.String()),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('raw_data', postgresql.JSONB()),
    )
    op.create_table(
        'outgoing_message',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer()),
        sa.Column('id_message', sa.String()),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('chat_id', sa.String()),
        sa.Column('sender', sa.String()),
        sa.Column('chat_name', sa.String()),
        sa.Column('sender_name', sa.String()),
        sa.Column('text', sa.Text()),
        sa.Column('raw_data', postgresql.JSONB()),
    )
    op.create_table(
        'outgoing_message_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('receipt_id', sa.Integer()),
        sa.Column('chat_id', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('id_message', sa.String()),
        sa.Column('send_by_api', sa.Boolean()),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('raw_data', postgresql.JSONB()),
    )

def downgrade():
    op.drop_table('outgoing_api_message')
    op.drop_table('incoming_message')
    op.drop_table('incoming_call')
    op.drop_table('outgoing_message')
    op.drop_table('outgoing_message_status')
