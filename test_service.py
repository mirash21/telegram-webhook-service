import asyncio
import httpx
import json

async def test_webhook_service():
    """Test the webhook service with sample data"""
    
    # Test data similar to Telegram webhook
    test_data = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 987654321,
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe"
            },
            "chat": {
                "id": 987654321,
                "type": "private"
            },
            "date": 1708234567,
            "text": "Привет, как дела?"
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            print("Testing health endpoint...")
            response = await client.get("http://localhost:8000/")
            print(f"Health check: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
            
            # Test webhook endpoint
            print("Testing webhook endpoint...")
            response = await client.post(
                "http://localhost:8000/webhook/telegram",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Webhook response status: {response.status_code}")
            if response.status_code == 200:
                print("Webhook processed successfully!")
                print(f"Response data: {response.json()}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error connecting to service: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook_service())