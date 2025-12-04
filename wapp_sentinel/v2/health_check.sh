#!/bin/bash

# Health Check Script for Napoleon WhatsApp Sentinel

set -e

echo "🔍 Napoleon WhatsApp Sentinel - Health Check"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Docker Compose services are not running${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo "📦 Container Status:"
echo "-------------------"
docker-compose ps

echo ""
echo "🔍 Service Health Checks:"
echo "------------------------"

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check RabbitMQ
echo -n "RabbitMQ: "
if docker-compose exec -T rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check API
echo -n "API (FastAPI): "
if curl -f http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Unhealthy${NC}"
fi

# Check AI Agent Worker
echo -n "AI Agent Worker: "
if docker-compose ps ai_agent_worker | grep -q "Up"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

# Check Green API Worker
echo -n "Green API Worker: "
if docker-compose ps greenapi_worker | grep -q "Up"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

# Check Order Processor Worker
echo -n "Order Processor Worker: "
if docker-compose ps order_processor_worker | grep -q "Up"; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

echo ""
echo "📊 RabbitMQ Queues:"
echo "------------------"
docker-compose exec -T rabbitmq rabbitmqctl list_queues name messages consumers 2>/dev/null | grep -E "(greenapi_queue|incoming_interactions|ai_agent_queue|order_processor_queue)" || echo "No queues found"

echo ""
echo "💾 Database Connection:"
echo "----------------------"
if docker-compose exec -T api python -c "from app.database.database import engine; engine.connect(); print('✓ Database connected successfully')" 2>/dev/null; then
    echo -e "${GREEN}✓ Connection OK${NC}"
else
    echo -e "${RED}✗ Connection Failed${NC}"
fi

echo ""
echo "📈 Resource Usage:"
echo "-----------------"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep napoleon

echo ""
echo "🔗 Useful URLs:"
echo "--------------"
echo "API Documentation: http://localhost:8000/docs"
echo "RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo "Database: postgresql://localhost:5432/napoleon_db"

echo ""
echo "✅ Health check complete!"
