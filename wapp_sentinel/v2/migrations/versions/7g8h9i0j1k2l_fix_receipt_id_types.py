"""fix_receipt_id_types

Revision ID: 7g8h9i0j1k2l
Revises: 6f7g8h9i0j1k
Create Date: 2025-11-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7g8h9i0j1k2l'
down_revision = '6f7g8h9i0j1k'
branch_labels = None
depends_on = None

def upgrade():
    # Меняем тип receipt_id на String и делаем nullable во всех таблицах
    tables = [
        'outgoing_api_message',
        'incoming_message',
        'incoming_call',
        'outgoing_message',
        'outgoing_message_status'
    ]
    
    for table in tables:
        # Сначала сделаем nullable чтобы избежать проблем с пустыми значениями
        op.alter_column(table, 'receipt_id',
                       existing_type=sa.Integer(),
                       nullable=True)
        # Затем изменим тип на String
        op.alter_column(table, 'receipt_id',
                       existing_type=sa.Integer(),
                       type_=sa.String(),
                       postgresql_using="receipt_id::varchar")

def downgrade():
    tables = [
        'outgoing_api_message',
        'incoming_message',
        'incoming_call',
        'outgoing_message',
        'outgoing_message_status'
    ]
    
    for table in tables:
        op.alter_column(table, 'receipt_id',
                       existing_type=sa.String(),
                       type_=sa.Integer(),
                       postgresql_using="receipt_id::integer")
