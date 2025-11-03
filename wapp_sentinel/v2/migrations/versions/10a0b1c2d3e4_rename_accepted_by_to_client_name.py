"""rename accepted_by to client_name

Revision ID: 10a0b1c2d3e4
Revises: 9i0j1k2l3m4n
Create Date: 2025-11-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10a0b1c2d3e4'
down_revision = '9i0j1k2l3m4n'
branch_labels = None
depends_on = None


def upgrade():
    # Переименовываем колонку accepted_by в client_name
    op.alter_column('orders', 'accepted_by', new_column_name='client_name')


def downgrade():
    # Откатываем изменения
    op.alter_column('orders', 'client_name', new_column_name='accepted_by')
