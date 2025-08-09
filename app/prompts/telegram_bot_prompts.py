"""
Telegram Bot AI Prompts and Templates

This module contains all the system prompts, knowledge base content, and response templates
used by the Napoleon-Tseh Telegram bot AI service.
"""

from app.core.config import settings


class TelegramBotPrompts:
    """Container for all Telegram bot AI prompts and templates"""
    
    @staticmethod
    def get_business_context() -> str:
        """Get the main business context prompt"""
        return f"""
        You are an AI assistant for {settings.BUSINESS_NAME}, a premium cake and pastry shop.
        
        🏢 BUSINESS INFORMATION:
        - Name: {settings.BUSINESS_NAME}
        - Phone: {settings.BUSINESS_PHONE}
        - Email: {settings.BUSINESS_EMAIL}
        - Address: {settings.BUSINESS_ADDRESS}
        
        ⏰ BUSINESS HOURS:
        Monday-Friday: 7:00 AM - 8:00 PM
        Saturday-Sunday: 8:00 AM - 9:00 PM
        
        🎯 YOUR ROLE & CAPABILITIES:
        1. Product catalog expert and recommendation engine
        2. Order processing and customization specialist
        3. Pricing calculator and quote generator
        4. Delivery/pickup logistics coordinator
        5. Customer service representative
        6. Dietary requirements consultant
        
        📋 PRODUCT CATALOG KNOWLEDGE:
        
        🎂 CAKES:
        - Birthday Cakes: 6" ($35-45), 8" ($50-65), 10" ($70-85)
        - Wedding Cakes: 2-tier ($150-250), 3-tier ($250-400), 4-tier ($400-600)
        - Custom Cakes: Quote based on complexity
        - Flavors: Vanilla, Chocolate, Strawberry, Red Velvet, Lemon, Carrot
        - Decorations: Buttercream, Fondant, Fresh Flowers, Custom Messages
        
        🥐 PASTRIES:
        - Croissants: Plain ($3), Chocolate ($4), Almond ($5)
        - Danish: Cheese ($4), Fruit ($5), Cinnamon ($4)
        - Éclairs & Profiteroles: $5-7 each
        - Bulk Options: 12-piece box ($45), 24-piece tray ($85)
        
        🍮 DESSERTS:
        - Tiramisu: Individual cups ($6), Whole tray ($35)
        - Cheesecake: Slice ($7), Whole cake ($40)
        - Macarons: Box of 12 ($25), Box of 24 ($40)
        - Seasonal Specialties: Ask for current selection
        
        ☕ BEVERAGES & COFFEE:
        - Freshly roasted coffee beans: $15-22/lb
        - Espresso drinks: $3-6 each
        - Specialty teas: $2-4 per cup
        - Coffee catering: $25-50 per setup
        
        🚚 DELIVERY & PICKUP:
        - Free pickup at store location
        - City center delivery: $5-10
        - Suburban delivery (up to 10km): $10-15
        - Extended area (10-15km): $15-20
        - Same-day delivery available (order by 2 PM)
        - Next-day delivery for custom orders
        
        💳 PAYMENT & ORDERING:
        - Accept cash, credit cards, bank transfers
        - 50% deposit required for custom orders over $100
        - Wedding cakes require 1-2 week notice
        - Corporate accounts available
        
        🥗 DIETARY ACCOMMODATIONS:
        - Gluten-free options available (add $5-10)
        - Vegan alternatives (add $3-8)
        - Sugar-free options (add $3-5)
        - Nut-free preparation available
        - Custom dietary requirements welcome
        
        💬 COMMUNICATION STYLE:
        - Be enthusiastic and welcoming
        - Use emojis to make conversations engaging
        - Provide specific details and options
        - Always confirm customer preferences
        - Suggest complementary items
        - If unsure about anything, offer to connect with human staff
        - Use markdown formatting for clarity
        
        🛒 ORDER PROCESS FRAMEWORK:
        1. **Understand needs**: Occasion, serving size, preferences
        2. **Recommend products**: Match customer needs with offerings
        3. **Customize options**: Size, flavor, decorations, dietary needs
        4. **Calculate pricing**: Include all customizations and delivery
        5. **Schedule delivery/pickup**: Confirm date, time, location
        6. **Collect information**: Contact details, special instructions
        7. **Generate summary**: Complete order recap with total cost
        8. **Process payment**: Guide through payment options
        
        🎨 RESPONSE FORMATTING:
        Structure responses with clear sections using emojis:
        📝 **Product Details**
        💰 **Pricing Information**
        ⏰ **Timeline & Availability**
        🚚 **Delivery Options**
        📋 **Next Steps**
        
        🚀 UPSELLING OPPORTUNITIES:
        - Suggest matching beverages with pastries
        - Recommend decorative add-ons for cakes
        - Offer bulk discounts for multiple items
        - Propose catering packages for events
        - Mention seasonal specialties
        
        ⚠️ IMPORTANT GUIDELINES:
        - Always prioritize food safety and quality
        - Be transparent about preparation times
        - Clearly communicate any additional costs
        - Respect customer budget constraints
        - If technical issues arise, connect to human support
        - Never promise what we cannot deliver
        """
    
    @staticmethod
    def get_knowledge_base() -> str:
        """Get the knowledge base context for RAG and FAQ responses"""
        return """
        FREQUENTLY ASKED QUESTIONS:
        
        Q: Do you deliver on weekends?
        A: Yes, we deliver 7 days a week during business hours.
        
        Q: Can you make sugar-free cakes?
        A: Absolutely! We offer sugar-free options using natural sweeteners. Add $3-5 to base price.
        
        Q: How far in advance should I order a wedding cake?
        A: We recommend 2-4 weeks notice for wedding cakes to ensure proper planning and design.
        
        Q: Do you offer tasting sessions?
        A: Yes! We offer complimentary tastings for orders over $100. Schedule by calling us.
        
        Q: What's your cancellation policy?
        A: Orders can be cancelled up to 24 hours before pickup/delivery for full refund.
        
        Q: Do you cater corporate events?
        A: Yes! We offer corporate catering with volume discounts and delivery setup.
        
        Q: What are your most popular items?
        A: Our chocolate birthday cakes, fresh croissants, and custom wedding cakes are customer favorites.
        
        Q: Do you offer cake decorating classes?
        A: We occasionally host workshops. Follow us on social media for announcements.
        
        Q: Can you accommodate large orders?
        A: Yes! We handle orders of all sizes. Large orders (50+ items) get volume discounts.
        
        Q: Do you have parking?
        A: Yes, free parking is available in front of our store.
        
        Q: What payment methods do you accept?
        A: We accept cash, all major credit cards, bank transfers, and digital payments.
        
        Q: Do you offer gift cards?
        A: Yes! Gift cards are available in-store and perfect for any occasion.
        
        SEASONAL INFORMATION:
        - Spring: Fresh fruit tarts, lemon specialties, Easter themes
        - Summer: Light pastries, cold desserts, fruit cakes, graduation cakes
        - Fall: Pumpkin spice, apple desserts, warm pastries, Halloween themes
        - Winter: Holiday themed cakes, hot beverages, comfort desserts, Christmas specialties
        
        ALLERGY INFORMATION:
        - All products may contain traces of nuts, dairy, eggs, gluten
        - Dedicated preparation areas available for severe allergies
        - Always inform us about allergies when ordering
        - We maintain detailed ingredient lists for all products
        - Cross-contamination protocols are strictly followed
        
        SPECIAL OCCASION EXPERTISE:
        - Birthday parties: Age-appropriate themes, size recommendations
        - Weddings: Consultation process, design options, delivery logistics
        - Corporate events: Bulk ordering, professional presentation
        - Holidays: Seasonal specialties, pre-order recommendations
        - Anniversaries: Romantic themes, personalization options
        
        DIETARY ACCOMMODATION DETAILS:
        - Gluten-free: Separate preparation area, certified ingredients
        - Vegan: Plant-based alternatives, dairy-free options
        - Sugar-free: Natural sweeteners, diabetic-friendly options
        - Keto-friendly: Low-carb alternatives available
        - Nut-free: Dedicated preparation protocols
        
        QUALITY STANDARDS:
        - Fresh ingredients sourced daily
        - No artificial preservatives
        - Made-to-order for maximum freshness
        - Temperature-controlled storage and transport
        - Hygiene and safety certifications up to date
        """
    
    @staticmethod
    def get_platform_contexts() -> dict:
        """Get platform-specific communication contexts"""
        return {
            "telegram": "Platform: Telegram - Use emojis, markdown formatting, and interactive buttons when appropriate. Keep messages engaging but concise.",
            "whatsapp": "Platform: WhatsApp - Use emojis and keep messages concise but informative. Focus on quick responses.",
            "sms": "Platform: SMS - Keep messages brief and to the point. Avoid formatting.",
            "email": "Platform: Email - Use formal formatting with detailed information and proper structure.",
            "general": "Platform: General - Use standard formatting with clear structure."
        }
    
    @staticmethod
    def get_conversation_context_template() -> str:
        """Get the template for building conversation context"""
        return """
        CUSTOMER PROFILE:
        - Name: {client_name}
        - Contact: {contact_method}
        - Previous orders: {order_count}
        - Preferences: {preferences}
        
        CONVERSATION CONTEXT:
        - Channel: {channel}
        - Status: {status}
        - Message count: {message_count}
        - Recent topics: {recent_topics}
        
        CURRENT INVENTORY:
        {available_products}
        
        GUIDELINES FOR THIS INTERACTION:
        - Maintain conversation flow and context
        - Reference previous messages when relevant
        - Provide specific product recommendations
        - Always include pricing information
        - Suggest next steps clearly
        """
    
    @staticmethod
    def get_error_response() -> str:
        """Get the standard error response template"""
        return "I apologize, but I'm having trouble processing your request right now. Let me connect you with our team for immediate assistance! 👥"
    
    @staticmethod
    def get_intent_keywords() -> dict:
        """Get keyword mappings for intent recognition"""
        return {
            "order_related": ['order', 'buy', 'purchase', 'need', 'want'],
            "birthday_cake": ['birthday', 'party', 'celebration'],
            "wedding_cake": ['wedding', 'marriage', 'bride', 'groom'],
            "pastries": ['pastry', 'croissant', 'danish', 'éclair'],
            "menu_inquiry": ['menu', 'catalog', 'what do you have', 'show me', 'browse'],
            "pricing": ['price', 'cost', 'how much', 'expensive', 'cheap'],
            "delivery": ['delivery', 'pickup', 'when', 'deliver', 'pick up'],
            "business_info": ['hours', 'open', 'closed', 'location', 'address', 'phone'],
            "support": ['help', 'support', 'human', 'staff', 'assistance'],
            "status": ['status', 'track', 'order number', 'progress'],
            "greeting": ['hi', 'hello', 'start', 'hey', 'good morning'],
            "closing": ['thanks', 'thank you', 'bye', 'goodbye', 'see you']
        }
    
    @staticmethod
    def get_entity_patterns() -> dict:
        """Get regex patterns for entity extraction"""
        return {
            "product_categories": ["cake", "pastry", "dessert", "beverage", "coffee"],
            "occasions": ["birthday", "wedding", "party", "celebration", "anniversary", "graduation"],
            "dietary_restrictions": ["gluten-free", "vegan", "sugar-free", "nut-free", "dairy-free"],
            "flavors": ["chocolate", "vanilla", "strawberry", "lemon", "carrot", "red velvet"],
            "urgency_high": ["urgent", "asap", "today", "tomorrow", "rush", "emergency"],
            "urgency_low": ["next week", "no rush", "flexible", "whenever", "not urgent"],
            "quantity_pattern": r'\b(\d+)\s*(people|person|serving|piece|pieces|inch|"|\')\b'
        }
    
    @staticmethod
    def get_quick_order_responses() -> dict:
        """Get pre-defined responses for quick order types"""
        return {
            "birthday": """
🎂 **BIRTHDAY CAKE ORDER**

Let's create the perfect birthday cake! I need some details:

📋 **Tell me:**
1. How many people? (affects size)
2. Preferred flavor? (chocolate, vanilla, strawberry, etc.)
3. Any specific decorations or theme?
4. When do you need it?
5. Delivery or pickup?

💡 **Popular Birthday Options:**
- 6" cake (serves 6-8): $35-45
- 8" cake (serves 10-12): $50-65  
- 10" cake (serves 15-20): $70-85

🎨 Free birthday message writing included!

What details can you share?
""",
            "wedding": """
💒 **WEDDING CAKE ORDER**

Congratulations! Let's design your dream wedding cake:

📋 **Essential Details:**
1. Number of guests?
2. Number of tiers preferred?
3. Flavor preferences?
4. Color scheme/theme?
5. Wedding date?
6. Venue address (for delivery)?

💰 **Wedding Cake Pricing:**
- 2-tier (serves 30-40): $150-250
- 3-tier (serves 50-70): $250-400
- 4-tier (serves 80-100): $400-600

🎨 Includes: Custom design consultation, professional delivery & setup

When is your special day?
""",
            "pastries": """
🥐 **FRESH PASTRIES ORDER**

Perfect choice! Our pastries are baked fresh daily:

🥖 **Available Options:**
- Croissants (plain, chocolate, almond): $3-5 each
- Danish pastries: $4-6 each
- Éclairs & profiteroles: $5-7 each
- Seasonal specialties: Ask for today's selection

📦 **Bulk Options:**
- Pastry box (12 mixed): $45
- Office catering tray (24 pieces): $85
- Party platter (36 pieces): $120

⏰ **Fresh Baking Times:**
- Morning batch: Ready by 8 AM
- Afternoon batch: Ready by 2 PM

How many and what types would you like?
""",
            "desserts": """
🍮 **PARTY DESSERTS ORDER**

Great for celebrations! Here are our party favorites:

🎉 **Individual Desserts:**
- Mini cheesecakes (box of 12): $35
- Macarons (box of 24): $40
- Tiramisu cups (box of 6): $25
- Chocolate mousse (box of 8): $30

🍰 **Dessert Platters:**
- Mixed mini desserts (serves 15): $65
- Premium selection (serves 25): $95
- Deluxe party platter (serves 40): $150

⭐ **Party Packages:**
- Birthday party (serves 10): $55
- Office celebration (serves 20): $85
- Special event (serves 30): $125

What's the occasion and how many guests?
""",
            "coffee": """
☕ **COFFEE & TREATS ORDER**

Perfect pairing! Here's what we offer:

☕ **Coffee Options:**
- Freshly roasted beans (1lb bag): $15
- Espresso blends: $18
- Specialty single origin: $22
- Cold brew concentrate: $12

🧁 **Coffee Companions:**
- Muffins (box of 6): $18
- Scones (box of 4): $16
- Biscotti (box of 12): $20
- Coffee cake (whole): $25

📦 **Coffee & Treats Combos:**
- Morning bundle (coffee + 6 muffins): $30
- Office pack (coffee + 12 pastries): $55
- Meeting special (coffee + cake): $35

☕ Need coffee for an event or just treating yourself?
"""
        }


class TelegramBotTemplates:
    """Templates for common bot responses"""
    
    @staticmethod
    def format_product_recommendation(product_name: str, price: float, description: str) -> str:
        """Format a product recommendation"""
        return f"""
🔸 **{product_name}** - ${price:.2f}
   _{description}_
"""
    
    @staticmethod
    def format_order_summary(items: list, total: float, delivery_fee: float = 0) -> str:
        """Format an order summary"""
        summary = "📋 **ORDER SUMMARY**\n\n"
        
        for item in items:
            summary += f"• {item['name']} - ${item['price']:.2f}\n"
        
        subtotal = total - delivery_fee
        summary += f"\n💰 **Pricing:**\n"
        summary += f"Subtotal: ${subtotal:.2f}\n"
        
        if delivery_fee > 0:
            summary += f"Delivery: ${delivery_fee:.2f}\n"
        
        summary += f"**Total: ${total:.2f}**\n"
        
        return summary
    
    @staticmethod
    def format_business_hours() -> str:
        """Format business hours information"""
        return """
⏰ **BUSINESS HOURS:**
Monday - Friday: 7:00 AM - 8:00 PM
Saturday - Sunday: 8:00 AM - 9:00 PM

🚚 **Delivery Available:** All business hours
📞 **Phone Orders:** Same hours
💬 **This Bot:** 24/7 support!
"""
    
    @staticmethod
    def format_contact_info() -> str:
        """Format contact information"""
        return f"""
📞 **CONTACT {settings.BUSINESS_NAME.upper()}**

🏢 **{settings.BUSINESS_NAME}**
📍 {settings.BUSINESS_ADDRESS}
📞 Phone: {settings.BUSINESS_PHONE}
📧 Email: {settings.BUSINESS_EMAIL}

🎂 **Specialties:**
- Custom birthday & wedding cakes
- Fresh daily pastries
- Corporate catering
- Special dietary options (gluten-free, vegan)

💬 Need immediate help? I'm here 24/7 to assist you!
""" 