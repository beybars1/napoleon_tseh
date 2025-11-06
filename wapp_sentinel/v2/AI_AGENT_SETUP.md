# AI Agent Configuration Guide

## Environment Variables to Add

Add these variables to your `.env` file for AI agent functionality:

```bash
# Message Routing Configuration
# Comma-separated list of chat IDs that should be treated as managers
# Messages from these chats will go to order processing (existing flow)
MANAGER_CHAT_IDS=77028639438@c.us

# AI Agent Whitelist (for testing)
# Only messages from these chat IDs will be handled by AI agent
# Messages from other chats will be ignored (routed to manager queue but not processed)
AI_AGENT_CHAT_IDS=77006458263@c.us,77001234567@c.us

# Green API configuration (if not already set)
GREENAPI_INSTANCE=7105362159
GREENAPI_TOKEN=your_token_here
GREENAPI_BASE_URL=https://api.green-api.com
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

### Message Routing Logic:

1. **Manager Messages** (`MANAGER_CHAT_IDS`): Routed to order processing queue (existing flow)

2. **AI Agent Messages** (`AI_AGENT_CHAT_IDS`): Routed to AI agent for conversational order taking

3. **Other Messages**: Ignored (routed to manager queue but not processed)

### Testing:

**Test 1 - Manager Message:**
- Send from chat ID in `MANAGER_CHAT_IDS`
- Should go to `rabbitmq_worker.py` → `order_processor_worker.py` → Order table

**Test 2 - AI Agent Message:**
- Send from chat ID in `AI_AGENT_CHAT_IDS`
- Should go to `ai_agent_worker.py` → LangGraph → Conversation table
- AI should respond in WhatsApp

**Test 3 - Unknown Chat:**
- Send from chat ID NOT in either list
- Should be ignored (no processing, no AI response)

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
