# Napoleon Order Automation - MVP Setup Guide

## Quick Start (5 minutes)

### 1. Environment Setup
Create `.env` file with your credentials:
```bash
cp .env.example .env
# Edit .env with your actual values
```

Required variables:
- `GREEN_API_ID_INSTANCE` - Your GreenAPI instance ID
- `GREEN_API_TOKEN` - Your GreenAPI token  
- `OPENAI_API_KEY` - Your OpenAI API key
- `MAIN_GROUP_CHAT_ID` - Your main orders group chat ID (already set: `120363272114174001@g.us`)
- `OPERATIONAL_GROUP_CHAT_ID` - Your daily operations group chat ID

### 2. Start Database
```bash
docker-compose up -d postgres
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Test System
```bash
# Check if everything is configured
python test_mvp_workflow.py status

# Test order parsing
python test_mvp_workflow.py parse
```

### 5. Start API Server
```bash
uvicorn main:app --reload
```

### 6. Test Complete Workflow
```bash
# In another terminal
python test_mvp_workflow.py flow
```

## Current MVP Features ✅

1. **Automatic Message Processing**: Checks main group every 2 minutes
2. **Order Parsing**: Uses OpenAI to extract order details from Russian text
3. **Database Storage**: Saves all orders with metadata
4. **Manual Consolidation**: POST `/send-daily-orders` to generate daily summary
5. **Testing Mode**: Safe testing without sending real WhatsApp messages

## Usage Workflow

### Daily Operation:
1. **Morning**: POST `/send-daily-orders` to send today's orders to operational group
2. **Throughout Day**: System automatically processes new orders from main group
3. **Evening**: Check `/orders/today` to see all processed orders

### Manual Testing:
- `GET /orders` - View all orders
- `GET /orders/today` - View today's orders
- `POST /process-messages` - Manually process new messages
- `POST /send-daily-orders` - Manually send daily consolidation

## What's Missing for Production

1. **Real-time Webhooks**: Currently using polling (every 2 minutes)
2. **Error Handling**: Better error recovery and logging
3. **Date Intelligence**: Smarter date parsing for "завтра", "послезавтра" 
4. **Duplicate Detection**: Better duplicate order handling
5. **Order Editing**: Manual order correction interface
6. **Analytics**: Daily/weekly statistics

## Troubleshooting

### No messages found?
- Send a test message to your main group
- Check your GreenAPI permissions
- Verify `MAIN_GROUP_CHAT_ID` is correct

### Orders not parsing?
- Check OpenAI API key
- Review parsing prompt in `openai_service.py`
- Test with `python test_mvp_workflow.py parse`

### Database errors?
- Ensure PostgreSQL is running: `docker-compose up -d postgres`
- Check `DATABASE_URL` in `.env`

## Next Steps

1. **Test with Real Orders**: Send actual orders to your main group
2. **Configure Operational Group**: Add your `OPERATIONAL_GROUP_CHAT_ID`
3. **Enable Production Mode**: Set `TESTING_MODE=false`
4. **Schedule Daily Orders**: Uncomment scheduling in `main.py`
5. **Monitor**: Watch logs for any issues

## API Endpoints

- `GET /` - System status
- `GET /orders` - All orders
- `GET /orders/today` - Today's orders  
- `POST /process-messages` - Process new messages
- `POST /send-daily-orders` - Send daily consolidation
