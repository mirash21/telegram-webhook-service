import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio

from config import config, Config
from models import WebhookResponse, ProcessedWebhook
from webhook_handler import handle_webhook, get_webhook_stats, rate_limiter
from ai_agent import get_ai_agent_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration
is_valid, errors = Config.validate()
if not is_valid:
    logger.error(f"Configuration validation failed: {errors}")
    raise ValueError(f"Invalid configuration: {errors}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting webhook service...")
    
    # Startup
    logger.info("Webhook service started successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down webhook service...")

# Create FastAPI app
app = FastAPI(
    title="Telegram Webhook Service",
    description="Microservice for processing Telegram webhooks and forwarding to AI agent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"Incoming {request.method} request to {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Telegram Webhook Service",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    ai_health = await get_ai_agent_health()
    
    return {
        "status": "healthy",
        "service": "Telegram Webhook Service",
        "timestamp": ai_health["timestamp"],
        "components": {
            "ai_agent": ai_health,
            "webhook_processor": get_webhook_stats()
        }
    }

@app.post("/webhook/telegram", response_model=WebhookResponse)
async def telegram_webhook(request: Request):
    """
    Main endpoint for receiving Telegram webhooks
    
    Args:
        request: FastAPI Request object containing webhook data
        
    Returns:
        WebhookResponse with processing results
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        # Read raw body
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request body")
        
        # Process webhook
        processed_webhook = await handle_webhook(request, body)
        
        return WebhookResponse(
            success=True,
            message="Webhook processed successfully",
            processed_data={
                "update_id": processed_webhook.update_id,
                "chat_id": processed_webhook.chat_id,
                "user_id": processed_webhook.user_id,
                "message_type": processed_webhook.message_type,
                "sent_to_ai": processed_webhook.sent_to_ai,
                "ai_response": processed_webhook.ai_response
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/stats")
async def get_statistics():
    """Get service statistics"""
    webhook_stats = get_webhook_stats()
    ai_health = await get_ai_agent_health()
    
    return {
        "webhook_stats": webhook_stats,
        "ai_agent_stats": ai_health
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )