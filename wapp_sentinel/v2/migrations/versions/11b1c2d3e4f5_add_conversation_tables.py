"""add conversation tables for AI agent

Revision ID: 11b1c2d3e4f5
Revises: 10a0b1c2d3e4
Create Date: 2025-11-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '11b1c2d3e4f5'
down_revision = '10a0b1c2d3e4'
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('sender_phone', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),  # active, completed, abandoned
        sa.Column('current_step', sa.String(), nullable=True),  # current node in graph
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversations_chat_id'), 'conversations', ['chat_id'], unique=False)
    op.create_index(op.f('ix_conversations_status'), 'conversations', ['status'], unique=False)

    # Create conversation_messages table
    op.create_table('conversation_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),  # user, assistant, system
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_messages_conversation_id'), 'conversation_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_messages_timestamp'), 'conversation_messages', ['timestamp'], unique=False)

    # Create ai_generated_orders table
    op.create_table('ai_generated_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('client_name', sa.String(), nullable=True),
        sa.Column('client_phone', sa.String(), nullable=True),
        sa.Column('additional_phone', sa.String(), nullable=True),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('estimated_delivery_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_address', sa.String(), nullable=True),
        sa.Column('payment_status', sa.String(), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('validation_status', sa.String(), nullable=False),  # pending, validated, rejected
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_generated_orders_conversation_id'), 'ai_generated_orders', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_ai_generated_orders_chat_id'), 'ai_generated_orders', ['chat_id'], unique=False)
    op.create_index(op.f('ix_ai_generated_orders_validation_status'), 'ai_generated_orders', ['validation_status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ai_generated_orders_validation_status'), table_name='ai_generated_orders')
    op.drop_index(op.f('ix_ai_generated_orders_chat_id'), table_name='ai_generated_orders')
    op.drop_index(op.f('ix_ai_generated_orders_conversation_id'), table_name='ai_generated_orders')
    op.drop_table('ai_generated_orders')
    
    op.drop_index(op.f('ix_conversation_messages_timestamp'), table_name='conversation_messages')
    op.drop_index(op.f('ix_conversation_messages_conversation_id'), table_name='conversation_messages')
    op.drop_table('conversation_messages')
    
    op.drop_index(op.f('ix_conversations_status'), table_name='conversations')
    op.drop_index(op.f('ix_conversations_chat_id'), table_name='conversations')
    op.drop_table('conversations')
