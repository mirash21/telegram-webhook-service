import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Header
from models import TelegramWebhook, ProcessedWebhook, AIRequest
from ai_agent import send_to_ai_agent
from config import config

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """Main webhook processor class"""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        
    async def process_telegram_webhook(self, request: Request, body: bytes) -> ProcessedWebhook:
        """
        Process incoming Telegram webhook
        
        Args:
            request: FastAPI Request object
            body: Raw request body bytes
            
        Returns:
            ProcessedWebhook with processing results
        """
        try:
            # Validate webhook signature if secret token is configured
            if config.WEBHOOK_SECRET_TOKEN:
                self._validate_signature(request, body)
            
            # Parse and validate Telegram webhook data
            telegram_webhook = self._parse_webhook_data(body)
            
            # Extract message information
            message = telegram_webhook.get_message()
            if not message:
                raise ValueError("No message found in webhook")
            
            # Create processed webhook record
            processed_webhook = ProcessedWebhook(
                update_id=telegram_webhook.update_id,
                chat_id=message.chat.id if message.chat else None,
                user_id=message.from_user.id if message.from_user else None,
                message_text=telegram_webhook.get_text(),
                message_type=self._determine_message_type(telegram_webhook),
                raw_data=body.decode('utf-8')
            )
            
            # Send to AI agent for processing
            ai_request = AIRequest(
                webhook_id=processed_webhook.id or 0,
                update_id=telegram_webhook.update_id,
                chat_id=processed_webhook.chat_id,
                user_id=processed_webhook.user_id,
                message_text=processed_webhook.message_text,
                message_type=processed_webhook.message_type
            )
            
            ai_response = await send_to_ai_agent(ai_request)
            
            # Update processed webhook with AI results
            processed_webhook.sent_to_ai = ai_response.success
            processed_webhook.ai_response = ai_response.response_text
            
            self.processed_count += 1
            logger.info(f"Successfully processed webhook {telegram_webhook.update_id}")
            
            return processed_webhook
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing webhook: {e}")
            raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")
    
    def _validate_signature(self, request: Request, body: bytes):
        """Validate Telegram webhook signature"""
        try:
            # Get signature from header
            signature = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
            if not signature:
                raise HTTPException(status_code=401, detail="Missing signature header")
            
            # Verify signature
            expected_signature = hmac.new(
                config.WEBHOOK_SECRET_TOKEN.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            raise HTTPException(status_code=401, detail="Signature validation failed")
    
    def _parse_webhook_data(self, body: bytes) -> TelegramWebhook:
        """Parse and validate webhook JSON data"""
        try:
            data = json.loads(body.decode('utf-8'))
            return TelegramWebhook(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")
        except Exception as e:
            raise ValueError(f"Webhook data validation failed: {e}")
    
    def _determine_message_type(self, webhook: TelegramWebhook) -> str:
        """Determine message type from webhook data"""
        message = webhook.get_message()
        if not message:
            return "unknown"
            
        if message.text:
            return "text"
        elif message.photo:
            return "photo"
        elif message.document:
            return "document"
        elif message.audio:
            return "audio"
        elif message.video:
            return "video"
        elif message.entities:
            return "entities"
        else:
            return "other"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get webhook processor statistics"""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "success_rate": (
                self.processed_count / (self.processed_count + self.error_count) 
                if (self.processed_count + self.error_count) > 0 else 0
            ),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global webhook processor instance
webhook_processor = WebhookProcessor()


# Convenience functions
async def handle_webhook(request: Request, body: bytes) -> ProcessedWebhook:
    """Convenience function to handle webhook processing"""
    return await webhook_processor.process_telegram_webhook(request, body)


def get_webhook_stats() -> Dict[str, Any]:
    """Get webhook processing statistics"""
    return webhook_processor.get_statistics()


# Rate limiting implementation
class RateLimiter:
    """Simple rate limiter for webhook requests"""
    
    def __init__(self):
        self.requests = {}  # ip_address -> [timestamps]
        
    def is_allowed(self, ip_address: str) -> bool:
        """Check if request from IP is allowed based on rate limits"""
        now = datetime.utcnow().timestamp()
        window_start = now - config.RATE_LIMIT_WINDOW
        
        # Clean old requests
        if ip_address in self.requests:
            self.requests[ip_address] = [
                timestamp for timestamp in self.requests[ip_address]
                if timestamp > window_start
            ]
        else:
            self.requests[ip_address] = []
        
        # Check rate limit
        if len(self.requests[ip_address]) >= config.RATE_LIMIT:
            return False
            
        # Add current request
        self.requests[ip_address].append(now)
        return True


rate_limiter = RateLimiter()