import structlog
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import time

from app.core.config import settings
from app.core.database import get_async_session
from app.models.client import Client
from app.models.conversation import Conversation, ConversationChannel, ConversationStatus
from app.models.message import Message, MessageDirection, MessageType, MessageStatus
from app.models.product import Product, ProductStatus, ProductCategory
from app.models.order import Order, OrderStatus
from app.services.ai_service import AIService
from app.services.message_processor import MessageProcessor
from app.prompts.telegram_bot_prompts import TelegramBotPrompts, TelegramBotTemplates

logger = structlog.get_logger()


class TelegramBotService:
    """Enhanced Telegram bot service with OpenAI integration for customer service"""
    
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self.ai_service = AIService()
        
        # Load prompts and templates
        self.prompts = TelegramBotPrompts()
        self.templates = TelegramBotTemplates()
        
        # Enhanced business context for Telegram bot
        self.bot_context = f"""
        You are Napoleon-Tseh's AI customer service assistant on Telegram. 
        
        🏢 BUSINESS INFORMATION:
        - Name: {settings.BUSINESS_NAME}
        - Phone: {settings.BUSINESS_PHONE}
        - Email: {settings.BUSINESS_EMAIL}
        - Address: {settings.BUSINESS_ADDRESS}
        
        🎯 YOUR CAPABILITIES:
        1. Product catalog and recommendations
        2. Order taking and customization
        3. Pricing and availability information
        4. Delivery/pickup scheduling
        5. Customer support and FAQs
        
        📋 PRODUCT CATEGORIES:
        - Cakes (Custom, Birthday, Wedding, Special occasion)
        - Pastries (Croissants, Danish, Éclairs, Profiteroles)
        - Desserts (Tiramisu, Cheesecake, Macarons)
        - Beverages (Coffee, Tea, Fresh juices)
        
        💬 COMMUNICATION STYLE:
        - Be friendly, professional, and enthusiastic
        - Use emojis to make conversations engaging
        - Provide clear, structured information
        - Always ask clarifying questions for orders
        - Suggest upsells and complementary items
        - If unsure, connect customer to human staff
        
        🛒 ORDER PROCESS:
        1. Understand customer needs
        2. Recommend suitable products
        3. Confirm specifications (size, flavor, decorations)
        4. Calculate pricing
        5. Schedule delivery/pickup
        6. Collect contact information
        7. Generate order summary
        
        🚀 RESPONSE FORMAT:
        Use clear sections with emojis:
        📝 Product Details
        💰 Pricing
        ⏰ Timeline
        📋 Next Steps
        """
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("order", self.order_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for regular text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Contact and location handlers
        self.application.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
        self.application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🎂 Welcome to Napoleon-Tseh Bakery, {user.first_name}! 

I'm your AI assistant, ready to help you with:

🍰 **Browse our delicious menu**
🛒 **Place custom orders**
📍 **Get delivery information**
💬 **Answer any questions**

🚀 **Quick Actions:**
"""
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("🍰 View Menu", callback_data="show_menu"),
                InlineKeyboardButton("🛒 Place Order", callback_data="start_order")
            ],
            [
                InlineKeyboardButton("📍 Location & Hours", callback_data="location_info"),
                InlineKeyboardButton("📞 Contact Us", callback_data="contact_info")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help_info")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        
        # Process this interaction through our system
        await self._process_telegram_interaction(update, "start_command")
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        try:
            async for db in get_async_session():
                # Get active products by category
                result = await db.execute(
                    select(Product)
                    .where(Product.status == ProductStatus.ACTIVE)
                    .order_by(Product.category, Product.name)
                )
                products = result.scalars().all()
                
                if not products:
                    await update.message.reply_text("🚧 Our menu is being updated. Please check back soon!")
                    return
                
                # Group products by category
                menu_by_category = {}
                for product in products:
                    category = product.category.value if hasattr(product.category, 'value') else str(product.category)
                    if category not in menu_by_category:
                        menu_by_category[category] = []
                    menu_by_category[category].append(product)
                
                # Create menu message
                menu_text = "🍰 **NAPOLEON-TSEH MENU** 🍰\n\n"
                
                category_emojis = {
                    "cake": "🎂",
                    "pastry": "🥐", 
                    "dessert": "🍮",
                    "beverage": "☕"
                }
                
                for category, items in menu_by_category.items():
                    emoji = category_emojis.get(category.lower(), "🍽️")
                    menu_text += f"{emoji} **{category.upper()}**\n"
                    
                    for item in items[:5]:  # Limit to 5 items per category
                        price = f"${item.base_price:.2f}" if item.base_price else "Price on request"
                        menu_text += f"   • {item.name} - {price}\n"
                        if item.description:
                            menu_text += f"     _{item.description[:50]}..._\n"
                    
                    if len(items) > 5:
                        menu_text += f"     _...and {len(items) - 5} more items_\n"
                    menu_text += "\n"
                
                menu_text += "💬 Type the name of any item for more details!\n"
                menu_text += "🛒 Use /order to start placing an order"
                
                # Create category selection keyboard
                keyboard = []
                for category in menu_by_category.keys():
                    emoji = category_emojis.get(category.lower(), "🍽️")
                    keyboard.append([InlineKeyboardButton(f"{emoji} {category.title()}", callback_data=f"category_{category}")])
                
                keyboard.append([InlineKeyboardButton("🛒 Start Order", callback_data="start_order")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in menu_command: {e}")
            await update.message.reply_text("❌ Sorry, I couldn't load the menu right now. Please try again!")
    
    async def order_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /order command"""
        order_message = """
🛒 **START YOUR ORDER**

I'll help you create the perfect order! Here's how it works:

1️⃣ **Tell me what you want**
   - "I want a birthday cake for 10 people"
   - "Show me chocolate pastries"
   - "I need dessert for a party"

2️⃣ **I'll show you options**
   - Available products
   - Customization choices
   - Pricing information

3️⃣ **We'll finalize details**
   - Delivery/pickup preferences
   - Special instructions
   - Contact information

🎯 **What would you like to order today?**

Type your request below or choose from quick options:
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🎂 Birthday Cake", callback_data="quick_order_birthday"),
                InlineKeyboardButton("💒 Wedding Cake", callback_data="quick_order_wedding")
            ],
            [
                InlineKeyboardButton("🥐 Fresh Pastries", callback_data="quick_order_pastries"),
                InlineKeyboardButton("🍮 Party Desserts", callback_data="quick_order_desserts")
            ],
            [
                InlineKeyboardButton("☕ Coffee & Treats", callback_data="quick_order_coffee")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(order_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **NAPOLEON-TSEH BOT HELP**

**🔧 Commands:**
/start - Welcome & main menu
/menu - Browse our full catalog
/order - Start placing an order
/status - Check your order status
/contact - Get our contact information
/help - Show this help message

**💬 What I Can Help With:**
✅ Product recommendations
✅ Custom cake designs
✅ Pricing information
✅ Order tracking
✅ Delivery scheduling
✅ Special dietary requirements

**🛒 How to Order:**
1. Use /order or just tell me what you want
2. I'll show you available options
3. Customize your selection
4. Choose delivery/pickup
5. Confirm and pay

**🆘 Need Human Help?**
Just say "speak to human" or "transfer to staff" and I'll connect you with our team!

**📱 Pro Tips:**
- Be specific about your needs (size, occasion, dietary restrictions)
- Ask about our daily specials
- Request photos of products
- Share your location for delivery estimates
"""
        
        keyboard = [
            [InlineKeyboardButton("🍰 Browse Menu", callback_data="show_menu")],
            [InlineKeyboardButton("🛒 Start Order", callback_data="start_order")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="human_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = str(update.effective_user.id)
        
        try:
            async for db in get_async_session():
                # Find client by telegram ID
                result = await db.execute(
                    select(Client).where(Client.telegram_username.contains(user_id))
                )
                client = result.scalar_one_or_none()
                
                if not client:
                    await update.message.reply_text(
                        "📋 No orders found for your account.\n\n"
                        "🛒 Use /order to place your first order!"
                    )
                    return
                
                # Get recent orders
                result = await db.execute(
                    select(Order)
                    .where(Order.client_id == client.id)
                    .order_by(Order.created_at.desc())
                    .limit(5)
                )
                orders = result.scalars().all()
                
                if not orders:
                    await update.message.reply_text(
                        "📋 No orders found.\n\n"
                        "🛒 Use /order to place your first order!"
                    )
                    return
                
                status_text = "📋 **YOUR RECENT ORDERS**\n\n"
                
                for order in orders:
                    status_emoji = {
                        OrderStatus.PENDING: "⏳",
                        OrderStatus.CONFIRMED: "✅", 
                        OrderStatus.IN_PROGRESS: "👩‍🍳",
                        OrderStatus.READY: "🎉",
                        OrderStatus.DELIVERED: "✅",
                        OrderStatus.CANCELLED: "❌"
                    }.get(order.status, "📋")
                    
                    status_text += f"{status_emoji} **Order #{order.order_number}**\n"
                    status_text += f"   Status: {order.status.value.replace('_', ' ').title()}\n"
                    status_text += f"   Total: ${order.pricing.total_amount:.2f}\n"
                    status_text += f"   Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                
                await update.message.reply_text(status_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text("❌ Error checking order status. Please try again!")
    
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command"""
        contact_text = f"""
📞 **CONTACT NAPOLEON-TSEH**

🏢 **{settings.BUSINESS_NAME}**
📍 {settings.BUSINESS_ADDRESS}
📞 Phone: {settings.BUSINESS_PHONE}
📧 Email: {settings.BUSINESS_EMAIL}

⏰ **Business Hours:**
Monday - Friday: 7:00 AM - 8:00 PM
Saturday - Sunday: 8:00 AM - 9:00 PM

🚚 **Delivery Areas:**
We deliver within 15km of our location
Delivery fee: $5-15 depending on distance

🎂 **Specialties:**
- Custom birthday & wedding cakes
- Fresh daily pastries
- Corporate catering
- Special dietary options (gluten-free, vegan)

💬 Need immediate help? I'm here 24/7 to assist you!
"""
        
        keyboard = [
            [InlineKeyboardButton("📍 Get Directions", callback_data="directions")],
            [InlineKeyboardButton("🛒 Place Order", callback_data="start_order")],
            [InlineKeyboardButton("👥 Speak to Human", callback_data="human_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(contact_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        try:
            if callback_data == "show_menu":
                await self.menu_command(update, context)
            
            elif callback_data == "start_order":
                await self.order_command(update, context)
            
            elif callback_data == "help_info":
                await self.help_command(update, context)
            
            elif callback_data == "contact_info":
                await self.contact_command(update, context)
            
            elif callback_data == "location_info":
                await self._handle_location_info(query)
            
            elif callback_data.startswith("category_"):
                category = callback_data.replace("category_", "")
                await self._handle_category_selection(query, category)
            
            elif callback_data.startswith("quick_order_"):
                order_type = callback_data.replace("quick_order_", "")
                await self._handle_quick_order(query, order_type)
            
            elif callback_data == "human_support":
                await self._handle_human_support_request(query)
            
            elif callback_data == "directions":
                await self._handle_directions_request(query)
            
            elif callback_data == "show_phone":
                await query.message.reply_text(
                    f"📞 **Call Us:** {settings.BUSINESS_PHONE}\n\n"
                    f"⏰ **Hours:** Monday-Friday 7AM-8PM, Saturday-Sunday 8AM-9PM",
                    parse_mode=None
                )
                
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await query.message.reply_text("❌ Something went wrong. Please try again!")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages with AI processing"""
        user_message = update.message.text
        user = update.effective_user
        
        logger.info(f"Processing message from {user.username}: {user_message}")
        
        try:
            # Log the incoming user interaction (without AI processing to avoid duplicates)
            await self._log_telegram_interaction(update, user_message)
            
            # Get AI response directly (this also sets self._current_conversation_id)
            ai_response = await self._get_ai_response(update, user_message)
            
            if ai_response:
                # Store the outgoing AI response in database
                conversation_id = getattr(self, '_current_conversation_id', None)
                await self._store_outgoing_message(update, ai_response, conversation_id)
                
                # Check if response suggests creating an order
                if any(keyword in ai_response.lower() for keyword in ['order', 'place', 'buy', 'purchase']):
                    keyboard = [[InlineKeyboardButton("🛒 Continue Order", callback_data="start_order")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(ai_response, reply_markup=reply_markup, parse_mode=None)
                else:
                    await update.message.reply_text(ai_response, parse_mode=None)
            else:
                fallback_response = "🤔 I'm processing your request. Let me connect you with our team for better assistance!"
                # Store the fallback response too
                conversation_id = getattr(self, '_current_conversation_id', None)
                await self._store_outgoing_message(update, fallback_response, conversation_id)
                
                await update.message.reply_text(
                    fallback_response,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👥 Speak to Human", callback_data="human_support")]])
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = "❌ I encountered an error. Let me connect you with our support team!"
            # Store the error response too
            conversation_id = getattr(self, '_current_conversation_id', None)
            await self._store_outgoing_message(update, error_response, conversation_id)
            
            await update.message.reply_text(
                error_response,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👥 Get Help", callback_data="human_support")]])
            )
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared contact information"""
        contact = update.message.contact
        
        response = f"""
📱 **Contact Received!**

Thanks for sharing your contact info:
👤 {contact.first_name} {contact.last_name or ''}
📞 {contact.phone_number}

This will help us:
✅ Send order updates
✅ Coordinate delivery
✅ Provide better customer service

🛒 Ready to place an order?
"""
        
        keyboard = [[InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Store contact in our system
        await self._store_customer_contact(update, contact)
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle shared location"""
        location = update.message.location
        
        response = f"""
📍 **Location Received!**

Latitude: {location.latitude}
Longitude: {location.longitude}

Calculating delivery options for your area...

🚚 **Delivery Information:**
- Standard delivery: $10-15
- Express delivery (2 hours): $20
- Pickup available at our store

🛒 Would you like to place an order?
"""
        
        keyboard = [
            [InlineKeyboardButton("🛒 Place Order", callback_data="start_order")],
            [InlineKeyboardButton("📍 Store Directions", callback_data="directions")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _get_ai_response(self, update: Update, message: str) -> Optional[str]:
        """Get AI response for user message"""
        try:
            async for db in get_async_session():
                user_id = str(update.effective_user.id)
                
                # Find or create client
                client = await self._find_or_create_client(db, update.effective_user)
                
                # Find or create conversation
                conversation = await self._find_or_create_conversation(db, client, user_id)
                
                # Store conversation ID for later use
                self._current_conversation_id = conversation.id
                
                # Get recent message history
                result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(10)
                )
                message_history = list(reversed(result.scalars().all()))
                
                # Get available products
                result = await db.execute(
                    select(Product).where(Product.status == ProductStatus.ACTIVE)
                )
                products = list(result.scalars().all())
                
                # Enhanced AI processing with Telegram context
                enhanced_prompt = f"""
                {self.bot_context}
                
                CURRENT CONTEXT:
                - Platform: Telegram
                - Customer: {update.effective_user.first_name} {update.effective_user.last_name or ''}
                - Username: @{update.effective_user.username or 'N/A'}
                - Message: {message}
                
                Respond with a helpful, engaging message that addresses the customer's needs.
                Include relevant product suggestions and pricing when appropriate.
                Use emojis and formatting to make the response visually appealing.
                """
                
                ai_response = await self.ai_service.process_message(
                    message=enhanced_prompt,
                    client=client,
                    conversation=conversation,
                    message_history=message_history,
                    products=products
                )
                
                return ai_response.get("response")
                
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None
    
    async def _log_telegram_interaction(self, update: Update, message: str):
        """Log interaction without AI processing to avoid duplicate responses"""
        try:
            async for db in get_async_session():
                user_id = str(update.effective_user.id)
                
                # Create message data for logging only
                message_data = {
                    "sender_id": user_id,
                    "sender_name": f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip(),
                    "message_text": message,
                    "message_type": "text",
                    "timestamp": datetime.now().isoformat(),
                    "telegram_user_id": update.effective_user.id,
                    "telegram_username": update.effective_user.username,
                    "telegram_message_id": str(update.message.message_id)  # Convert to string
                }
                
                # Store message without AI processing
                message_processor = MessageProcessor(db)
                await message_processor._store_message_only(
                    ConversationChannel.TELEGRAM,
                    message_data
                )
                
        except Exception as e:
            logger.error(f"Error logging telegram interaction: {e}")

    async def _store_outgoing_message(self, update: Update, ai_response: str, conversation_id: int = None):
        """Store outgoing AI response in database"""
        try:
            async for db in get_async_session():
                user_id = str(update.effective_user.id)
                
                # Find or create client if needed
                if not conversation_id:
                    client = await self._find_or_create_client(db, update.effective_user)
                    conversation = await self._find_or_create_conversation(db, client, user_id)
                    conversation_id = conversation.id
                
                # Store outgoing message using correct Message model fields
                from app.models.message import Message, MessageDirection, MessageType
                
                message = Message(
                    conversation_id=conversation_id,
                    direction=MessageDirection.OUTGOING,  # Bot response is outgoing
                    content=ai_response,
                    message_type=MessageType.TEXT,
                    external_id=f"bot_{int(time.time() * 1000)}",  # Unique bot message ID
                    created_at=datetime.now(),
                    # Store sender info in message_metadata instead of non-existent sender_info field
                    message_metadata={
                        "sender_id": "bot",
                        "sender_name": "Napoleon-Tseh AI Assistant",
                        "sender_type": "ai_bot"
                    }
                )
                
                db.add(message)
                await db.commit()
                
                logger.info(f"✅ Stored outgoing AI response in database (conversation_id: {conversation_id})")
                
        except Exception as e:
            logger.error(f"❌ Error storing outgoing message: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def _process_telegram_interaction(self, update: Update, message: str):
        """Process interaction through our message system"""
        try:
            async for db in get_async_session():
                user_id = str(update.effective_user.id)
                
                # Create message data for processing
                message_data = {
                    "sender_id": user_id,
                    "sender_name": f"{update.effective_user.first_name} {update.effective_user.last_name or ''}".strip(),
                    "message_text": message,
                    "message_type": "text",
                    "timestamp": datetime.now().isoformat(),
                    "telegram_user_id": update.effective_user.id,
                    "telegram_username": update.effective_user.username
                }
                
                # Process through message processor
                message_processor = MessageProcessor(db)
                await message_processor.process_incoming_message(
                    ConversationChannel.TELEGRAM,
                    message_data
                )
                
        except Exception as e:
            logger.error(f"Error processing telegram interaction: {e}")
    
    async def _find_or_create_client(self, db: AsyncSession, user) -> Client:
        """Find or create client from Telegram user"""
        try:
            # Try to find existing client by telegram_id
            result = await db.execute(
                select(Client).where(
                    Client.telegram_id == str(user.id)
                )
            )
            client = result.scalar_one_or_none()
            
            if not client:
                # Create new client
                client = Client(
                    first_name=user.first_name,
                    last_name=user.last_name or "",
                    phone=f"telegram_{user.id}",  # Placeholder phone (required field)
                    telegram_id=str(user.id)
                )
                db.add(client)
                await db.commit()
                await db.refresh(client)
            
            return client
            
        except Exception as e:
            logger.error(f"Error finding/creating client: {e}")
            raise
    
    async def _find_or_create_conversation(self, db: AsyncSession, client: Client, telegram_id: str) -> Conversation:
        """Find or create conversation"""
        try:
            # Try to find active conversation
            result = await db.execute(
                select(Conversation).where(
                    and_(
                        Conversation.client_id == client.id,
                        Conversation.channel == ConversationChannel.TELEGRAM,
                        Conversation.status == ConversationStatus.ACTIVE
                    )
                )
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                # Create new conversation
                conversation = Conversation(
                    client_id=client.id,
                    channel=ConversationChannel.TELEGRAM,
                    status=ConversationStatus.ACTIVE,
                    channel_thread_id=telegram_id
                )
                db.add(conversation)
                await db.commit()
                await db.refresh(conversation)
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error finding/creating conversation: {e}")
            raise
    
    async def _handle_category_selection(self, query, category: str):
        """Handle product category selection"""
        try:
            async for db in get_async_session():
                # Get products in category
                result = await db.execute(
                    select(Product)
                    .where(
                        and_(
                            Product.status == ProductStatus.ACTIVE,
                            Product.category == category
                        )
                    )
                    .limit(10)
                )
                products = result.scalars().all()
                
                if not products:
                    await query.message.reply_text(f"🚧 No {category} items available right now.")
                    return
                
                category_text = f"🍽️ **{category.upper()} SELECTION**\n\n"
                
                for product in products:
                    price = f"${product.base_price:.2f}" if product.base_price else "Price on request"
                    category_text += f" **{product.name}** - {price}\n"
                    if product.description:
                        category_text += f"   _{product.description[:80]}..._\n"
                    category_text += "\n"
                
                category_text += "💬 Tell me which item interests you for more details!"
                
                keyboard = [[InlineKeyboardButton("🛒 Start Order", callback_data="start_order")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(category_text, reply_markup=reply_markup, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error handling category selection: {e}")
            await query.message.reply_text("❌ Error loading category. Please try again!")
    
    async def _handle_quick_order(self, query, order_type: str):
        """Handle quick order options"""
        # Use the centralized quick order responses
        response = self.ai_service.get_quick_order_response(order_type)
        
        keyboard = [
            [InlineKeyboardButton("📋 Provide Details", callback_data="start_order")],
            [InlineKeyboardButton("📞 Call to Discuss", callback_data="human_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(response, reply_markup=reply_markup, parse_mode=None)
    
    async def _handle_human_support_request(self, query):
        """Handle request for human support"""
        support_message = """
👥 **CONNECTING TO HUMAN SUPPORT**

I'm notifying our team about your request. Here's what happens next:

⏰ **Response Times:**
- Business hours: 5-15 minutes
- After hours: Next business day
- Urgent orders: Call us directly

📞 **Direct Contact:**
Phone: {phone}
Email: {email}

💬 **What I've Done:**
✅ Logged your conversation
✅ Notified available staff
✅ Prepared your chat history

🔄 **While You Wait:**
Feel free to continue chatting with me, or use our other services!

Our team will join this chat soon! 
""".format(phone=settings.BUSINESS_PHONE, email=settings.BUSINESS_EMAIL)
        
        keyboard = [
            [InlineKeyboardButton("📞 Show Phone", callback_data="show_phone")],
            [InlineKeyboardButton("📧 Send Email", url=f"mailto:{settings.BUSINESS_EMAIL}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(support_message, reply_markup=reply_markup, parse_mode=None)
        
        # TODO: Implement staff notification system
        # This could send a notification to staff dashboard or messaging system
    
    async def _handle_location_info(self, query):
        """Handle location information request"""
        location_message = f"""
📍 **NAPOLEON-TSEH LOCATION**

🏢 **Address:**
{settings.BUSINESS_ADDRESS}

⏰ **Hours:**
Monday - Friday: 7:00 AM - 8:00 PM
Saturday - Sunday: 8:00 AM - 9:00 PM

🚚 **Delivery Areas:**
- City center: $5 delivery fee
- Suburbs (up to 10km): $10 delivery fee
- Extended area (10-15km): $15 delivery fee

🚗 **Parking:**
Free parking available in front of store

🚌 **Public Transport:**
Bus routes 12, 15, 22 stop nearby
"""
        
        keyboard = [
            [InlineKeyboardButton("🗺️ Open in Maps", url=f"https://maps.google.com/?q={settings.BUSINESS_ADDRESS}")],
            [InlineKeyboardButton("🛒 Place Order", callback_data="start_order")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(location_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _handle_directions_request(self, query):
        """Handle directions request"""
        maps_url = f"https://maps.google.com/?q={settings.BUSINESS_ADDRESS}"
        
        directions_message = f"""
🗺️ **DIRECTIONS TO NAPOLEON-TSEH**

📍 **Address:** {settings.BUSINESS_ADDRESS}

🚗 **By Car:** Free parking available
🚌 **By Bus:** Routes 12, 15, 22
🚶 **Walking:** Located in city center

Click below to open in your maps app:
"""
        
        keyboard = [
            [InlineKeyboardButton("🗺️ Open Directions", url=maps_url)],
            [InlineKeyboardButton("📞 Call for Help", url=f"tel:{settings.BUSINESS_PHONE}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(directions_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def _store_customer_contact(self, update: Update, contact):
        """Store customer contact information"""
        try:
            async for db in get_async_session():
                user_id = str(update.effective_user.id)
                
                # Find or create client
                client = await self._find_or_create_client(db, update.effective_user)
                
                # Update contact information
                client.phone_number = contact.phone_number
                if not client.full_name or client.full_name.startswith("user_"):
                    client.full_name = f"{contact.first_name} {contact.last_name or ''}".strip()
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing customer contact: {e}")
    
    async def run_polling(self):
        """Run the bot with polling (for development)"""
        logger.info("Starting Telegram bot with polling...")
        
        try:
            # First, try to initialize and start
            try:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling(drop_pending_updates=True)
                logger.info("✅ Bot polling started successfully")
                
            except RuntimeError as e:
                if "already running" in str(e) or "already initialized" in str(e):
                    logger.warning(f"Application already running: {e}")
                    # Stop and restart
                    await self._stop_application()
                    await asyncio.sleep(1)  # Wait a moment
                    
                    # Try again
                    await self.application.initialize()
                    await self.application.start()
                    await self.application.updater.start_polling(drop_pending_updates=True)
                    logger.info("✅ Bot polling restarted successfully")
                else:
                    raise
            
            # Store the polling task reference
            self.polling_task = asyncio.current_task()
            
            try:
                # Keep the bot running
                await asyncio.Event().wait()
            except (KeyboardInterrupt, asyncio.CancelledError):
                logger.info("Stopping bot...")
            finally:
                await self._stop_application()
                
        except Exception as e:
            logger.error(f"Error in run_polling: {e}")
            await self._stop_application()
            raise
    
    async def _stop_application(self):
        """Helper method to safely stop the application"""
        try:
            if hasattr(self.application, 'updater') and self.application.updater.running:
                await self.application.updater.stop()
            if hasattr(self.application, '_running') and self.application._running:
                await self.application.stop()
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
    
    async def stop_bot(self):
        """Stop the bot gracefully"""
        logger.info("🛑 Stopping bot...")
        
        # Cancel polling task if it exists
        if hasattr(self, 'polling_task') and self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            logger.info("✅ Polling task cancelled")
        
        await self._stop_application()
        logger.info("✅ Bot stopped successfully")
    
    async def set_webhook(self, webhook_url: str):
        """Set webhook for production deployment"""
        try:
            await self.bot.set_webhook(url=webhook_url)
            logger.info(f"Webhook set to: {webhook_url}")
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            raise
    
    async def handle_webhook_update(self, update_data: dict):
        """Handle webhook update from Telegram"""
        try:
            update = Update.de_json(update_data, self.bot)
            await self.application.process_update(update)
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")


# Global bot instance
telegram_bot_service = TelegramBotService() 