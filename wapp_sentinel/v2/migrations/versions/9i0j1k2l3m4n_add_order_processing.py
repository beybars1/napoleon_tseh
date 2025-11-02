"""add_order_processing

Revision ID: 9i0j1k2l3m4n
Revises: 8h9i0j1k2l3m
Create Date: 2025-11-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9i0j1k2l3m4n'
down_revision = '8h9i0j1k2l3m'
branch_labels = None
depends_on = None

def upgrade():
    # 1. Создаем таблицу orders
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('message_table', sa.String(length=50), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('order_accepted_date', sa.DateTime(timezone=False), nullable=False),
        sa.Column('estimated_delivery_datetime', sa.DateTime(timezone=False), nullable=True),
        sa.Column('payment_status', sa.Boolean(), nullable=True),
        sa.Column('contact_number_primary', sa.String(length=20), nullable=True),
        sa.Column('contact_number_secondary', sa.String(length=20), nullable=True),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('accepted_by', sa.String(length=100), nullable=True),
        sa.Column('raw_message_text', sa.Text(), nullable=False),
        sa.Column('openai_response', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=True),
        sa.Column('processing_status', sa.String(length=20), server_default='completed', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=False), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_table', 'message_id', name='orders_message_unique')
    )
    
    # Создаем индексы для orders
    op.create_index('idx_orders_chat_id', 'orders', ['chat_id'])
    op.create_index('idx_orders_delivery_datetime', 'orders', ['estimated_delivery_datetime'])
    op.create_index('idx_orders_accepted_date', 'orders', ['order_accepted_date'])
    op.create_index('idx_orders_payment_status', 'orders', ['payment_status'])
    
    # 2. Добавляем колонку order_processed в 3 таблицы
    op.add_column('incoming_message', sa.Column('order_processed', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('outgoing_message', sa.Column('order_processed', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('outgoing_api_message', sa.Column('order_processed', sa.Boolean(), server_default='false', nullable=True))
    
    # Создаем индексы для производительности (partial index на FALSE значения)
    op.create_index('idx_incoming_message_order_processed', 'incoming_message', ['order_processed'], 
                    postgresql_where=sa.text('order_processed = false'))
    op.create_index('idx_outgoing_message_order_processed', 'outgoing_message', ['order_processed'],
                    postgresql_where=sa.text('order_processed = false'))
    op.create_index('idx_outgoing_api_message_order_processed', 'outgoing_api_message', ['order_processed'],
                    postgresql_where=sa.text('order_processed = false'))

def downgrade():
    # Удаляем индексы для order_processed
    op.drop_index('idx_outgoing_api_message_order_processed', table_name='outgoing_api_message')
    op.drop_index('idx_outgoing_message_order_processed', table_name='outgoing_message')
    op.drop_index('idx_incoming_message_order_processed', table_name='incoming_message')
    
    # Удаляем колонки order_processed
    op.drop_column('outgoing_api_message', 'order_processed')
    op.drop_column('outgoing_message', 'order_processed')
    op.drop_column('incoming_message', 'order_processed')
    
    # Удаляем индексы для orders
    op.drop_index('idx_orders_payment_status', table_name='orders')
    op.drop_index('idx_orders_accepted_date', table_name='orders')
    op.drop_index('idx_orders_delivery_datetime', table_name='orders')
    op.drop_index('idx_orders_chat_id', table_name='orders')
    
    # Удаляем таблицу orders
    op.drop_table('orders')
