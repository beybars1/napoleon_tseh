# 🚀 Telegram Bot Production Deployment Guide

This guide covers deploying the Napoleon-Tseh Telegram bot to production using FastAPI webhooks.

## 📋 Overview

The bot can run in two modes:
- **Development (Polling)**: Bot actively polls Telegram for updates
- **Production (Webhook)**: Telegram sends updates to your FastAPI server via HTTPS

## 🔧 Production Requirements

### Essential Requirements
- ✅ **Public Domain/IP**: Accessible from the internet
- ✅ **SSL Certificate**: Valid HTTPS certificate (required by Telegram)
- ✅ **FastAPI Server**: Running and accessible
- ✅ **Port 443**: Open for HTTPS traffic
- ✅ **Telegram Bot Token**: From @BotFather

### Recommended Infrastructure
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt or commercial certificate
- **Process Manager**: systemd, PM2, or Docker
- **Firewall**: UFW or iptables configured

## 🛠️ Setup Methods

### Method 1: Automatic Setup (Recommended)

```bash
# 1. With domain
python app/scripts/start_telegram_production.py your-domain.com

# 2. With IP and port
python app/scripts/start_telegram_production.py 123.45.67.89:8000
```

### Method 2: API Setup

```bash
# Start FastAPI server first
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Then configure via API
curl -X POST "https://your-domain.com/api/v1/webhooks/telegram/setup_production" \
  -H "Content-Type: application/json" \
  -d '{"domain": "your-domain.com"}'
```

### Method 3: Environment Variables

Add to your `.env`:
```env
TELEGRAM_PRODUCTION_MODE=true
TELEGRAM_WEBHOOK_DOMAIN=your-domain.com
```

Then start normally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🌐 Nginx Configuration

### Basic Nginx Config (`/etc/nginx/sites-available/napoleon-tseh`)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # FastAPI Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Telegram Webhook (specific optimization)
    location /api/v1/webhooks/telegram {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Webhook optimizations
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 30s;
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/napoleon-tseh /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 SSL Certificate Setup

### Using Let's Encrypt (Free)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (add to crontab)
0 12 * * * /usr/bin/certbot renew --quiet
```

### Using Custom Certificate

```bash
# Copy your certificates
sudo cp your-cert.pem /etc/ssl/certs/napoleon-tseh.pem
sudo cp your-key.pem /etc/ssl/private/napoleon-tseh.key

# Update nginx config paths
ssl_certificate /etc/ssl/certs/napoleon-tseh.pem;
ssl_certificate_key /etc/ssl/private/napoleon-tseh.key;
```

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TELEGRAM_PRODUCTION_MODE=true
      - TELEGRAM_WEBHOOK_DOMAIN=your-domain.com
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: napoleon_tseh
      POSTGRES_USER: napoleon
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

## 🎯 API Management

### Check Bot Status
```bash
curl "https://your-domain.com/api/v1/webhooks/telegram/status"
```

### Switch to Webhook Mode
```bash
curl -X POST "https://your-domain.com/api/v1/webhooks/telegram/switch_mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "webhook", "domain": "your-domain.com"}'
```

### Switch to Polling Mode (for maintenance)
```bash
curl -X POST "https://your-domain.com/api/v1/webhooks/telegram/switch_mode" \
  -H "Content-Type: application/json" \
  -d '{"mode": "polling"}'
```

### Get Webhook Info
```bash
curl "https://your-domain.com/api/v1/webhooks/telegram/webhook_info"
```

## 📊 Monitoring & Logging

### Log Files to Monitor
```bash
# FastAPI application logs
tail -f /var/log/napoleon-tseh/app.log

# Nginx access logs
tail -f /var/log/nginx/access.log

# Nginx error logs
tail -f /var/log/nginx/error.log

# System logs
journalctl -f -u nginx
```

### Health Check Endpoints
- Bot Status: `GET /api/v1/webhooks/telegram/status`
- Webhook Info: `GET /api/v1/webhooks/telegram/webhook_info`
- API Health: `GET /health` (if implemented)

### Monitoring Metrics
- Response time for webhook endpoints
- Message processing rate
- Error rates and types
- Database connection status
- OpenAI API response times

## 🚨 Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages
```bash
# Check webhook status
curl "https://your-domain.com/api/v1/webhooks/telegram/webhook_info"

# Verify HTTPS accessibility
curl -I "https://your-domain.com/api/v1/webhooks/telegram"

# Check Telegram can reach your server
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/api/v1/webhooks/telegram"
```

#### 2. SSL Certificate Issues
```bash
# Test SSL
openssl s_client -connect your-domain.com:443

# Check certificate validity
curl -vI "https://your-domain.com"
```

#### 3. Bot Responds Twice
- Ensure only one mode is active (either polling OR webhook)
- Check for duplicate webhook registrations
- Verify no development instances are running

#### 4. High Response Time
```bash
# Check FastAPI performance
curl -w "@curl-format.txt" "https://your-domain.com/api/v1/webhooks/telegram/status"

# Monitor database connections
# Monitor OpenAI API response times
```

### Debug Commands
```bash
# Test webhook manually
curl -X POST "https://your-domain.com/api/v1/webhooks/telegram" \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "test", "from": {"id": 123}}}'

# Clear webhook (emergency)
curl -X DELETE "https://your-domain.com/api/v1/webhooks/telegram/webhook"

# Switch to polling for debugging
python app/scripts/run_telegram_bot.py
```

## 🔄 Deployment Workflow

### Initial Deployment
1. ✅ Setup server with domain and SSL
2. ✅ Configure Nginx reverse proxy
3. ✅ Deploy FastAPI application
4. ✅ Run production setup script
5. ✅ Test bot functionality
6. ✅ Monitor logs and metrics

### Updates/Maintenance
1. ✅ Switch to polling mode (optional)
2. ✅ Deploy new code
3. ✅ Restart FastAPI service
4. ✅ Switch back to webhook mode
5. ✅ Verify functionality

### Scaling
- Use multiple FastAPI instances behind load balancer
- Implement Redis for session management
- Use database connection pooling
- Monitor and scale based on message volume

## 🎉 Success Checklist

After setup, verify:
- [ ] Webhook status returns active URL
- [ ] Bot responds to `/start` command
- [ ] Messages are logged in database
- [ ] No duplicate responses
- [ ] SSL certificate is valid
- [ ] Logs show incoming webhook requests
- [ ] Bot commands work correctly
- [ ] AI responses are generated

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review FastAPI and Nginx logs
3. Test individual components
4. Use the debug commands provided

Your Telegram bot is now ready for production! 🎂🤖 