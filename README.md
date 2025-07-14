# AI-Enabled CRM System for Cake Pastry Business

A comprehensive Customer Relationship Management (CRM) system designed specifically for cake and pastry businesses, featuring AI-powered multi-channel communication, real-time order management, and advanced analytics.

## 🚀 Features

### 1. Multi-Channel AI Communication
- **WhatsApp Business API** - Automated customer interactions
- **Telegram Bot** - Real-time messaging support
- **SMS Integration** - Via Twilio for broader reach
- **Email Support** - Automated email responses
- **Instagram Integration** - Social media customer engagement

### 2. AI-Powered Conversations
- **OpenAI GPT Integration** - Intelligent customer service
- **Intent Recognition** - Automatically categorize customer requests
- **Sentiment Analysis** - Monitor customer satisfaction
- **Auto-Response System** - 24/7 customer support
- **Human Escalation** - Seamless handoff when needed

### 3. Smart Order Management
- **Real-time Dashboard** - McDonald's-style order tracking
- **Order Status Updates** - Live progress monitoring
- **Kitchen Display System** - Optimized for cooks
- **Delivery Tracking** - Pickup and delivery management
- **Custom Order Processing** - Handle special requests

### 4. Customer Management
- **Unified Customer Profiles** - All channels in one place
- **Order History** - Complete customer journey
- **Preferences Tracking** - Personalized service
- **Loyalty Insights** - Customer value analysis
- **Contact History** - Full conversation records

### 5. Product Catalog
- **Digital Menu** - Complete product database
- **Customization Options** - Sizes, flavors, decorations
- **Inventory Management** - Stock level monitoring
- **Pricing Management** - Dynamic pricing support
- **Product Analytics** - Performance insights

### 6. Analytics & Insights
- **Sales Analytics** - Revenue and order trends
- **Customer Insights** - Behavior analysis
- **Product Performance** - Best-selling items
- **Channel Analytics** - Communication effectiveness
- **AI Performance** - Response quality metrics

### 7. Real-time Features
- **WebSocket Support** - Live updates
- **Push Notifications** - Instant alerts
- **Live Chat** - Real-time conversations
- **Order Tracking** - Live status updates

## 🛠 Technology Stack

### Backend Framework
- **FastAPI** - Modern, high-performance web framework
- **Python 3.12** - Latest Python features
- **Uvicorn** - ASGI server for production

### Database & ORM
- **PostgreSQL 13** - Reliable relational database
- **SQLAlchemy 2.0** - Modern ORM with async support
- **Alembic** - Database migrations
- **asyncpg & psycopg2** - Database drivers

### Background Processing
- **Redis** - Message broker and caching
- **ARQ** - Async task queue for background jobs

### AI & Communication
- **OpenAI GPT** - AI-powered conversations
- **Twilio** - SMS and WhatsApp integration
- **Telegram Bot API** - Telegram messaging
- **Meta WhatsApp Business API** - Official WhatsApp integration

### Development & Deployment
- **Docker & Docker Compose** - Containerization
- **Ruff** - Code linting and formatting
- **Structlog** - Structured logging
- **Pytest** - Testing framework

## 📋 Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd napoleon_tseh
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Install Dependencies
```bash
# Using Make
make install

# Or directly with pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Edit `.env` file with your API keys and configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cake_crm

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Twilio (SMS & WhatsApp)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

# Business Information
BUSINESS_NAME=Your Cake Shop
BUSINESS_PHONE=+1234567890
BUSINESS_EMAIL=info@yourcakeshop.com
```

### 5. Run with Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Run database migrations
docker-compose exec app alembic upgrade head
```

### 6. Run Locally
```bash
# Start the application
make run-app

# In another terminal, start the worker
make run-worker

# Run database migrations
make db-upgrade
```

## 📚 API Documentation

Once the application is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Development

### Database Migrations
```bash
# Create a new migration
make db-revision message="Add new feature"

# Apply migrations
make db-upgrade

# Rollback last migration
make db-downgrade
```

### Code Quality
```bash
# Run linting
make lint

# Format code
make format

# Run tests
make test
```

### Development Tools
When running with Docker Compose, you get access to:

- **pgAdmin**: http://localhost:8080 (admin@cakecrm.com / admin)
- **Redis Commander**: http://localhost:8081

## 🌐 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/create-user` - Create new user (admin only)

### Clients
- `GET /api/v1/clients/` - List all clients
- `GET /api/v1/clients/{id}` - Get client details
- `PUT /api/v1/clients/{id}` - Update client
- `GET /api/v1/clients/stats/summary` - Client statistics

### Products
- `GET /api/v1/products/` - List products
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products/` - Create product
- `PUT /api/v1/products/{id}` - Update product

### Orders
- `GET /api/v1/orders/` - List orders
- `GET /api/v1/orders/{id}` - Get order details
- `PUT /api/v1/orders/{id}/status` - Update order status

### Conversations
- `GET /api/v1/conversations/` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation details
- `PUT /api/v1/conversations/{id}/settings` - Update settings

### Dashboard
- `GET /api/v1/dashboard/overview` - Dashboard overview
- `GET /api/v1/dashboard/orders/active` - Active orders
- `WebSocket /api/v1/dashboard/ws` - Real-time updates

### Webhooks
- `POST /api/v1/webhooks/whatsapp` - WhatsApp webhook
- `POST /api/v1/webhooks/telegram` - Telegram webhook
- `POST /api/v1/webhooks/sms` - SMS webhook

### Analytics
- `GET /api/v1/analytics/sales/overview` - Sales analytics
- `GET /api/v1/analytics/products/performance` - Product performance
- `GET /api/v1/analytics/customers/insights` - Customer insights
- `GET /api/v1/analytics/dashboard/kpis` - Key performance indicators

## 🔐 Security Features

- **JWT Authentication** - Secure API access
- **Role-based Access Control** - Admin/Staff/Cook roles
- **API Rate Limiting** - Prevent abuse
- **Input Validation** - Pydantic models
- **SQL Injection Protection** - SQLAlchemy ORM
- **CORS Configuration** - Cross-origin security

## 📊 Smart Order Dashboard

The system includes a McDonald's-style order dashboard featuring:

- **Real-time Order Queue** - Live order status updates
- **Kitchen Display** - Optimized for cooking staff
- **Time Tracking** - Preparation time monitoring
- **Priority Management** - Urgent order handling
- **WebSocket Updates** - Instant notifications

## 🤖 AI Features

### Conversation AI
- **Natural Language Processing** - Understand customer intent
- **Context Awareness** - Remember conversation history
- **Product Recommendations** - Suggest relevant items
- **Order Assistance** - Help with order placement
- **Multilingual Support** - Multiple language handling

### Analytics AI
- **Customer Behavior Analysis** - Predict preferences
- **Sales Forecasting** - Predict demand
- **Inventory Optimization** - Stock level recommendations
- **Sentiment Monitoring** - Customer satisfaction tracking

## 🚀 Deployment

### Production Deployment
1. Set up production environment variables
2. Configure SSL/TLS certificates
3. Set up reverse proxy (Nginx)
4. Configure monitoring and logging
5. Set up backup strategies

### Environment Variables for Production
```env
DEBUG=False
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/cake_crm
CORS_ORIGINS=["https://yourdomain.com"]
```

## 📈 Monitoring & Logging

- **Structured Logging** - JSON formatted logs
- **Error Tracking** - Comprehensive error handling
- **Performance Monitoring** - Response time tracking
- **Health Checks** - System status monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the code examples

## 🎯 Roadmap

- [ ] Voice call integration (Retell AI)
- [ ] Advanced AI analytics
- [ ] Mobile app support
- [ ] Multi-location support
- [ ] Advanced reporting
- [ ] Integration with POS systems
- [ ] Loyalty program management
- [ ] Advanced inventory management

---

Built with ❤️ for cake and pastry businesses worldwide. # napoleon_tseh
