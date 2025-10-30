"""Add sender_contact_name, text_message, type_webhook to incoming_message

Revision ID: 5e6f7g8h9i0j
Revises: 4d5e6f7g8h9i
Create Date: 2025-10-31 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5e6f7g8h9i0j'
down_revision = '4d5e6f7g8h9i'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('incoming_message', sa.Column('sender_contact_name', sa.String()))
    op.add_column('incoming_message', sa.Column('text_message', sa.Text()))
    op.add_column('incoming_message', sa.Column('type_webhook', sa.String()))

def downgrade():
    op.drop_column('incoming_message', 'sender_contact_name')
    op.drop_column('incoming_message', 'text_message')
    op.drop_column('incoming_message', 'type_webhook')
