# AI Agent Configuration Guide

## Environment Variables to Add

Add these variables to your `.env` file for AI agent functionality:

```bash
# AI Agent Configuration
# Comma-separated list of chat IDs that should be treated as managers
# Messages from these chats will go to order processing (existing flow)
# Messages from other chats will go to AI agent (new conversational flow)
MANAGER_CHAT_IDS=79001234567@c.us,79009876543@c.us

# Green API configuration (if not already set)
GREEN_API_URL=https://api.green-api.com/waInstance{YOUR_INSTANCE}/
GREEN_API_TOKEN=your_token_here
```

## Database Migration

Run the migration to create new tables:

```bash
cd /home/beybars/dev_python/napoleon_tseh/wapp_sentinel/v2
alembic upgrade head
```

This will create:
- `conversations` - Tracks AI agent conversations
- `conversation_messages` - Stores conversation history
- `ai_generated_orders` - Orders collected by AI agent

## Installing Dependencies

Install the new dependencies:

```bash
pip install langgraph langchain-openai langchain-core
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

## Running the AI Agent Worker

Start the AI agent worker in a separate terminal:

```bash
cd /home/beybars/dev_python/napoleon_tseh/wapp_sentinel/v2
python app/ai_agent_worker.py
```

## Testing the System

1. **Manager Flow (Existing)**: Messages from chat IDs listed in `MANAGER_CHAT_IDS` will continue to use the existing order processing flow

2. **Client Flow (New AI Agent)**: Messages from any other chat ID will be handled by the AI agent for conversational order taking

## Architecture

```
WhatsApp Message → FastAPI (/receiveNotification)
                       ↓
                [determine_message_type()]
                       ↓
        ┌──────────────┴──────────────┐
        ↓                              ↓
   Manager Chat                   Client Chat
        ↓                              ↓
greenapi_notifications          ai_agent_interactions
        ↓                              ↓
rabbitmq_worker.py              ai_agent_worker.py
        ↓                              ↓
order_processor_worker.py        LangGraph Agent
        ↓                              ↓
  Order in DB               Conversation in DB
                                   ↓
                            AIGeneratedOrder in DB
```

## Conversation Flow

The AI agent follows this flow:

1. **greet** - Welcome message
2. **collect_items** - Extract products from user message
3. **collect_delivery** - Get delivery date/time/address
4. **collect_payment** - Ask about payment status
5. **collect_contacts** - Get name and phone
6. **validate** - Check all data collected
7. **confirm** - Show summary, ask for confirmation
8. **save** - Save to database

The agent can handle:
- Clarification requests at any step
- Retries if information unclear
- Natural conversation flow
- Multiple retries with context preservation

## Monitoring

Check conversation status in database:

```sql
-- Active conversations
SELECT * FROM conversations WHERE status = 'active';

-- Conversation messages
SELECT c.chat_id, cm.role, cm.content, cm.timestamp 
FROM conversation_messages cm
JOIN conversations c ON cm.conversation_id = c.id
WHERE c.chat_id = 'YOUR_CHAT_ID'
ORDER BY cm.timestamp;

-- AI generated orders
SELECT * FROM ai_generated_orders WHERE validation_status = 'validated';
```
