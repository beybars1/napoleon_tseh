"""fix_timestamp_handling

Revision ID: 6f7g8h9i0j1k
Revises: 5e6f7g8h9i0j
Create Date: 2025-11-02 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6f7g8h9i0j1k'
down_revision = '5e6f7g8h9i0j'
branch_labels = None
depends_on = None

def upgrade():
    # Отключаем автоматическую конвертацию timezone для timestamp колонок
    tables_and_columns = [
        ('whatsapp_notifications', ['message_timestamp', 'received_at', 'processed_at']),
        ('outgoing_api_message', ['timestamp']),
        ('incoming_message', ['timestamp']),
        ('incoming_call', ['timestamp']),
        ('outgoing_message', ['timestamp']),
        ('outgoing_message_status', ['timestamp'])
    ]
    
    # 1. Сначала изменяем тип на TIMESTAMP WITH TIME ZONE и конвертируем в UTC
    for table, columns in tables_and_columns:
        for column in columns:
            # Преобразуем в UTC если значение не NULL
            op.execute(f"UPDATE {table} SET {column} = {column} AT TIME ZONE 'UTC' WHERE {column} IS NOT NULL")
            # Изменяем тип на TIMESTAMP WITHOUT TIME ZONE
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITHOUT TIME ZONE")

    # 2. Устанавливаем сессию в UTC
    op.execute("SET timezone TO 'UTC'")

def downgrade():
    # Возвращаем timezone
    tables_and_columns = [
        ('whatsapp_notifications', ['message_timestamp', 'received_at', 'processed_at']),
        ('outgoing_api_message', ['timestamp']),
        ('incoming_message', ['timestamp']),
        ('incoming_call', ['timestamp']),
        ('outgoing_message', ['timestamp']),
        ('outgoing_message_status', ['timestamp'])
    ]
    
    for table, columns in tables_and_columns:
        for column in columns:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE TIMESTAMP WITH TIME ZONE")
