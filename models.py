from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
import json


class TelegramUser(BaseModel):
    """Telegram user model"""
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    added_to_attachment_menu: Optional[bool] = None


class TelegramChat(BaseModel):
    """Telegram chat model"""
    id: int
    type: str  # private, group, supergroup, channel
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message model"""
    message_id: int
    date: datetime
    chat: TelegramChat
    from_user: Optional[TelegramUser] = Field(None, alias='from')
    text: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    caption: Optional[str] = None
    photo: Optional[List[Dict[str, Any]]] = None
    document: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True

    @validator('date', pre=True)
    def convert_timestamp(cls, v):
        if isinstance(v, int):
            return datetime.fromtimestamp(v)
        return v


class TelegramWebhook(BaseModel):
    """Main Telegram webhook model"""
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None
    edited_channel_post: Optional[TelegramMessage] = None
    inline_query: Optional[Dict[str, Any]] = None
    chosen_inline_result: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    shipping_query: Optional[Dict[str, Any]] = None
    pre_checkout_query: Optional[Dict[str, Any]] = None
    poll: Optional[Dict[str, Any]] = None
    poll_answer: Optional[Dict[str, Any]] = None
    my_chat_member: Optional[Dict[str, Any]] = None
    chat_member: Optional[Dict[str, Any]] = None
    chat_join_request: Optional[Dict[str, Any]] = None

    def get_message(self) -> Optional[TelegramMessage]:
        """Get the main message from the update"""
        return self.message or self.edited_message or self.channel_post or self.edited_channel_post

    def get_text(self) -> Optional[str]:
        """Extract text content from the message"""
        message = self.get_message()
        if not message:
            return None
            
        return message.text or message.caption


class WebhookResponse(BaseModel):
    """Response model for webhook endpoint"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed_data: Optional[Dict[str, Any]] = None


class ProcessedWebhook(BaseModel):
    """Model for storing processed webhook data"""
    id: Optional[int] = None
    update_id: int
    chat_id: Optional[int] = None
    user_id: Optional[int] = None
    message_text: Optional[str] = None
    message_type: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    sent_to_ai: bool = False
    ai_response: Optional[str] = None
    raw_data: str  # JSON string of original webhook

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            'update_id': self.update_id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'message_text': self.message_text,
            'message_type': self.message_type,
            'processed_at': self.processed_at,
            'sent_to_ai': self.sent_to_ai,
            'ai_response': self.ai_response,
            'raw_data': self.raw_data
        }


class AIRequest(BaseModel):
    """Model for sending data to AI agent"""
    webhook_id: int
    update_id: int
    chat_id: Optional[int]
    user_id: Optional[int]
    message_text: Optional[str]
    message_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIResponse(BaseModel):
    """Model for AI agent response"""
    webhook_id: int
    success: bool
    response_text: Optional[str] = None
    processing_time: float  # in seconds
    error_message: Optional[str] = None