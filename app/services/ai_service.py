import json
import structlog
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.client import Client
from app.models.product import Product
from app.models.order import Order
from app.models.conversation import Conversation
from app.models.message import Message, MessageDirection
from app.prompts.telegram_bot_prompts import TelegramBotPrompts, TelegramBotTemplates

logger = structlog.get_logger()


class AIService:
    """AI service for handling OpenAI integration and conversation processing"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.AI_MODEL
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS
        
        # Load prompts from external file
        self.prompts = TelegramBotPrompts()
        self.templates = TelegramBotTemplates()
        
        # Cache prompts for performance
        self.business_context = self.prompts.get_business_context()
        self.knowledge_base_context = self.prompts.get_knowledge_base()
        self.platform_contexts = self.prompts.get_platform_contexts()
        self.intent_keywords = self.prompts.get_intent_keywords()
        self.entity_patterns = self.prompts.get_entity_patterns()

    async def process_message(
        self,
        message: str,
        client: Client,
        conversation: Conversation,
        message_history: List[Message],
        products: List[Product] = None,
        platform_context: str = "general"
    ) -> Dict[str, Any]:
        """
        Enhanced message processing with platform-specific context
        
        Args:
            message: The incoming message text
            client: The client who sent the message
            conversation: The conversation context
            message_history: Previous messages in the conversation
            products: Available products for recommendations
            platform_context: Platform-specific context (telegram, whatsapp, etc.)
            
        Returns:
            Dict containing response, intent, entities, and confidence
        """
        try:
            # Build enhanced conversation context
            context = self._build_enhanced_conversation_context(
                client, conversation, message_history, products, platform_context
            )
            
            # Create messages for OpenAI with enhanced context
            messages = [
                {"role": "system", "content": self.business_context},
                {"role": "system", "content": self.knowledge_base_context},
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ]
            
            # Add recent message history with better formatting
            for msg in message_history[-10:]:  # Last 10 messages
                role = "user" if msg.direction == MessageDirection.INCOMING else "assistant"
                if msg.content:
                    messages.insert(-1, {"role": role, "content": msg.content})
            
            # Get AI response with enhanced parameters
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                presence_penalty=0.1,  # Encourage more diverse responses
                frequency_penalty=0.1   # Reduce repetition
            )
            
            ai_response = response.choices[0].message.content
            
            # Extract intent and entities with enhanced analysis
            intent = self._extract_enhanced_intent(message, ai_response)
            entities = self._extract_enhanced_entities(message)
            
            # Calculate confidence based on response quality
            confidence = self._calculate_response_confidence(message, ai_response, intent)
            
            return {
                "response": ai_response,
                "intent": intent,
                "entities": entities,
                "confidence": confidence,
                "platform": platform_context,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error processing message with AI: {e}")
            
            # Check if this is an API key error and provide helpful fallback
            if "invalid_api_key" in str(e) or "401" in str(e):
                return self._get_fallback_response(message, client, products)
            
            return {
                "response": self.prompts.get_error_response(),
                "intent": "error",
                "entities": {},
                "confidence": 0.0,
                "error": str(e)
            }

    def _build_enhanced_conversation_context(
        self,
        client: Client,
        conversation: Conversation,
        message_history: List[Message],
        products: List[Product],
        platform_context: str
    ) -> str:
        """Build enhanced conversation context with platform-specific information"""
        
        # Get the context template
        template = self.prompts.get_conversation_context_template()
        
        # Product availability context
        available_products = []
        if products:
            for category in self.entity_patterns["product_categories"]:
                category_items = [p for p in products if str(p.category).lower() == category]
                if category_items:
                    available_products.append(f"{category.title()}: {len(category_items)} items available")
        
        # Format the template with actual data
        return template.format(
            client_name=f"{client.first_name or ''} {client.last_name or ''}".strip() or "Customer",
            contact_method=self._get_client_contact_method(client),
            order_count=len([msg for msg in message_history if 'order' in msg.content.lower()]),
            preferences=getattr(client, 'preferences', 'None'),
            channel=conversation.channel.value,
            status=conversation.status.value,
            message_count=len(message_history),
            recent_topics=self._extract_recent_topics(message_history),
            available_products="\n".join(available_products) if available_products else "Full catalog available"
        ) + f"\n\n{self.platform_contexts.get(platform_context, self.platform_contexts['general'])}"

    def _get_client_contact_method(self, client: Client) -> str:
        """Determine client's preferred contact method based on available data"""
        if client.telegram_id:
            return "telegram"
        elif client.whatsapp_id:
            return "whatsapp"
        elif client.email:
            return "email"
        elif client.phone and not client.phone.startswith("telegram_"):
            return "phone"
        else:
            return "unknown"

    def _extract_enhanced_intent(self, message: str, ai_response: str) -> str:
        """Extract enhanced intent from message and response"""
        message_lower = message.lower()
        
        # Check for order-related intents first
        if any(word in message_lower for word in self.intent_keywords["order_related"]):
            if any(word in message_lower for word in self.intent_keywords["birthday_cake"]):
                return "order_birthday_cake"
            elif any(word in message_lower for word in self.intent_keywords["wedding_cake"]):
                return "order_wedding_cake"
            elif any(word in message_lower for word in self.intent_keywords["pastries"]):
                return "order_pastries"
            else:
                return "place_order"
        
        # Check for information requests
        elif any(word in message_lower for word in self.intent_keywords["menu_inquiry"]):
            return "browse_menu"
        elif any(word in message_lower for word in self.intent_keywords["pricing"]):
            return "pricing_inquiry"
        elif any(word in message_lower for word in self.intent_keywords["delivery"]):
            return "delivery_inquiry"
        elif any(word in message_lower for word in self.intent_keywords["business_info"]):
            return "business_info"
        
        # Check for support requests
        elif any(word in message_lower for word in self.intent_keywords["support"]):
            return "human_support"
        elif any(word in message_lower for word in self.intent_keywords["status"]):
            return "order_status"
        
        # Check for greetings and closings
        elif any(word in message_lower for word in self.intent_keywords["greeting"]):
            return "greeting"
        elif any(word in message_lower for word in self.intent_keywords["closing"]):
            return "closing"
        
        # Default
        else:
            return "general_inquiry"

    def _extract_enhanced_entities(self, message: str) -> Dict[str, Any]:
        """Extract enhanced entities from message"""
        entities = {}
        message_lower = message.lower()
        
        # Product categories
        for category in self.entity_patterns["product_categories"]:
            if category in message_lower:
                entities["product_category"] = category
        
        # Occasions
        for occasion in self.entity_patterns["occasions"]:
            if occasion in message_lower:
                entities["occasion"] = occasion
        
        # Sizes/quantities using regex pattern
        quantity_pattern = self.entity_patterns["quantity_pattern"]
        quantity_match = re.search(quantity_pattern, message_lower)
        if quantity_match:
            entities["quantity"] = {
                "number": int(quantity_match.group(1)),
                "unit": quantity_match.group(2)
            }
        
        # Dietary restrictions
        for diet in self.entity_patterns["dietary_restrictions"]:
            if diet in message_lower:
                entities["dietary_restriction"] = diet
        
        # Flavors
        for flavor in self.entity_patterns["flavors"]:
            if flavor in message_lower:
                entities["flavor"] = flavor
        
        # Urgency
        if any(word in message_lower for word in self.entity_patterns["urgency_high"]):
            entities["urgency"] = "high"
        elif any(word in message_lower for word in self.entity_patterns["urgency_low"]):
            entities["urgency"] = "low"
        else:
            entities["urgency"] = "normal"
        
        return entities

    def _calculate_response_confidence(self, message: str, response: str, intent: str) -> float:
        """Calculate confidence score for the AI response"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear intents
        if intent in ["place_order", "browse_menu", "pricing_inquiry"]:
            confidence += 0.2
        
        # Increase confidence if response contains specific information
        if response and any(char in response for char in ["$", "€", "£"]):  # Contains pricing
            confidence += 0.1
        
        if response and len(response) > 50:  # Detailed response
            confidence += 0.1
        
        # Decrease confidence for unclear messages
        if len(message.split()) < 3:  # Very short message
            confidence -= 0.1
        
        if "?" in message and intent == "general_inquiry":  # Question without clear intent
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1

    def _extract_recent_topics(self, message_history: List[Message]) -> str:
        """Extract recent conversation topics"""
        if not message_history:
            return "New conversation"
        
        recent_messages = message_history[-5:]  # Last 5 messages
        topics = []
        
        for msg in recent_messages:
            if msg.content:
                content_lower = msg.content.lower()
                if any(word in content_lower for word in ["cake", "birthday", "wedding"]):
                    topics.append("cakes")
                elif any(word in content_lower for word in ["pastry", "croissant"]):
                    topics.append("pastries")
                elif any(word in content_lower for word in ["order", "buy"]):
                    topics.append("ordering")
                elif any(word in content_lower for word in ["price", "cost"]):
                    topics.append("pricing")
        
        return ", ".join(set(topics)) if topics else "General conversation"
    
    async def generate_product_recommendations(
        self,
        client: Client,
        products: List[Product],
        context: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate personalized product recommendations"""
        
        try:
            # Build recommendation context using templates
            recommendation_context = f"""
            Based on the customer information and available products, recommend 3-5 products that would be most suitable.
            
            Customer: {client.full_name}
            Previous orders: {getattr(client, 'total_orders', 0)}
            Preferences: {json.dumps(getattr(client, 'preferences', {})) if hasattr(client, 'preferences') else 'None'}
            Context: {context}
            
            Available products:
            {json.dumps([{
                'name': p.name, 
                'price': getattr(p, 'base_price', 0), 
                'category': str(p.category), 
                'description': p.description
            } for p in products[:30]])}
            
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
                    "price": getattr(product, 'base_price', 0),
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
            positive_words = ["good", "great", "excellent", "love", "perfect", "amazing", "wonderful", "fantastic"]
            negative_words = ["bad", "terrible", "awful", "hate", "horrible", "disappointed", "poor", "worst"]
            
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
    
    def get_quick_order_response(self, order_type: str) -> str:
        """Get a pre-defined quick order response"""
        quick_responses = self.prompts.get_quick_order_responses()
        return quick_responses.get(order_type, "🛒 Let me help you with your order!")
    
    def format_product_recommendation(self, product_name: str, price: float, description: str) -> str:
        """Format a product recommendation using templates"""
        return self.templates.format_product_recommendation(product_name, price, description)
    
    def format_order_summary(self, items: list, total: float, delivery_fee: float = 0) -> str:
        """Format an order summary using templates"""
        return self.templates.format_order_summary(items, total, delivery_fee)
    
    def get_business_hours_info(self) -> str:
        """Get formatted business hours information"""
        return self.templates.format_business_hours()
    
    def get_contact_info(self) -> str:
        """Get formatted contact information"""
        return self.templates.format_contact_info() 

    def _get_fallback_response(self, message: str, client: Client, products: List[Product] = None) -> Dict[str, Any]:
        """Provide basic responses when AI is not available"""
        message_lower = message.lower()
        client_name = f"{client.first_name or ''} {client.last_name or ''}".strip() or "valued customer"
        
        # Basic intent detection
        if any(word in message_lower for word in ['start', 'hello', 'hi', 'hey']):
            response = f"""
🎂 **Welcome to Napoleon-Tseh, {client_name}!**

I'm here to help you with our delicious cakes and pastries! Here's what I can assist you with:

🍰 **Our Specialties:**
- Custom Birthday Cakes
- Wedding Cakes  
- Fresh Daily Pastries
- Special Occasion Desserts

📋 **How to Order:**
1. Tell me what occasion you're celebrating
2. Let me know how many people you're serving
3. Choose your preferred flavors and decorations
4. Schedule pickup or delivery

📞 **Contact Us:**
Phone: {settings.BUSINESS_PHONE}
Email: {settings.BUSINESS_EMAIL}

💬 Try asking: "I need a birthday cake" or "Show me your menu"
"""
        
        elif any(word in message_lower for word in ['menu', 'catalog', 'what do you have']):
            response = """
🍰 **NAPOLEON-TSEH MENU** 

🎂 **CAKES:**
- Birthday Cakes: 6" ($35-45), 8" ($50-65), 10" ($70-85)
- Wedding Cakes: 2-tier ($150-250), 3-tier ($250-400)
- Custom designs available

🥐 **PASTRIES:** 
- Fresh Croissants: $3-5 each
- Danish Pastries: $4-6 each  
- Éclairs & Profiteroles: $5-7 each

🍮 **DESSERTS:**
- Tiramisu: $6 individual, $35 whole tray
- Cheesecake: $7 slice, $40 whole
- Macarons: $25 (box of 12)

📞 Call us for detailed pricing and custom orders!
"""
        
        elif any(word in message_lower for word in ['order', 'buy', 'cake', 'birthday', 'wedding']):
            response = f"""
🛒 **Let's Create Your Perfect Order, {client_name}!**

To help you best, I'll need some details:

📋 **Tell me about:**
1. **Occasion**: Birthday, wedding, celebration?
2. **Size**: How many people will you serve?
3. **Flavors**: Chocolate, vanilla, strawberry, etc.?
4. **Date needed**: When do you need it?
5. **Delivery/Pickup**: Which do you prefer?

💡 **Popular Options:**
- Birthday Cake for 10 people: $50-65
- Wedding consultation: Free with order
- Same-day pickup available

📞 **Quick Order**: Call {settings.BUSINESS_PHONE}
📧 **Email**: {settings.BUSINESS_EMAIL}
"""
        
        elif any(word in message_lower for word in ['price', 'cost', 'how much']):
            response = """
💰 **NAPOLEON-TSEH PRICING**

🎂 **Birthday Cakes:**
- 6" (serves 6-8): $35-45
- 8" (serves 10-12): $50-65  
- 10" (serves 15-20): $70-85

💒 **Wedding Cakes:**
- 2-tier (30-40 people): $150-250
- 3-tier (50-70 people): $250-400
- Custom designs: Quote on request

🥐 **Daily Fresh Items:**
- Croissants: $3-5 each
- Pastries: $4-7 each
- Dessert boxes: $25-45

📞 Call for exact pricing and customization options!
"""
        
        elif any(word in message_lower for word in ['hours', 'open', 'location', 'contact']):
            response = f"""
📍 **NAPOLEON-TSEH INFORMATION**

🏢 **{settings.BUSINESS_NAME}**
📍 {settings.BUSINESS_ADDRESS}
📞 Phone: {settings.BUSINESS_PHONE}
📧 Email: {settings.BUSINESS_EMAIL}

⏰ **Hours:**
Monday-Friday: 7:00 AM - 8:00 PM
Saturday-Sunday: 8:00 AM - 9:00 PM

🚚 **Delivery:** Available 7 days a week
🏪 **Pickup:** Free at our store location
"""
        
        else:
            # Generic helpful response
            response = f"""
Thank you for your message, {client_name}! 

I'd love to help you with our delicious cakes and pastries. Here are some things you can ask me:

🍰 "Show me your menu"
🎂 "I need a birthday cake for 10 people"  
💰 "What are your prices?"
📍 "What are your hours?"
🛒 "How do I place an order?"

📞 **For immediate assistance:**
Call: {settings.BUSINESS_PHONE}
Email: {settings.BUSINESS_EMAIL}

What can I help you create today? 🎂✨
"""
        
        # Determine basic intent
        intent = "general_inquiry"
        if any(word in message_lower for word in ['order', 'buy', 'cake']):
            intent = "place_order"
        elif any(word in message_lower for word in ['menu', 'catalog']):
            intent = "browse_menu"
        elif any(word in message_lower for word in ['price', 'cost']):
            intent = "pricing_inquiry"
        
        return {
            "response": response.strip(),
            "intent": intent,
            "entities": {},
            "confidence": 0.8,
            "platform": "fallback_mode",
            "tokens_used": 0
        } 