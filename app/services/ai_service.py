import json
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.client import Client
from app.models.product import Product
from app.models.order import Order
from app.models.conversation import Conversation
from app.models.message import Message, MessageDirection

logger = structlog.get_logger()


class AIService:
    """AI service for handling OpenAI integration and conversation processing"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.AI_MODEL
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS
        
        # Business context
        self.business_context = f"""
        You are an AI assistant for {settings.BUSINESS_NAME}, a cake and pastry shop.
        
        Business Information:
        - Name: {settings.BUSINESS_NAME}
        - Phone: {settings.BUSINESS_PHONE}
        - Email: {settings.BUSINESS_EMAIL}
        - Address: {settings.BUSINESS_ADDRESS}
        
        Your role is to help customers with:
        1. Product inquiries and recommendations
        2. Order placement and customization
        3. Delivery and pickup information
        4. General customer service
        
        Be friendly, helpful, and professional. Always try to convert conversations into sales opportunities.
        If you can't answer a question, politely ask the customer to wait while you connect them with a human staff member.
        """
    
    async def process_message(
        self,
        message: str,
        client: Client,
        conversation: Conversation,
        message_history: List[Message],
        products: List[Product] = None
    ) -> Dict[str, Any]:
        """
        Process an incoming message and generate AI response
        
        Args:
            message: The incoming message text
            client: The client who sent the message
            conversation: The conversation context
            message_history: Previous messages in the conversation
            products: Available products for recommendations
            
        Returns:
            Dict containing response, intent, entities, and confidence
        """
        try:
            # Build conversation context
            context = self._build_conversation_context(
                client, conversation, message_history, products
            )
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": self.business_context},
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ]
            
            # Add recent message history
            for msg in message_history[-10:]:  # Last 10 messages
                role = "user" if msg.direction == MessageDirection.INCOMING else "assistant"
                if msg.content:
                    messages.insert(-1, {"role": role, "content": msg.content})
            
            # Get AI response
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract intent and entities
            intent = await self._extract_intent(message)
            entities = await self._extract_entities(message)
            
            # Calculate confidence (simplified)
            confidence = min(95, max(60, len(ai_response) * 2))
            
            return {
                "response": ai_response,
                "intent": intent,
                "entities": entities,
                "confidence": confidence,
                "should_escalate": self._should_escalate_to_human(intent, entities)
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your message right now. Let me connect you with a human staff member who can help you.",
                "intent": "error",
                "entities": {},
                "confidence": 0,
                "should_escalate": True
            }
    
    def _build_conversation_context(
        self,
        client: Client,
        conversation: Conversation,
        message_history: List[Message],
        products: List[Product] = None
    ) -> str:
        """Build context for the AI conversation"""
        
        context_parts = []
        
        # Client information
        context_parts.append(f"Customer Information:")
        context_parts.append(f"- Name: {client.full_name}")
        context_parts.append(f"- Phone: {client.phone}")
        if client.email:
            context_parts.append(f"- Email: {client.email}")
        
        # Client preferences and history
        if client.preferences:
            context_parts.append(f"- Preferences: {json.dumps(client.preferences)}")
        if client.total_orders > 0:
            context_parts.append(f"- Total previous orders: {client.total_orders}")
            context_parts.append(f"- Total spent: ${client.total_spent / 100:.2f}")
        
        # Available products
        if products:
            context_parts.append(f"\nAvailable Products:")
            for product in products[:20]:  # Limit to 20 products
                context_parts.append(
                    f"- {product.name}: ${product.price_display:.2f} ({product.category.value})"
                )
                if product.description:
                    context_parts.append(f"  Description: {product.description}")
        
        # Current time
        context_parts.append(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(context_parts)
    
    async def _extract_intent(self, message: str) -> str:
        """Extract intent from message"""
        # Simplified intent extraction
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["order", "buy", "purchase", "want"]):
            return "order_intent"
        elif any(word in message_lower for word in ["price", "cost", "how much"]):
            return "price_inquiry"
        elif any(word in message_lower for word in ["menu", "products", "what do you have"]):
            return "product_inquiry"
        elif any(word in message_lower for word in ["delivery", "pickup", "when"]):
            return "delivery_inquiry"
        elif any(word in message_lower for word in ["cancel", "change", "modify"]):
            return "order_modification"
        elif any(word in message_lower for word in ["hello", "hi", "hey"]):
            return "greeting"
        else:
            return "general_inquiry"
    
    async def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message"""
        # Simplified entity extraction
        entities = {}
        
        # Extract potential product names (this would be more sophisticated in production)
        message_lower = message.lower()
        
        # Common cake/pastry terms
        if "cake" in message_lower:
            entities["product_type"] = "cake"
        elif "cupcake" in message_lower:
            entities["product_type"] = "cupcake"
        elif "pastry" in message_lower:
            entities["product_type"] = "pastry"
        elif "cookie" in message_lower:
            entities["product_type"] = "cookie"
        
        # Extract numbers (could be quantities or prices)
        import re
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        return entities
    
    def _should_escalate_to_human(self, intent: str, entities: Dict[str, Any]) -> bool:
        """Determine if conversation should be escalated to human"""
        
        escalation_intents = [
            "complaint",
            "refund",
            "complex_customization",
            "urgent_request"
        ]
        
        return intent in escalation_intents
    
    async def generate_product_recommendations(
        self,
        client: Client,
        products: List[Product],
        context: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate personalized product recommendations"""
        
        try:
            # Build recommendation context
            recommendation_context = f"""
            Based on the customer information and available products, recommend 3-5 products that would be most suitable.
            
            Customer: {client.full_name}
            Previous orders: {client.total_orders}
            Preferences: {json.dumps(client.preferences) if client.preferences else 'None'}
            Context: {context}
            
            Available products:
            {json.dumps([{'name': p.name, 'price': p.price_display, 'category': p.category.value, 'description': p.description} for p in products[:30]])}
            
            Provide recommendations in JSON format with reasoning.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful product recommendation assistant for a cake shop."},
                    {"role": "user", "content": recommendation_context}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse recommendations (simplified)
            recommendations = []
            for product in products[:5]:  # Fallback to first 5 products
                recommendations.append({
                    "product_id": product.id,
                    "name": product.name,
                    "price": product.price_display,
                    "reason": f"Great choice for {client.full_name}"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def analyze_conversation_sentiment(self, messages: List[Message]) -> Dict[str, Any]:
        """Analyze sentiment of conversation"""
        
        try:
            # Combine recent messages
            text_content = []
            for msg in messages[-10:]:  # Last 10 messages
                if msg.content and msg.direction == MessageDirection.INCOMING:
                    text_content.append(msg.content)
            
            if not text_content:
                return {"sentiment": "neutral", "confidence": 0}
            
            combined_text = " ".join(text_content)
            
            # Simple sentiment analysis (in production, use more sophisticated methods)
            positive_words = ["good", "great", "excellent", "love", "perfect", "amazing"]
            negative_words = ["bad", "terrible", "awful", "hate", "horrible", "disappointed"]
            
            positive_count = sum(1 for word in positive_words if word in combined_text.lower())
            negative_count = sum(1 for word in negative_words if word in combined_text.lower())
            
            if positive_count > negative_count:
                sentiment = "positive"
                confidence = min(90, positive_count * 20)
            elif negative_count > positive_count:
                sentiment = "negative"
                confidence = min(90, negative_count * 20)
            else:
                sentiment = "neutral"
                confidence = 50
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "positive_indicators": positive_count,
                "negative_indicators": negative_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"sentiment": "neutral", "confidence": 0} 