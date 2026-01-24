import os
from typing import Iterable
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Row

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:admin@localhost:5432/napoleon-sentinel-db",
)

TABLE_COLUMNS = {
    "outgoing_api_message": ["timestamp"],
    "incoming_message": ["timestamp"],
    "incoming_call": ["timestamp"],
    "outgoing_message": ["timestamp"],
    "outgoing_message_status": ["timestamp"],
    "orders": [
        "order_accepted_date",
        "estimated_delivery_datetime",
        "created_at",
        "updated_at",
    ],
    "conversations": ["created_at", "updated_at", "completed_at"],
    "conversation_messages": ["timestamp"],
    "ai_generated_orders": ["estimated_delivery_datetime", "created_at", "confirmed_at"],
    "products": ["created_at", "updated_at"],
}


def sample_rows(table: str, columns: Iterable[str], limit: int = 5) -> Iterable[Row]:
    column_sql = ", ".join([f"{col}" for col in columns])
    sql = text(
        f"SELECT id, {column_sql} FROM {table} "
        f"WHERE {columns[0]} IS NOT NULL ORDER BY id DESC LIMIT :limit"
    )
    with engine.begin() as conn:
        return list(conn.execute(sql, {"limit": limit}))


def check_timezone(row: Row, column: str) -> str:
    value = row._mapping.get(column)
    if value is None:
        return "NULL"
    tzinfo = getattr(value, "tzinfo", None)
    if tzinfo is None:
        return "naive"
    offset = tzinfo.utcoffset(value)
    if offset is None:
        return "naive"
    if offset.total_seconds() == 0:
        return "UTC"
    hours = int(offset.total_seconds() / 3600)
    return f"offset_{hours:+d}"


def main() -> None:
    print("Timestamp verification (expect UTC-aware timestamptz)")
    print(f"DATABASE_URL: {DATABASE_URL}")
    print("-")

    for table, columns in TABLE_COLUMNS.items():
        print(f"Table: {table}")
        try:
            rows = sample_rows(table, columns)
            if not rows:
                print("  no rows")
                continue
            for row in rows:
                flags = []
                for col in columns:
                    flags.append(f"{col}={check_timezone(row, col)}")
                print(f"  id={row._mapping.get('id')} | " + ", ".join(flags))
        except Exception as exc:
            print(f"  error: {exc}")
        print("-")


if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    main()
