from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import init_redis
from app.api.v1.router import api_router
from app.services.ai_service import AIService
from app.services.communication_service import CommunicationService
from app.services.telegram_startup_service import telegram_startup_service

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Napoleon-Tseh CRM application")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    # Initialize AI service
    ai_service = AIService()
    app.state.ai_service = ai_service
    logger.info("AI service initialized")
    
    # Initialize communication service
    comm_service = CommunicationService()
    app.state.communication_service = comm_service
    logger.info("Communication service initialized")

    # Initialize and start Telegram bot
    telegram_task = None
    try:
        logger.info("🤖 Telegram bot service initialized (not auto-started)")
        # bot_result = await telegram_startup_service.start_bot()
        app.state.telegram_service = telegram_startup_service
        
        # if bot_result.get("success"):
        #     logger.info(f"✅ Telegram bot started in {bot_result.get('mode')} mode")
        #     if bot_result.get("webhook_url"):
        #         logger.info(f"🔗 Webhook URL: {bot_result.get('webhook_url')}")
        # else:
        #     logger.error(f"❌ Failed to start Telegram bot: {bot_result.get('error')}")
        logger.info("💡 Use POST /api/v1/webhooks/telegram/start_bot to start the bot manually")
    except Exception as e:
        logger.error(f"❌ Error initializing Telegram bot service: {e}")
        # Don't fail the entire app if bot fails to start
    
    yield
    
    # Cleanup on shutdown
    try:
        logger.info("🛑 Shutting down Telegram bot...")
        if hasattr(app.state, 'telegram_service'):
            # Stop the bot gracefully using the new method
            try:
                await app.state.telegram_service.stop_bot()
                logger.info("✅ Telegram bot stopped successfully")
            except Exception as stop_error:
                logger.warning(f"Warning during bot shutdown: {stop_error}")
    except Exception as e:
        logger.error(f"Error shutting down Telegram bot: {e}")
    
    logger.info("Shutting down Napoleon-Tseh CRM application")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Enabled Napoleon-Tseh CRM System",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly in production
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    ) 