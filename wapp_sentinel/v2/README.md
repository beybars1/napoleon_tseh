# Napoleon Tseh - WhatsApp Sentinel v2

**Автоматизированная система обработки заказов через WhatsApp с AI-агентами и аналитикой**

## 🎯 Описание проекта

Napoleon Tseh WhatsApp Sentinel - это комплексная система для автоматизации приема, обработки и учета заказов кондитерской через WhatsApp мессенджер. Система использует искусственный интеллект (OpenAI GPT-4 + LangGraph) для разговорного приема заказов и обработки исторических данных, автоматически генерирует ежедневные отчеты.

## ✨ Основные возможности

### 🤖 AI-агенты для обработки

#### **AI Agent Worker (LangGraph)**
- **Разговорный прием заказов** через WhatsApp
- Контекстное ведение диалога с клиентом
- Пошаговый сбор информации:
  - 📦 Позиции заказа (название, количество)
  - 📅 Дата и время доставки
  - 📍 Адрес доставки
  - 💳 Способ оплаты
  - 👤 Контактная информация
- Подтверждение заказа перед сохранением
- Whitelist для тестирования

#### **Order Processor Worker (OpenAI)**
- **AI-парсинг** исторических заказов
- Обработка неструктурированных сообщений
- Извлечение информации из текста
- Автоматическая категоризация

### 📊 Автоматические отчеты
- **Ежедневная рассылка** отчетов по расписанию
- Красиво отформатированные сообщения в WhatsApp
- Статистика по оплатам и количеству заказов
- Сортировка заказов по времени доставки
- API endpoints для ручной отправки

### 🔄 Микросервисная архитектура
- **Абстракция брокера сообщений** — единый интерфейс для RabbitMQ (локально) и Azure Service Bus (продакшн)
- Переключение через переменную окружения `BROKER_TYPE`
- Три специализированных worker'а:
  - **Green API Worker** - сохранение всех событий Green API
  - **AI Agent Worker** - разговорный прием заказов (LangGraph)
  - **Order Processor Worker** - обработка исторических заказов (OpenAI)
- Масштабируемая и отказоустойчивая система
- Docker контейнеризация

### 💾 Надежное хранение
- **PostgreSQL** база данных
- Все timestamps хранятся в `timestamptz` (UTC)
- Полная история всех сообщений и заказов
- Таблицы для конверсаций и AI-генерированных заказов
- Миграции через Alembic
- Индексы для быстрого поиска

## 🏗️ Архитектура системы

```
┌──────────────────────────────────────────────────────────────────┐
│                     WhatsApp (Green API)                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI API (:8000)                          │
│  • Webhook endpoint /receiveNotification                         │
│  • Message routing (manager vs AI agent vs unknown)              │
│  • API endpoints для отчетов                                     │
│  • APScheduler для автоматической отправки                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              Message Broker Abstraction Layer                    │
│  ┌─────────────────────┐    ┌──────────────────────────┐        │
│  │  RabbitMQ (local)   │ OR │ Azure Service Bus (prod) │        │
│  │  BROKER_TYPE=       │    │ BROKER_TYPE=             │        │
│  │    rabbitmq         │    │   servicebus             │        │
│  └─────────────────────┘    └──────────────────────────┘        │
│                                                                  │
│  Очереди:                                                        │
│  • greenapi_queue        - все события Green API                 │
│  • ai_agent_queue        - сообщения для AI агента               │
│  • order_processor_queue - заказы для обработки                   │
└──────┬───────────────────────┬──────────────────┬────────────────┘
       │                       │                  │
       ▼                       ▼                  ▼
┌────────────────────┐  ┌──────────────────┐  ┌────────────────────────┐
│ Green API Worker   │  │ AI Agent Worker  │  │ Order Processor Worker │
│                    │  │                  │  │                        │
│ • Сохраняет все    │  │ • LangGraph FSM  │  │ • OpenAI парсинг      │
│   события в БД     │  │ • Диалог с       │  │ • Обработка           │
│ • Публикует в      │  │   клиентом       │  │   исторических        │
│   order_processor │  │ • Сбор инфо о    │  │   заказов             │
│   queue            │  │   заказе         │  │ • Сохранение в        │
│                    │  │ • Валидация      │  │   таблицу orders      │
│                    │  │ • Подтверждение  │  │                        │
└───────────┬────────┘  └────────┬─────────┘  └────────────┬───────────┘
         │                    │                       │
         └────────────────────┼───────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database (timestamptz UTC)            │
│  • incoming_message - входящие сообщения                         │
│  • outgoing_message - исходящие сообщения                        │
│  • outgoing_api_message - сообщения через API                    │
│  • conversations - диалоги AI агента                             │
│  • conversation_messages - сообщения в диалогах                  │
│  • ai_generated_orders - заказы от AI агента                     │
│  • orders - обработанные заказы (исторические)                   │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│               Daily Report Service + Scheduler                   │
│  • Генерация отчетов за день                                     │
│  • Автоматическая отправка по расписанию (00:30)                 │
│  • Отправка в WhatsApp чат менеджера                             │
└──────────────────────────────────────────────────────────────────┘
```

## ☁️ Azure Production Deployment

Система развернута в Azure (resource group: `napoleon-rg`):

| Ресурс | Сервис Azure | Описание |
|--------|-------------|----------|
| API | Container App | FastAPI webhook + API |
| AI Agent Worker | Container App | LangGraph диалоги |
| GreenAPI Worker | Container App | Сохранение событий |
| Order Processor Worker | Container App | OpenAI парсинг заказов |
| PostgreSQL | Azure Database for PostgreSQL Flexible Server | Основная БД |
| Message Broker | Azure Service Bus (Basic) | Очереди сообщений ($0.05/мес) |
| Container Registry | Azure Container Registry | Docker образы |

### Переключение брокера

```bash
# Локально (docker-compose) — RabbitMQ
BROKER_TYPE=rabbitmq

# Продакшн (Azure) — Service Bus
BROKER_TYPE=servicebus
SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.10+
- Docker & Docker Compose
- Green API аккаунт
- OpenAI API ключ

### 🐳 Запуск через Docker (рекомендуется)

1. **Настройте переменные окружения:**
```bash
cp .env.example .env
nano .env  # Отредактируйте .env файл
```

Обязательные переменные:
```env
GREENAPI_INSTANCE=your_instance
GREENAPI_TOKEN=your_token
OPENAI_API_KEY=your_openai_key
MANAGER_CHAT_IDS=77028639438@c.us
AI_AGENT_CHAT_IDS=77006458263@c.us
```

2. **Запустите все сервисы:**
```bash
docker compose up -d
```

3. **Примените миграции:**
```bash
docker compose exec api alembic upgrade head
```

4. **Проверьте статус:**
```bash
./health_check.sh
# или
docker compose ps
```

### 💻 Локальный запуск (для разработки)

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Запустите инфраструктуру (PostgreSQL + RabbitMQ):**
```bash
docker compose up -d postgres rabbitmq
```

3. **Примените миграции:**
```bash
alembic upgrade head
```

4. **Запустите сервисы в отдельных терминалах:**
```bash
# Терминал 1: FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Терминал 2: Green API Worker
python app/greenapi_worker.py

# Терминал 3: AI Agent Worker
python app/ai_agent_worker.py

# Терминал 4: Order Processor Worker
python app/order_processor_worker.py
```

## 📝 Конфигурация

### Основные настройки (.env)

```env
# Green API
GREENAPI_INSTANCE=your_instance_id
GREENAPI_TOKEN=your_token
GREEN_API_BASE_URL=https://api.greenapi.com/waInstance

# Message Broker
BROKER_TYPE=rabbitmq              # rabbitmq (local) или servicebus (Azure)
GREENAPI_QUEUE=greenapi_queue
ORDER_PROCESSOR_QUEUE=order_processor_queue
AI_AGENT_QUEUE=ai_agent_queue

# RabbitMQ (только для локальной разработки)
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Azure Service Bus (только для продакшн)
# SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...

# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini

# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=napoleon-sentinel-db
DATABASE_URL=postgresql://admin:admin@localhost:5433/napoleon-sentinel-db

# Chat IDs for routing
MANAGER_CHAT_IDS=77028639438@c.us
AI_AGENT_CHAT_IDS=77006458263@c.us

# Scheduler
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=00:30
DAILY_REPORT_CHAT_ID=77028639438@c.us
DAILY_REPORT_TIMEZONE=Asia/Almaty
```

### Маршрутизация сообщений

Система автоматически определяет тип обработки на основе chat_id:

- **MANAGER_CHAT_IDS** - сообщения от менеджера (сохраняются в БД, не обрабатываются)
- **AI_AGENT_CHAT_IDS** - сообщения для AI агента (разговорный прием заказов)
- **Прочие** - игнорируются (безопасность)

## 🔌 API Endpoints

### Webhook
- `POST /receiveNotification` - Прием уведомлений от Green API

### Отправка сообщений
- `POST /sendMessage` - Отправка сообщения в WhatsApp
- `DELETE /removeNotification/{receipt_id}` - Удаление уведомления

### Отчеты
- `GET /orders/daily-report/{date}` - Предпросмотр отчета
- `POST /orders/preview-daily-report` - Предпросмотр (POST)
- `POST /orders/send-daily-report` - Отправить отчет в WhatsApp

### Мониторинг
- `GET /scheduler/status` - Статус планировщика

## 📦 Структура проекта

```
wapp_sentinel/v2/
├── app/
│   ├── main.py                    # FastAPI приложение + routing
│   ├── scheduler.py               # APScheduler для автоматических задач
│   ├── greenapi_worker.py         # Green API Worker (сохранение событий)
│   ├── ai_agent_worker.py         # AI Agent Worker (LangGraph диалоги)
│   ├── order_processor_worker.py  # Order Processor Worker (OpenAI парсинг)
│   ├── messaging/                 # Абстракция брокера сообщений
│   │   ├── __init__.py            # Фабрика get_broker(), экспорт
│   │   ├── base.py                # ABC MessageBroker + AckAction enum
│   │   ├── rabbitmq_broker.py     # RabbitMQ реализация (pika)
│   │   └── servicebus_broker.py   # Azure Service Bus реализация
│   ├── agents/
│   │   ├── state.py               # ConversationState TypedDict
│   │   ├── nodes/                 # LangGraph узлы
│   │   ├── tools/                 # LangGraph инструменты
│   │   └── order_graph.py         # LangGraph workflow
│   ├── database/
│   │   ├── database.py            # SQLAlchemy setup
│   │   └── models.py              # Модели БД (timestamptz UTC)
│   ├── services/
│   │   ├── openai_service.py      # OpenAI интеграция
│   │   └── daily_report_service.py # Генерация отчетов
│   └── processors/
│       ├── diagnose.py            # Утилиты диагностики
│       └── process_historical_orders.py # Обработка истории
├── migrations/                    # Alembic миграции
├── scripts/
│   └── verify_timestamps.py      # Проверка UTC timestamps в БД
├── Dockerfile.api                 # Docker для API
├── Dockerfile.greenapi_worker     # Docker для Green API Worker
├── Dockerfile.ai_agent_worker     # Docker для AI Agent Worker
├── Dockerfile.order_processor_worker  # Docker для Order Processor Worker
├── docker-compose.yml             # Docker Compose (dev, RabbitMQ)
├── Makefile                       # Удобные команды
├── health_check.sh               # Скрипт проверки здоровья
├── requirements.txt               # Python зависимости
├── alembic.ini                    # Alembic конфигурация
├── .env                           # Переменные окружения
└── README.md                      # Этот файл
```

## 🐳 Docker Services

### Development (docker-compose.yml)
```yaml
services:
  postgres:              # PostgreSQL база данных (порт 5433)
  rabbitmq:              # RabbitMQ message broker (5672, 15672)
  api:                   # FastAPI application (порт 8000)  [BROKER_TYPE=rabbitmq]
  greenapi_worker:       # Сохранение всех событий Green API  [BROKER_TYPE=rabbitmq]
  ai_agent_worker:       # Разговорный прием заказов (LangGraph)  [BROKER_TYPE=rabbitmq]
  order_processor_worker: # Обработка исторических заказов (OpenAI)  [BROKER_TYPE=rabbitmq]
```

### Команды управления (Makefile)
```bash
make up              # Запустить все сервисы
make down            # Остановить все сервисы
make logs            # Смотреть все логи
make logs-api        # Логи API
make logs-message    # Логи Green API Worker
make logs-ai         # Логи AI Agent Worker
make logs-aggregation # Логи Order Processor Worker
make restart         # Перезапустить все
make migrate         # Применить миграции
make shell           # Bash в API контейнере
make db-shell        # PostgreSQL shell
make ps              # Статус контейнеров
```

## 📨 Messaging Abstraction Layer

Система поддерживает два брокера сообщений через единый интерфейс `MessageBroker`:

### Интерфейс
```python
from app.messaging import get_broker, AckAction

broker = get_broker()  # Singleton, выбирается по BROKER_TYPE

# Публикация
broker.publish("queue_name", {"key": "value"})

# Потребление (блокирующее)
def handler(message: dict) -> AckAction:
    process(message)
    return AckAction.ACK  # или NACK, REQUEUE

broker.consume("queue_name", handler)
```

### Реализации

| Реализация | Env | Использование |
|-----------|-----|---------------|
| `RabbitMQBroker` | `BROKER_TYPE=rabbitmq` | Локальная разработка (docker-compose) |
| `ServiceBusBroker` | `BROKER_TYPE=servicebus` | Azure продакшн (Container Apps) |

### AckAction

| Действие | RabbitMQ | Service Bus |
|----------|----------|-------------|
| `ACK` | `basic_ack` | `complete_message` |
| `NACK` | `basic_nack(requeue=False)` | `dead_letter_message` |
| `REQUEUE` | `basic_nack(requeue=True)` | `abandon_message` |

## 🔄 Жизненный цикл обработки

### Вариант 1: AI Agent (новые заказы)

1. **Клиент отправляет сообщение** в WhatsApp (из AI_AGENT_CHAT_IDS)
2. **Green API webhook** → FastAPI `/receiveNotification`
3. **FastAPI маршрутизация** → определяет тип = `client`
4. **Публикация** в `ai_agent_queue` очередь
5. **AI Agent Worker** (LangGraph):
   - Получает сообщение из очереди
   - Загружает/создает состояние диалога
   - Обрабатывает через граф состояний
   - Собирает информацию о заказе пошагово
   - Валидирует и подтверждает
   - Сохраняет в `conversations`, `conversation_messages`, `ai_generated_orders`
   - Отправляет ответы в WhatsApp через Green API

### Вариант 2: Исторические заказы (менеджер)

1. **Менеджер отправляет сообщение** в WhatsApp (из MANAGER_CHAT_IDS)
2. **Green API webhook** → FastAPI `/receiveNotification`
3. **FastAPI маршрутизация** → определяет тип = `manager`
4. **Публикация** в `greenapi_queue` очередь
5. **Green API Worker**:
   - Получает из `greenapi_queue`
   - Сохраняет все события в БД (incoming_message, outgoing_message, etc.)
   - Публикует в `order_processor_queue` очередь
6. **Order Processor Worker** (OpenAI):
   - Получает из `order_processor_queue` очереди
   - Парсит текст с помощью OpenAI GPT-4
   - Извлекает структурированные данные
   - Сохраняет в таблицу `orders`

### Вариант 3: Автоматические отчеты

1. **APScheduler** запускает задачу в 00:30 (Asia/Almaty)
2. **Daily Report Service**:
   - Собирает заказы за прошедший день
   - Генерирует красиво отформатированный отчет
   - Отправляет в WhatsApp чат менеджера
   - Статистика: количество заказов, оплаченные/неоплаченные

## 🛠️ Разработка

### Создание новой миграции
```bash
# Через Docker
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head

# Локально
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Тестирование
```bash
# Тест daily report
python test_daily_report.py

# Проверка AI Agent
# Отправьте сообщение с номера из AI_AGENT_CHAT_IDS

# Проверка timestamps в БД
python scripts/verify_timestamps.py
```

### Мониторинг
```bash
# Health check всех сервисов
./health_check.sh

# RabbitMQ Management UI (локально)
http://localhost:15672
# Login: guest / Password: guest

# API Documentation
http://localhost:8000/docs

# Scheduler status
curl http://localhost:8000/scheduler/status

# Логи Docker
docker compose logs -f
docker compose logs -f ai_agent_worker
docker compose logs -f greenapi_worker
docker compose logs -f order_processor_worker
```

## 🔧 Troubleshooting

### AI Agent Worker не отвечает
```bash
# Проверьте логи
docker compose logs -f ai_agent_worker

# Убедитесь что:
# 1. OPENAI_API_KEY установлен
# 2. Chat ID есть в AI_AGENT_CHAT_IDS
# 3. BROKER_TYPE установлен корректно
# 4. Worker запущен и подключен к брокеру
```

### Green API Worker не сохраняет события
```bash
# Проверьте логи
docker compose logs -f greenapi_worker

# Проверьте подключение к БД
docker compose exec greenapi_worker python -c "from app.database.database import engine; engine.connect()"

# Проверьте RabbitMQ (локально)
docker compose exec rabbitmq rabbitmq-diagnostics ping
```

### Order Processor Worker не обрабатывает заказы
```bash
# Проверьте логи
docker compose logs -f order_processor_worker

# Проверьте OpenAI API ключ
docker compose exec order_processor_worker python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### PostgreSQL подключение
```bash
# Проверьте статус
docker compose exec postgres pg_isready

# Проверьте порт (5433 вместо 5432)
DATABASE_URL=postgresql://admin:admin@localhost:5433/napoleon-sentinel-db

# Подключитесь к БД
docker compose exec postgres psql -U admin -d napoleon-sentinel-db
```

### Проверка брокера
```bash
# Проверьте какой брокер используется
docker compose logs api 2>&1 | grep -i broker

# Ожидаемый вывод (локально):
# Using RabbitMQ broker

# Ожидаемый вывод (Azure):
# Using Azure Service Bus broker
```

### Scheduler не отправляет отчеты
```bash
# Проверьте настройки в .env
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=00:30
DAILY_REPORT_CHAT_ID=77028639438@c.us
DAILY_REPORT_TIMEZONE=Asia/Almaty

# Проверьте статус
curl http://localhost:8000/scheduler/status

# Ручная отправка для теста
curl -X POST http://localhost:8000/orders/send-daily-report
```

## 📚 Технологии

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с БД (`DateTime(timezone=True)`)
- **Alembic** - миграции базы данных
- **Pika** - Python клиент для RabbitMQ (локально)
- **azure-servicebus** - Azure Service Bus SDK (продакшн)
- **APScheduler** - планировщик задач

### AI & ML
- **OpenAI GPT-4o-mini** - парсинг исторических заказов
- **LangGraph** - граф состояний для AI агента
- **LangChain** - интеграция с LLM

### Infrastructure
- **PostgreSQL 15** - реляционная БД (timestamptz UTC)
- **RabbitMQ 3** - очереди сообщений (локальная разработка)
- **Azure Service Bus** - очереди сообщений (продакшн, Basic tier)
- **Azure Container Apps** - контейнерный хостинг (продакшн)
- **Azure Container Registry** - хранение Docker образов
- **Docker & Docker Compose** - контейнеризация (локально)
- **Green API** - WhatsApp интеграция

## 🤝 Участие в разработке

Проект разработан для автоматизации работы кондитерской Napoleon Tseh.

## 📄 Лицензия

Proprietary - все права защищены

## 👨‍💻 Автор

**Napoleon Tseh Team**
- Repository: beybars1/napoleon_tseh
- Branch: dev

## 🔗 Связанные проекты

- Green API - https://green-api.com
- OpenAI API - https://openai.com
- Azure Service Bus - https://learn.microsoft.com/azure/service-bus-messaging/
- LangGraph - https://langchain-ai.github.io/langgraph/

---

**Версия:** 2.1  
**Последнее обновление:** Февраль 2026
