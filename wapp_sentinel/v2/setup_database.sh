#!/bin/bash
# Helper script for database migrations and seeding

set -e

echo "🔧 Napoleon Tseh - Database Setup Script"
echo "=========================================="
echo ""

# Check if containers are running
if ! docker compose ps | grep -q "napoleon_postgres.*Up"; then
    echo "❌ Error: PostgreSQL container is not running"
    echo "   Run: docker compose up -d"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Run migration
echo "📦 Running database migrations..."
docker compose exec api python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

echo ""

# Check if products exist
PRODUCT_COUNT=$(docker compose exec postgres psql -U napoleon_admin -d postgres -t -c "SELECT COUNT(*) FROM products;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$PRODUCT_COUNT" = "0" ]; then
    echo "🌱 Seeding products table..."
    docker compose exec api python /app/seed_products.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Products seeded successfully"
    else
        echo "❌ Product seeding failed"
        exit 1
    fi
else
    echo "ℹ️  Products table already has $PRODUCT_COUNT products (skipping seed)"
fi

echo ""
echo "🎉 Database setup complete!"
echo ""
echo "📊 Database Summary:"
docker compose exec postgres psql -U napoleon_admin -d postgres -c "
SELECT 
    'Products' as table_name, 
    COUNT(*) as count 
FROM products
UNION ALL
SELECT 
    'Conversations', 
    COUNT(*) 
FROM conversations
UNION ALL
SELECT 
    'Orders', 
    COUNT(*) 
FROM orders;
"

echo ""
echo "✅ Ready to start AI Agent v2!"
