"""add_products_table_and_v2_fields

Revision ID: 12a1b2c3d4e5
Revises: 11b1c2d3e4f5
Create Date: 2026-01-17 01:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '12a1b2c3d4e5'
down_revision: Union[str, None] = '11b1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create products table
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_per_kg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('fixed_price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sizes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ingredients', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('allergens', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preparation_hours', sa.Integer(), nullable=True, server_default='4'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id')
    )
    op.create_index(op.f('ix_products_product_id'), 'products', ['product_id'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_available'), 'products', ['available'], unique=False)
    
    # Add v2 fields to conversations table
    op.add_column('conversations', sa.Column('last_intent', sa.String(length=50), nullable=True))
    op.add_column('conversations', sa.Column('conversation_stage', sa.String(length=50), nullable=True, server_default='browsing'))
    op.add_column('conversations', sa.Column('clarification_count', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('conversations', sa.Column('flagged_for_human', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('conversations', sa.Column('escalation_reason', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_conversations_flagged_for_human'), 'conversations', ['flagged_for_human'], unique=False)
    
    # Add intent field to conversation_messages table
    op.add_column('conversation_messages', sa.Column('intent', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove intent field from conversation_messages
    op.drop_column('conversation_messages', 'intent')
    
    # Remove v2 fields from conversations
    op.drop_index(op.f('ix_conversations_flagged_for_human'), table_name='conversations')
    op.drop_column('conversations', 'escalation_reason')
    op.drop_column('conversations', 'flagged_for_human')
    op.drop_column('conversations', 'clarification_count')
    op.drop_column('conversations', 'conversation_stage')
    op.drop_column('conversations', 'last_intent')
    
    # Drop products table
    op.drop_index(op.f('ix_products_available'), table_name='products')
    op.drop_index(op.f('ix_products_category'), table_name='products')
    op.drop_index(op.f('ix_products_product_id'), table_name='products')
    op.drop_table('products')
