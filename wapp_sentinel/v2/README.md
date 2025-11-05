# Napoleon Tseh - WhatsApp Sentinel v2

**Автоматизированная система обработки заказов через WhatsApp с AI-парсингом и автоматической отчетностью**

## 🎯 Описание проекта

Napoleon Tseh WhatsApp Sentinel - это комплексная система для автоматизации приема, обработки и учета заказов кондитерской через WhatsApp мессенджер. Система использует искусственный интеллект (OpenAI GPT) для извлечения структурированной информации из неформализованных сообщений и автоматически генерирует ежедневные отчеты.

## ✨ Основные возможности

### 🤖 Умная обработка сообщений
- **Webhook интеграция** с Green API для приема сообщений из WhatsApp
- **AI-парсинг** заказов с помощью OpenAI GPT-4
- Извлечение информации:
  - 📅 Дата и время доставки
  - 💳 Статус оплаты
  - 👤 Имя клиента
  - 📱 Контактные номера
  - 📦 Список товаров с количеством

### 📊 Автоматические отчеты
- **Ежедневная рассылка** отчетов по расписанию
- Красиво отформатированные сообщения в WhatsApp
- Статистика по оплатам и количеству заказов
- Сортировка заказов по времени доставки
- API endpoints для ручной отправки

### 🔄 Асинхронная архитектура
- **RabbitMQ** для надежной очереди сообщений
- Два специализированных worker'а:
  - Обработка входящих сообщений
  - AI-анализ и сохранение заказов
- Масштабируемая и отказоустойчивая система

### 💾 Надежное хранение
- **PostgreSQL** база данных
- Полная история всех сообщений и заказов
- Миграции через Alembic
- Индексы для быстрого поиска

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsApp (Green API)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI (main.py)                              │
│  • Webhook endpoint /receiveNotification                         │
│  • API endpoints для отчетов                                     │
│  • APScheduler для автоматической отправки                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RabbitMQ Queue                              │
│  • greenapi_notifications - входящие сообщения                   │
│  • order_processing - заказы для AI обработки                    │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐   ┌─────────────────────────────────┐
│  rabbitmq_worker.py      │   │  order_processor_worker.py      │
│  • Сохраняет сообщения   │   │  • Отправляет в OpenAI          │
│  • Фильтрует заказы      │   │  • Парсит структуру заказа      │
│  • Пересылает в AI очередь│  │  • Сохраняет в таблицу orders   │
└──────────────┬───────────┘   └─────────────┬───────────────────┘
               │                              │
               └──────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  • incoming_message - входящие сообщения                         │
│  • outgoing_message - исходящие сообщения                        │
│  • outgoing_api_message - сообщения через API                    │
│  • orders - структурированные заказы                             │
└─────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Daily Report Service + Scheduler                    │
│  • Генерация отчетов за день                                     │
│  • Автоматическая отправка по расписанию                         │
│  • Отправка в WhatsApp чат                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.10+
- Docker & Docker Compose
- Green API аккаунт
- OpenAI API ключ

### Установка

1. **Клонируйте репозиторий:**
```bash
cd /home/beybars/dev_python/napoleon_tseh/wapp_sentinel/v2
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл
```

4. **Запустите Docker контейнеры:**
```bash
docker compose up -d
```

5. **Примените миграции:**
```bash
alembic upgrade head
```

6. **Запустите сервисы:**
```bash
# Терминал 1: FastAPI
python app/main.py

# Терминал 2: RabbitMQ Worker
python app/rabbitmq_worker.py

# Терминал 3: Order Processor Worker
python app/order_processor_worker.py
```

## 📝 Конфигурация

### Основные настройки (.env)

```env
# Green API
GREENAPI_INSTANCE=your_instance_id
GREENAPI_TOKEN=your_token
GREEN_API_BASE_URL=https://api.green-api.com

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_QUEUE=greenapi_notifications
ORDER_PROCESSING_QUEUE=order_processing

# OpenAI
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini

# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=napoleon-sentinel-db
DATABASE_URL=postgresql://admin:admin@localhost:5432/napoleon-sentinel-db

# Scheduler
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=08:00
DAILY_REPORT_CHAT_ID=your_chat_id@g.us
DAILY_REPORT_TIMEZONE=Asia/Almaty

# Target Chat (для фильтрации)
TARGET_CHAT_ID=120363403664602093@g.us
```

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
│   ├── main.py                    # FastAPI приложение
│   ├── scheduler.py               # APScheduler для автоматических задач
│   ├── rabbitmq_worker.py         # Worker для обработки сообщений
│   ├── order_processor_worker.py  # Worker для AI-парсинга заказов
│   ├── database/
│   │   ├── database.py            # SQLAlchemy setup
│   │   └── models.py              # Модели БД
│   ├── services/
│   │   ├── openai_service.py      # OpenAI интеграция
│   │   └── daily_report_service.py # Генерация отчетов
│   └── processors/
│       └── diagnose.py            # Утилиты диагностики
├── migrations/                    # Alembic миграции
├── docker-compose.yaml            # Docker services
├── requirements.txt               # Python зависимости
├── alembic.ini                    # Alembic конфигурация
├── .env                           # Переменные окружения
└── README.md                      # Этот файл
```

## 🐳 Docker Services

```yaml
services:
  postgres:      # PostgreSQL база данных
  rabbitmq:      # RabbitMQ message broker
```

## 🔄 Жизненный цикл заказа

1. **Менеджер отправляет сообщение** в WhatsApp чат
2. **Green API webhook** отправляет уведомление в FastAPI
3. **FastAPI публикует** сообщение в RabbitMQ очередь
4. **rabbitmq_worker** сохраняет сообщение в БД
5. **rabbitmq_worker** фильтрует заказы и отправляет в AI очередь
6. **order_processor_worker** получает сообщение из AI очереди
7. **OpenAI парсит** текст и извлекает структурированные данные
8. **order_processor_worker** сохраняет заказ в таблицу `orders`
9. **Scheduler** автоматически собирает заказы и отправляет отчет

## 📊 Формат ежедневного отчета

```
📋 ЗАКАЗЫ НА 04.11.2025
Всего заказов: 3

────────────────────────────────────────
ЗАКАЗ #1
🕐 Время доставки: 12:00
💳 ✅ Оплачено
👤 Клиент: Айнур
📱 Контакт: +77001234567
📦 Товары:
   • Торт "Наполеон" - 1 кг
   • Капкейки - 6 шт
📅 Принят: 03.11.2025 18:30

────────────────────────────────────────
ЗАКАЗ #2
🕐 Время доставки: 14:00
💳 ❌ Не оплачено
👤 Клиент: Мария
📱 Контакт: +77009876543
📦 Товары:
   • Торт "Прага" - 2 кг
📅 Принят: 04.11.2025 09:00

────────────────────────────────────────
📊 СТАТИСТИКА:
   • Всего заказов: 2
   • Оплачено: 1
   • Не оплачено: 1
────────────────────────────────────────
```

## 🛠️ Разработка

### Запуск тестов
```bash
python test_daily_report.py
```

### Создание новой миграции
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Проверка статуса
```bash
# RabbitMQ Management UI
http://localhost:15672
# Login: guest / Password: guest

# Scheduler status
curl http://localhost:8000/scheduler/status
```

## 🔧 Troubleshooting

### RabbitMQ подключение
Убедитесь что credentials в коде совпадают с docker-compose.yaml

### OpenAI парсинг
Проверьте что:
- OPENAI_API_KEY корректный
- Модель доступна (gpt-4o-mini)
- Есть баланс на аккаунте

### Scheduler не работает
```bash
# Проверьте настройки
SCHEDULER_ENABLED=true
DAILY_REPORT_CHAT_ID=your_chat_id@g.us

# Проверьте статус
curl http://localhost:8000/scheduler/status
```

## 📚 Дополнительная документация

- `SCHEDULER_README.md` - Подробно о планировщике
- `DAILY_REPORT_API.md` - API для отчетов
- `MIGRATION_GUIDE.md` - Руководство по миграции

## 🤝 Участие в разработке

Проект разработан для автоматизации работы кондитерской Napoleon Tseh.

## 📄 Лицензия

Proprietary - все права защищены

## 👨‍💻 Автор

**Napoleon Tseh Team**
- Repository: beybars1/napoleon_tseh
- Branch: main

## 🔗 Связанные проекты

- Green API - https://green-api.com
- OpenAI API - https://openai.com
- APScheduler - https://apscheduler.readthedocs.io

---

**Версия:** 2.0  
**Последнее обновление:** Ноябрь 2025
