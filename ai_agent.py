import asyncio
import logging
from datetime import datetime
from typing import Optional
from models import AIRequest, AIResponse

logger = logging.getLogger(__name__)


class AIAgent:
    """Simple AI agent simulator for webhook processing"""
    
    def __init__(self):
        self.is_ready = True
        self.processing_count = 0
        
    async def process_webhook(self, ai_request: AIRequest) -> AIResponse:
        """
        Process webhook data and return AI response
        
        Args:
            ai_request: AIRequest object with webhook data
            
        Returns:
            AIResponse with processing results
        """
        start_time = datetime.utcnow()
        self.processing_count += 1
        
        try:
            logger.info(f"AI Agent processing webhook {ai_request.webhook_id}")
            
            # Simulate AI processing delay
            await asyncio.sleep(0.1)  # 100ms processing time
            
            # Generate response based on message content
            response_text = self._generate_response(ai_request)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = AIResponse(
                webhook_id=ai_request.webhook_id,
                success=True,
                response_text=response_text,
                processing_time=processing_time
            )
            
            logger.info(f"AI Agent completed processing webhook {ai_request.webhook_id} "
                       f"in {processing_time:.3f}s")
            
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"AI Agent error processing webhook {ai_request.webhook_id}: {e}")
            
            return AIResponse(
                webhook_id=ai_request.webhook_id,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _generate_response(self, ai_request: AIRequest) -> str:
        """Generate appropriate response based on input data"""
        if not ai_request.message_text:
            return "Получено сообщение без текста"
            
        text = ai_request.message_text.lower().strip()
        
        # Simple response logic
        if "привет" in text or "hello" in text:
            return "Привет! Рад вас видеть!"
        elif "помощь" in text or "help" in text:
            return "Я могу помочь вам с различными вопросами. Что вам нужно?"
        elif "время" in text or "time" in text:
            return f"Текущее время: {datetime.now().strftime('%H:%M:%S')}"
        elif "?" in text:
            return "Интересный вопрос! Я подумаю над этим."
        else:
            return f"Получено сообщение: '{ai_request.message_text}'"
    
    async def health_check(self) -> dict:
        """Check AI agent health status"""
        return {
            "status": "healthy" if self.is_ready else "unhealthy",
            "processing_count": self.processing_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_stats(self) -> dict:
        """Get AI agent statistics"""
        return {
            "total_processed": self.processing_count,
            "is_ready": self.is_ready,
            "average_processing_time": 0.1  # Simulated average
        }


# Global AI agent instance
ai_agent = AIAgent()


# Utility functions for external use
async def send_to_ai_agent(ai_request: AIRequest) -> AIResponse:
    """Convenience function to send data to AI agent"""
    return await ai_agent.process_webhook(ai_request)


async def get_ai_agent_health() -> dict:
    """Convenience function to check AI agent health"""
    return await ai_agent.health_check()