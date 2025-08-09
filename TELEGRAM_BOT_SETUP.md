# 🤖 Napoleon-Tseh Telegram Bot Setup Guide

This guide will help you set up the AI-powered Telegram bot for Napoleon-Tseh bakery management system.

## 🎯 **Features**

✅ **AI-Powered Customer Service** - OpenAI GPT integration for natural conversations  
✅ **Order Management** - Complete order taking and processing  
✅ **Menu Display** - Interactive product catalog browsing  
✅ **Multi-language Support** - Responds in customer's preferred language  
✅ **Payment Integration** - Ready for payment processing integration  
✅ **Admin Management** - Staff notifications and human handover  
✅ **Analytics & Reporting** - Conversation tracking and insights  

## 🛠️ **Prerequisites**

- **Telegram Account** - For creating the bot
- **OpenAI API Key** - For AI-powered responses
- **Running Backend** - Napoleon-Tseh FastAPI backend
- **PostgreSQL Database** - For conversation and order storage

## 📋 **Step 1: Create Telegram Bot**

### 1.1 Contact BotFather
1. Open Telegram and search for `@BotFather`
2. Start a conversation with `/start`
3. Create new bot with `/newbot`
4. Choose a name: `Napoleon-Tseh Bakery Bot`
5. Choose a username: `napoleon_tseh_bot` (must end with `_bot`)

### 1.2 Get Bot Token
```
✅ Congratulations! You've created a bot!
🔑 Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```
**⚠️ IMPORTANT**: Keep this token secret!

### 1.3 Configure Bot Settings
```bash
# Set bot description
/setdescription
Napoleon-Tseh AI assistant for ordering delicious cakes, pastries, and desserts. Available 24/7 to help with orders, menu information, and customer service.

# Set bot about text
/setabouttext
AI-powered bakery assistant for Napoleon-Tseh. Order custom cakes, browse our menu, and get instant customer support!

# Set bot commands
/setcommands
start - Welcome message and main menu
menu - Browse our product catalog
order - Start placing an order
status - Check your order status
contact - Get our contact information
help - Bot help and commands
```

## 🔧 **Step 2: Backend Configuration**

### 2.1 Environment Variables
Add these to your `.env` file:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/api/v1/webhooks/telegram

# OpenAI Configuration (if not already set)
OPENAI_API_KEY=sk-your-openai-api-key-here
AI_MODEL=gpt-3.5-turbo
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=500

# Business Information (update with your details)
BUSINESS_NAME=Napoleon-Tseh
BUSINESS_PHONE=+1-555-123-4567
BUSINESS_EMAIL=orders@napoleon-tseh.com
BUSINESS_ADDRESS=123 Bakery Street, Sweet City, SC 12345
```

### 2.2 Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt
```

## 🚀 **Step 3: Development Setup**

### 3.1 Run Bot in Development Mode
```bash
# Start the backend first
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a new terminal, run the Telegram bot
python app/scripts/run_telegram_bot.py
```

### 3.2 Test Your Bot
1. Open Telegram
2. Search for your bot username: `@napoleon_tseh_bot`
3. Send `/start` to begin
4. Try commands like `/menu`, `/order`, `/help`

## 🌐 **Step 4: Production Deployment**

### 4.1 Set Up Webhooks
For production, use webhooks instead of polling:

```bash
# Set webhook URL (replace with your domain)
curl -X POST "http://localhost:8000/api/v1/webhooks/telegram/set_webhook" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://yourdomain.com/api/v1/webhooks/telegram"}'

# Check webhook status
curl "http://localhost:8000/api/v1/webhooks/telegram/webhook_info"
```

### 4.2 SSL Certificate
**Important**: Telegram requires HTTPS for webhooks!

```bash
# Using Let's Encrypt with Certbot
sudo certbot --nginx -d yourdomain.com

# Or use a reverse proxy like Nginx
sudo nano /etc/nginx/sites-available/napoleon-tseh
```

Example Nginx configuration:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location /api/v1/webhooks/telegram {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🎨 **Step 5: Customization**

### 5.1 Update Business Information
The system uses a centralized prompts file for better maintainability. Edit `app/prompts/telegram_bot_prompts.py`:

```python
# In TelegramBotPrompts.get_business_context() method, update:
- Name: {settings.BUSINESS_NAME}
- Phone: {settings.BUSINESS_PHONE}  
- Email: {settings.BUSINESS_EMAIL}
- Address: {settings.BUSINESS_ADDRESS}

# Update business hours, pricing, and product information
# Update delivery areas and policies
# Customize communication style and guidelines
```

### 5.2 Customize AI Responses
The prompts are now organized in a dedicated file structure:

```
app/prompts/
├── __init__.py
└── telegram_bot_prompts.py    # Main prompts and templates
```

**Key customization areas:**

```python
# Update product catalog in get_business_context()
🎂 CAKES:
- Your cake types and pricing
- Available flavors and decorations

🥐 PASTRIES:
- Your pastry selection
- Bulk pricing options

# Customize FAQ responses in get_knowledge_base()
Q: Your specific business questions
A: Your answers and policies

# Update quick order responses in get_quick_order_responses()
"birthday": "Your custom birthday cake order flow"
"wedding": "Your custom wedding cake consultation process"
```

### 5.3 Add Custom Commands
Edit `app/services/telegram_bot_service.py`:

```python
# Add new command handlers:
self.application.add_handler(CommandHandler("specials", self.specials_command))
self.application.add_handler(CommandHandler("catering", self.catering_command))

async def specials_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /specials command"""
    specials_text = self.ai_service.get_daily_specials()  # Add this method
    await update.message.reply_text(specials_text, parse_mode='Markdown')
```

### 5.4 Customize Response Templates
Edit `TelegramBotTemplates` class in the prompts file:

```python
@staticmethod
def format_seasonal_special(item_name: str, price: float, description: str) -> str:
    """Format seasonal special offers"""
    return f"""
🌟 **TODAY'S SPECIAL** 🌟

🔸 **{item_name}** - ${price:.2f}
   _{description}_
   
⏰ Available today only!
"""
```

## 📊 **Step 6: Analytics & Monitoring**

### 6.1 Bot Analytics Dashboard
Access conversation analytics at:
- **Frontend**: http://localhost:3000/conversations
- **API**: http://localhost:8000/api/v1/conversations

### 6.2 Monitor Bot Performance
```bash
# Check webhook status
curl "http://localhost:8000/api/v1/webhooks/telegram/webhook_info"

# View recent conversations
curl "http://localhost:8000/api/v1/conversations?channel=telegram&limit=10"

# Check message processing stats
curl "http://localhost:8000/api/v1/messages/stats"
```

### 6.3 Logs and Debugging
```bash
# View bot logs
tail -f app.log | grep telegram

# Check for errors
grep ERROR app.log | grep telegram
```

## 🔄 **Step 7: Advanced Features**

### 7.1 Payment Integration
```python
# Add payment handler to telegram_bot_service.py
from telegram import LabeledPrice, PreCheckoutQuery

async def handle_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process payment through Telegram Payments"""
    # Implementation for Stripe/PayPal integration
```

### 7.2 RAG Integration (Future Enhancement)
```python
# Prepare for vector database integration
from app.services.rag_service import RAGService

class TelegramBotService:
    def __init__(self):
        # Add RAG service
        self.rag_service = RAGService()
        
    async def _get_ai_response_with_rag(self, message: str, context: dict):
        """Enhanced AI response with RAG"""
        # Retrieve relevant documents
        relevant_docs = await self.rag_service.retrieve(message)
        
        # Enhance context with retrieved information
        enhanced_context = self._build_rag_context(context, relevant_docs)
        
        # Generate response with enhanced context
        return await self.ai_service.process_message(
            message=message,
            context=enhanced_context
        )
```

### 7.3 Multi-language Support
```python
# Add language detection and translation
from googletrans import Translator

async def detect_and_respond(self, message: str, user_language: str):
    """Detect language and respond appropriately"""
    if user_language != 'en':
        # Translate to English for processing
        translated = await self.translator.translate(message, dest='en')
        
        # Process with AI
        response = await self.ai_service.process_message(translated.text)
        
        # Translate response back to user language
        final_response = await self.translator.translate(response, dest=user_language)
        return final_response.text
    
    return await self.ai_service.process_message(message)
```

## 🛡️ **Security Best Practices**

### 1. Environment Security
```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use environment variable validation
python -c "from app.core.config import settings; print('✅ Configuration valid')"
```

### 2. Rate Limiting
```python
# Implement rate limiting for bot messages
from slowapi import Limiter

@router.post("/telegram")
@limiter.limit("100/minute")
async def telegram_webhook(request: Request, webhook_data: Dict[str, Any]):
    # Webhook implementation
```

### 3. Input Validation
```python
# Validate all incoming messages
def validate_telegram_update(update_data: dict) -> bool:
    """Validate Telegram webhook data"""
    required_fields = ["update_id"]
    return all(field in update_data for field in required_fields)
```

## 🆘 **Troubleshooting**

### Common Issues:

**1. Bot Not Responding**
```bash
# Check bot token
python -c "from app.core.config import settings; print(f'Token: {settings.TELEGRAM_BOT_TOKEN[:10]}...')"

# Test bot connection
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

**2. Webhook Issues**
```bash
# Delete existing webhook
curl -X DELETE "http://localhost:8000/api/v1/webhooks/telegram/webhook"

# Set new webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/telegram/set_webhook" \
  -d '{"webhook_url": "https://yourdomain.com/api/v1/webhooks/telegram"}'
```

**3. AI Not Working**
```bash
# Check OpenAI API key
python -c "from app.services.ai_service import AIService; print('✅ AI service initialized')"

# Test AI directly
curl -X POST "http://localhost:8000/api/v1/ai/test" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me?"}'
```

**4. Database Connection**
```bash
# Check database connection
python -c "from app.core.database import get_async_session; print('✅ Database connected')"

# Check conversation table
psql napoleon_tseh -c "SELECT COUNT(*) FROM conversations WHERE channel = 'telegram';"
```

## 📚 **Resources**

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **python-telegram-bot**: https://python-telegram-bot.readthedocs.io/
- **OpenAI API**: https://platform.openai.com/docs
- **FastAPI Webhooks**: https://fastapi.tiangolo.com/advanced/events/

## 🎉 **Next Steps**

1. **Test thoroughly** - Try various conversation scenarios
2. **Customize responses** - Tailor AI responses to your business
3. **Add payment processing** - Integrate with Stripe/PayPal
4. **Implement RAG** - Add knowledge base for better responses
5. **Monitor performance** - Set up analytics and alerts
6. **Train staff** - Teach team how to handle escalated conversations

---

🎂 **Happy baking with AI assistance!** 🤖

For support, contact the development team or check the project documentation. 