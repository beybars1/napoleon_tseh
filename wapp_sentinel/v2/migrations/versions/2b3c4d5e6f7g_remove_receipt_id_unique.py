"""Remove unique constraint from receipt_id in whatsapp_notifications

Revision ID: 2b3c4d5e6f7g
Revises: 1a2b3c4d5e6f
Create Date: 2025-10-30 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7g'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

def upgrade():
    # Удаляем уникальное ограничение с receipt_id
    op.drop_constraint('whatsapp_notifications_receipt_id_key', 'whatsapp_notifications', type_='unique')

def downgrade():
    # Возвращаем уникальное ограничение
    op.create_unique_constraint('whatsapp_notifications_receipt_id_key', 'whatsapp_notifications', ['receipt_id'])
