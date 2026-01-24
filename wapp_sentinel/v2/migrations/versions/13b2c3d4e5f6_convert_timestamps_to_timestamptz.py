"""convert timestamps to timestamptz

Revision ID: 13b2c3d4e5f6
Revises: 12a1b2c3d4e5
Create Date: 2026-01-24 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '13b2c3d4e5f6'
down_revision = '12a1b2c3d4e5'
branch_labels = None
depends_on = None


def upgrade():
    # Message event timestamps
    message_tables = [
        'outgoing_api_message',
        'incoming_message',
        'incoming_call',
        'outgoing_message',
        'outgoing_message_status'
    ]
    for table in message_tables:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN timestamp TYPE TIMESTAMPTZ USING timestamp AT TIME ZONE 'Asia/Almaty'"
        )

    # Orders timestamps
    op.execute(
        "ALTER TABLE orders ALTER COLUMN order_accepted_date TYPE TIMESTAMPTZ USING order_accepted_date AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN estimated_delivery_datetime TYPE TIMESTAMPTZ USING estimated_delivery_datetime AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN updated_at TYPE TIMESTAMPTZ USING updated_at AT TIME ZONE 'Asia/Almaty'"
    )


def downgrade():
    # Orders timestamps
    op.execute(
        "ALTER TABLE orders ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN estimated_delivery_datetime TYPE TIMESTAMP WITHOUT TIME ZONE USING estimated_delivery_datetime AT TIME ZONE 'Asia/Almaty'"
    )
    op.execute(
        "ALTER TABLE orders ALTER COLUMN order_accepted_date TYPE TIMESTAMP WITHOUT TIME ZONE USING order_accepted_date AT TIME ZONE 'Asia/Almaty'"
    )

    # Message event timestamps
    message_tables = [
        'outgoing_message_status',
        'outgoing_message',
        'incoming_call',
        'incoming_message',
        'outgoing_api_message'
    ]
    for table in message_tables:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN timestamp TYPE TIMESTAMP WITHOUT TIME ZONE USING timestamp AT TIME ZONE 'Asia/Almaty'"
        )
