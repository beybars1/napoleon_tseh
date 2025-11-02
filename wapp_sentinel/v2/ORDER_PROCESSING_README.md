# Order Processing System - Руководство по запуску

## Обзор системы

Система автоматической обработки заказов из WhatsApp группы через OpenAI.

### Архитектура:

```
WhatsApp → Green API Webhook → FastAPI → RabbitMQ Queue 1
                                              ↓
                                         Worker 1 (rabbitmq_worker.py)
                                              ↓
                                         Database (3 таблицы сообщений)
                                              ↓
                                         RabbitMQ Queue 2 (order_processing)
                                              ↓
                                         Worker 2 (order_processor_worker.py)
                                              ↓
                                         OpenAI GPT-3.5-turbo
                                              ↓
                                         Database (orders таблица)
```

## Настройка

### 1. Установка зависимостей

```bash
pip install openai
```

### 2. Настройка переменных окружения

Добавьте в `.env`:

```bash
# Green API (уже настроено)
GREENAPI_INSTANCE=your_instance_id
GREENAPI_TOKEN=your_api_token
GREEN_API_BASE_URL=https://api.green-api.com

# RabbitMQ (уже настроено)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=greenapi_notifications

# OpenAI (НОВОЕ - необходимо добавить)
OPENAI_API_KEY=sk-ваш-ключ-openai
OPENAI_MODEL=gpt-3.5-turbo

# Order Processing (НОВОЕ)
TARGET_CHAT_ID=120363403664602093@g.us
ORDER_PROCESSING_QUEUE=order_processing
```

### 3. Применение миграций

```bash
cd /path/to/v2
alembic upgrade head
```

## Запуск системы

### Терминал 1: FastAPI (если не запущен)
```bash
cd /path/to/v2
python app/main.py
```

### Терминал 2: Worker 1 - Message Receiver (если не запущен)
```bash
cd /path/to/v2
python app/rabbitmq_worker.py
```

### Терминал 3: Worker 2 - Order Processor (НОВЫЙ)
```bash
cd /path/to/v2
python app/order_processor_worker.py
```

## Обработка исторических данных

Для обработки существующих сообщений из базы данных:

```bash
cd /path/to/v2
python app/processors/process_historical_orders.py
```

Скрипт:
1. Найдет все непроцессированные сообщения из целевого чата
2. Опубликует их в очередь `order_processing`
3. Worker 2 автоматически обработает их

**Важно:** Убедитесь что Worker 2 запущен перед обработкой исторических данных!

## Проверка работы

### 1. Проверка очередей RabbitMQ

```bash
# Просмотр всех очередей
docker exec rabbitmq rabbitmqctl list_queues

# Должны увидеть:
# greenapi_notifications
# order_processing
```

### 2. Проверка базы данных

```sql
-- Проверить количество обработанных заказов
SELECT COUNT(*) FROM orders;

-- Посмотреть последние заказы
SELECT 
    id,
    message_table,
    estimated_delivery_datetime,
    payment_status,
    accepted_by,
    confidence
FROM orders
ORDER BY created_at DESC
LIMIT 10;

-- Проверить сколько сообщений еще не обработано
SELECT 
    'incoming_message' as table_name,
    COUNT(*) as unprocessed_count
FROM incoming_message
WHERE chat_id = '120363403664602093@g.us' 
  AND order_processed = FALSE
  AND text_message IS NOT NULL

UNION ALL

SELECT 
    'outgoing_message',
    COUNT(*)
FROM outgoing_message
WHERE chat_id = '120363403664602093@g.us' 
  AND order_processed = FALSE
  AND text IS NOT NULL

UNION ALL

SELECT 
    'outgoing_api_message',
    COUNT(*)
FROM outgoing_api_message
WHERE chat_id = '120363403664602093@g.us' 
  AND order_processed = FALSE
  AND text IS NOT NULL;
```

### 3. Мониторинг логов

**Worker 1 (rabbitmq_worker.py):**
```
[x] Received message: {...}
[+] Saved to DB
[→] Published to order queue: message_id=123, table=incoming_message
```

**Worker 2 (order_processor_worker.py):**
```
[x] Received order message
[→] Processing order: message_id=123, table=incoming_message
[AI] Sending to OpenAI for parsing...
[AI] OpenAI response confidence: high
[✓] Order saved to database: order_id=45
[✓] Message marked as processed
[✓] Order processed successfully
```

## Тестирование

### Отправить тестовое сообщение в WhatsApp группу:

```
Заказ на 05.11.25 
На 15:00
Наполеон классический 2кг 
Медовик 1шт

Оплачено 
87012345678
Асель
```

Система должна:
1. ✅ Получить через webhook (FastAPI)
2. ✅ Сохранить в БД (Worker 1)
3. ✅ Опубликовать в order_processing (Worker 1)
4. ✅ Обработать через OpenAI (Worker 2)
5. ✅ Сохранить в таблицу orders (Worker 2)

## Остановка системы

```bash
# В каждом терминале нажмите Ctrl+C

# Worker 1
^C
[*] Worker stopped

# Worker 2
^C
[*] Stopping Order Processor Worker...
[*] Worker stopped
```

## Troubleshooting

### Проблема: Worker 2 не обрабатывает сообщения

**Решение:**
1. Проверьте что `OPENAI_API_KEY` установлен правильно
2. Проверьте логи Worker 2 на ошибки
3. Убедитесь что очередь `order_processing` существует

### Проблема: OpenAI возвращает низкую уверенность (low confidence)

**Решение:**
1. Проверьте формат сообщений - возможно они не содержат ключевую информацию
2. Улучшите промпт в `app/services/openai_service.py`
3. Попробуйте использовать GPT-4 вместо GPT-3.5-turbo

### Проблема: Исторические данные не обрабатываются

**Решение:**
1. Убедитесь что Worker 2 запущен
2. Проверьте что сообщения есть в очереди: `docker exec rabbitmq rabbitmqctl list_queues`
3. Посмотрите логи Worker 2

## Расширение функционала

### Добавление новых полей в Order

1. Добавьте колонку в модель `Order` (app/database/models.py)
2. Создайте миграцию: `alembic revision -m "add_new_field"`
3. Примените миграцию: `alembic upgrade head`
4. Обновите промпт OpenAI (app/services/openai_service.py)

### Изменение целевого чата

Измените `TARGET_CHAT_ID` в `.env`:
```bash
TARGET_CHAT_ID=другой_chat_id@g.us
```

Перезапустите Worker 1 и Worker 2.

## Стоимость OpenAI

GPT-3.5-turbo:
- Input: ~$0.0015 / 1K tokens
- Output: ~$0.002 / 1K tokens

Средний заказ: ~200 tokens = $0.0004

1000 заказов ≈ $0.40
