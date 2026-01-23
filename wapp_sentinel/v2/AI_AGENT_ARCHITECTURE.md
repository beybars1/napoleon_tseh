# AI Agent Architecture - Napoleon Tseh
## Intent-Driven Conversational Order Collection System

**Version:** 2.0  
**Date:** January 17, 2026  
**Architecture Pattern:** Custom Intent Router with Specialized Nodes (LangGraph)  
**Model:** OpenAI GPT-4o-mini  

---

## 🎯 Project Overview

### Business Context
**Napoleon Tseh** - Premium made-to-order Napoleon cakes and dessert sets
- **No ready-made products** - everything is made fresh on order
- **Premium quality focus** - artisanal approach
- **B2C Sales** - Direct to consumer via WhatsApp

### AI Agent Goals
1. **Automate 90% of customer interactions** - AI handles routine inquiries and order collection
2. **Smart human escalation for 10%** - Complex cases, customizations, high-value orders go to human operators
3. **Professional sales experience** - Knowledgeable, helpful, brand-appropriate communication
4. **Flexible conversation flow** - Handle non-linear dialogues, questions mid-order, topic switching

### Key Business Rules
- **Minimum lead time:** 4 hours before pickup/delivery
- **Payment:** 100% prepay required before production starts
- **Fulfillment:** Customer pickup OR customer-arranged Yandex courier to our address
- **Location:** Almaty, Kazakhstan
- **Customization:** Route to human operator (decorations, special requests)

---

## 🏗️ Architecture Overview

### Design Philosophy
**Intent-Driven with Explicit Routing** - Instead of a rigid linear flow, the agent:
1. Classifies user intent in each message
2. Routes to specialized node based on intent
3. Each node is an expert in its domain
4. Maintains flexible conversation state throughout

### Why Option B (Custom Router) Over Option A (ReAct Agent)
- ✅ **Predictable behavior** - Well-defined conversation patterns for sales
- ✅ **Full control** - Explicit routing rules for business logic
- ✅ **Cost efficient** - Lower token usage (no reasoning overhead)
- ✅ **Maintainable** - Clear codebase structure for team
- ✅ **Fast responses** - No agent deliberation delay
- ✅ **Debuggable** - Easy to trace node-to-node flow

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   USER MESSAGE (WhatsApp)                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              LOAD CONVERSATION STATE FROM DB                     │
│  • Get conversation history                                      │
│  • Load order draft (if any)                                     │
│  • Check if flagged for human                                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PRE-ROUTING CHECKS                              │
│  IF conversation.flagged_for_human:                              │
│      → Queue for human operator                                  │
│  IF first_message:                                               │
│      → Send professional greeting                                │
│  ELSE:                                                           │
│      → Continue to intent classification                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│             INTENT CLASSIFIER NODE (GPT-4o-mini)                 │
│  Classify intent into:                                           │
│  1. greeting                                                     │
│  2. product_inquiry (what cakes, prices, ingredients)            │
│  3. order_placement (ready to order)                             │
│  4. order_info_provision (answering agent questions)             │
│  5. customization_request (decorations, special)                 │
│  6. delivery_inquiry (pickup/delivery questions)                 │
│  7. payment_inquiry                                              │
│  8. order_status (where's my order)                              │
│  9. complaint                                                    │
│  10. small_talk                                                  │
└───────────────┬────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTER (Conditional Edges)                    │
│  Routes to appropriate specialized node                          │
└─┬──┬──┬──┬──┬──┬──┬──┬──┬──────────────────────────────────────┘
  │  │  │  │  │  │  │  │  │
  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼  ▼
  
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Product Inquiry  │  │ Order Collector  │  │ Human Escalation │
│                  │  │                  │  │                  │
│ Tool:            │  │ Tools:           │  │ Action:          │
│ • get_products() │  │ • validate_item()│  │ • flag_for_human│
│ • get_price()    │  │ • check_timing() │  │ • notify_operator│
│                  │  │ • add_to_cart()  │  │ • gentle handoff │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Order Finalizer  │  │ Info Provider    │  │ Small Talk       │
│                  │  │                  │  │                  │
│ Actions:         │  │ Info:            │  │ Action:          │
│ • Show summary   │  │ • Pickup address │  │ • Friendly reply │
│ • Confirm prepay │  │ • Payment process│  │ • Redirect focus │
│ • Save to DB     │  │ • Lead time      │  │ • Offer help     │
└──────────────────┘  └──────────────────┘  └──────────────────┘

                ↓
┌─────────────────────────────────────────────────────────────────┐
│               RESPONSE GENERATOR + STATE UPDATE                  │
│  • Generate professional response                                │
│  • Update conversation state in DB                               │
│  • Save message history                                          │
│  • Update order draft if info collected                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
                          WhatsApp Reply
```

---

## 🔧 Core Components

### 1. Conversation State Schema

```python
class ConversationState(TypedDict):
    """Enhanced state for flexible conversation management"""
    
    # Identity
    conversation_id: int
    chat_id: str
    
    # Full conversation history (no message limit)
    messages: List[Dict[str, Any]]  
    # Structure: [{"role": "user/assistant", "content": "...", "timestamp": "...", "intent": "..."}]
    
    # Order draft (flexible, can be partial)
    order_draft: Optional[Dict[str, Any]]
    # Structure:
    # {
    #   "items": [
    #     {"product_id": "...", "name": "...", "quantity": "...", "price": ..., "notes": "..."}
    #   ],
    #   "pickup": {
    #     "date": "YYYY-MM-DD",
    #     "time": "HH:MM",
    #     "method": "self_pickup" | "yandex_courier"
    #   },
    #   "customer": {
    #     "name": "...",
    #     "phone": "...",
    #     "phone2": "..."
    #   },
    #   "payment": {
    #     "method": "kaspi" | "halyk" | "other",
    #     "status": "pending" | "confirmed",
    #     "amount": ...
    #   },
    #   "special_requests": "...",
    #   "total_amount": ...,
    #   "completeness": {
    #     "items": bool,
    #     "pickup_time": bool,
    #     "customer_info": bool,
    #     "payment_confirmed": bool
    #   }
    # }
    
    # Conversation context
    last_intent: str
    conversation_stage: str  # browsing | ordering | confirming | completed | escalated
    clarification_count: int  # Track if agent is stuck
    
    # Flags
    flagged_for_human: bool
    escalation_reason: Optional[str]
    
    # Metadata
    started_at: str  # ISO timestamp
    last_activity: str  # ISO timestamp
    completed_at: Optional[str]
```

### 2. Intent Taxonomy

**10 Intent Categories:**

| Intent | Description | Example User Messages |
|--------|-------------|----------------------|
| `greeting` | Initial hello, hi | "Здравствуйте", "Привет" |
| `product_inquiry` | Questions about products, prices, ingredients | "Какие у вас торты?", "Сколько стоит Наполеон?", "Есть без орехов?" |
| `order_placement` | Ready to order, adding items | "Хочу заказать Наполеон 2кг", "Добавьте ещё шоколадный" |
| `order_info_provision` | Answering agent's questions | "На завтра в 15:00", "Иван, +77001234567" |
| `customization_request` | Special decorations, custom requests | "Можно сердечко сверху?", "Напишите 'С днем рождения'" |
| `delivery_inquiry` | Pickup/delivery questions | "Как забрать?", "Доставляете?", "Где ваш адрес?" |
| `payment_inquiry` | Payment methods, confirmation | "Как оплатить?", "Можно каспи?", "Оплатил, вот чек" |
| `order_status` | Checking existing order | "Где мой заказ?", "Готов ли торт?" |
| `complaint` | Issues, problems | "Торт был не вкусный", "Опоздали с заказом" |
| `small_talk` | Off-topic, casual chat | "Как дела?", "Спасибо" |

### 3. Specialized Nodes

#### **A. Intent Classifier Node**
- **Purpose:** Classify every user message into one of 10 intents
- **Implementation:** GPT-4o-mini with structured output (JSON mode or function calling)
- **Input:** User message + conversation history (last 5 messages for context)
- **Output:** Intent label + confidence score

```python
def classify_intent(state: ConversationState) -> Dict[str, Any]:
    """
    Classify user intent using GPT-4o-mini
    """
    system_prompt = """
    Ты - классификатор намерений для кондитерской Napoleon Tseh.
    
    Классифицируй сообщение пользователя в одну из категорий:
    - greeting
    - product_inquiry
    - order_placement
    - order_info_provision
    - customization_request
    - delivery_inquiry
    - payment_inquiry
    - order_status
    - complaint
    - small_talk
    
    Учитывай контекст предыдущих сообщений.
    """
    
    # Call GPT-4o-mini with JSON mode
    # Return: {"intent": "product_inquiry", "confidence": 0.95}
```

#### **B. Product Inquiry Node**
- **Purpose:** Answer questions about products, prices, ingredients
- **Tools:** 
  - `get_products(category=None, filter=None)` - Query products table
  - `get_product_details(product_id)` - Get specific product info
- **Behavior:**
  - Query products from database
  - Format response professionally
  - Suggest ordering if appropriate
  - Handle follow-up questions

```python
def handle_product_inquiry(state: ConversationState) -> ConversationState:
    """
    Handle product questions
    """
    # Extract what user wants to know
    # Query products table
    # Generate informative response
    # Optionally suggest: "Хотите заказать?"
    # Update state
```

#### **C. Order Collector Node**
- **Purpose:** Extract order information, build cart incrementally
- **Tools:**
  - `validate_item(product_name)` - Check if product exists
  - `add_to_cart(items)` - Add items to order draft
  - `check_timing(pickup_datetime)` - Validate 4hr rule
- **Behavior:**
  - Extract items from user message (LLM extraction)
  - Validate products exist in catalog
  - Add to order draft
  - Calculate running total
  - Ask for missing info (time, contact) if needed

```python
def collect_order(state: ConversationState) -> ConversationState:
    """
    Collect order information
    """
    # Extract items using LLM
    # Validate against products table
    # Add to order_draft
    # Check if pickup time specified
    # If timing < 4hrs, politely decline
    # Ask for missing info
    # Update state
```

#### **D. Order Finalizer Node**
- **Purpose:** Show summary, confirm prepay requirement, save order
- **Actions:**
  - Check order completeness
  - Generate beautiful summary
  - Explain prepay requirement (100% upfront)
  - Provide payment instructions (Kaspi/Halyk)
  - Save to `ai_generated_orders` table
  - Mark conversation as completed

```python
def finalize_order(state: ConversationState) -> ConversationState:
    """
    Finalize and save order
    """
    # Check all required fields present
    # Generate order summary
    # Explain payment process
    # Save to database
    # Send confirmation message
    # Update conversation status
```

#### **E. Human Escalation Node**
- **Purpose:** Smoothly hand off to human operator
- **Actions:**
  - Flag conversation: `flagged_for_human = True`
  - Record escalation reason
  - Send gentle handoff message
  - Notify operator (future: push notification, Telegram alert)
  - Stop AI responses

```python
def escalate_to_human(state: ConversationState, reason: str) -> ConversationState:
    """
    Escalate conversation to human operator
    """
    state["flagged_for_human"] = True
    state["escalation_reason"] = reason
    state["conversation_stage"] = "escalated"
    
    handoff_message = """
    Спасибо за ваш запрос! 
    Для индивидуального оформления я соединяю вас с нашим специалистом.
    Он ответит вам в ближайшее время. ☕
    """
    
    # Notify operator system
    # Update state
```

#### **F. Info Provider Node**
- **Purpose:** Answer logistics questions (pickup, payment, timing)
- **Knowledge Base:**
  - Pickup address in Almaty
  - Payment methods (Kaspi, Halyk)
  - Lead time (4 hours minimum)
  - Yandex courier option

```python
def provide_info(state: ConversationState) -> ConversationState:
    """
    Provide business information
    """
    # Determine what info user needs
    # Provide clear, professional answer
    # Offer to help with order if appropriate
```

#### **G. Small Talk Node**
- **Purpose:** Handle casual conversation, redirect to business
- **Behavior:**
  - Friendly but brief response
  - Gently redirect to ordering/products
  - Maintain professional tone

---

## 🛠️ Tool Layer

### Tool Functions (Python)

```python
# Product Tools
def get_products(category: Optional[str] = None, filter: Optional[Dict] = None) -> List[Dict]:
    """
    Query products table
    Args:
        category: "cakes" | "dessert_sets" | None (all)
        filter: {"allergen_free": ["nuts"], "max_price": 10000}
    Returns:
        List of product dictionaries
    """
    pass

def get_product_details(product_id: str) -> Dict:
    """
    Get detailed info for specific product
    Returns:
        {id, name, description, price, sizes, ingredients, allergens, available}
    """
    pass

# Order Tools
def validate_item(product_name: str) -> Optional[Dict]:
    """
    Fuzzy match product name to catalog
    Returns:
        Product dict if found, None otherwise
    """
    pass

def add_to_cart(state: ConversationState, items: List[Dict]) -> ConversationState:
    """
    Add items to order draft
    """
    pass

def calculate_total(items: List[Dict]) -> float:
    """
    Calculate total price
    """
    pass

def check_timing(pickup_datetime: datetime) -> Dict:
    """
    Validate pickup time meets 4hr minimum
    Returns:
        {"valid": bool, "hours_until": float, "message": str}
    """
    pass

# Persistence Tools
def save_order_draft(state: ConversationState) -> None:
    """
    Save partial order to DB (auto-save)
    """
    pass

def finalize_order_db(state: ConversationState) -> int:
    """
    Create final order record in ai_generated_orders table
    Returns:
        order_id
    """
    pass
```

---

## 🚨 Escalation Logic (10% Human / 90% AI Goal)

### Automatic Escalation Triggers

```python
def should_escalate_to_human(state: ConversationState) -> Tuple[bool, Optional[str]]:
    """
    Determine if conversation should be escalated to human
    Returns:
        (should_escalate: bool, reason: str)
    """
    
    # 1. EXPLICIT CUSTOMIZATION REQUESTS
    if state["last_intent"] == "customization_request":
        return True, "custom_decoration_request"
    
    # 2. COMPLAINTS
    if state["last_intent"] == "complaint":
        return True, "customer_complaint"
    
    # 3. HIGH-VALUE ORDERS (>50,000₸)
    if state["order_draft"] and state["order_draft"].get("total_amount", 0) > 50000:
        return True, "high_value_order"
    
    # 4. AGENT CONFUSION (user repeated question 3+ times)
    if state["clarification_count"] >= 3:
        return True, "agent_unable_to_help"
    
    # 5. EXPLICIT REQUEST FOR HUMAN
    keywords = ["менеджер", "оператор", "человек", "специалист", "сотрудник"]
    if any(kw in state["messages"][-1]["content"].lower() for kw in keywords):
        return True, "explicit_human_request"
    
    # 6. COMPLEX MULTI-ITEM URGENT ORDERS
    if state["order_draft"]:
        items_count = len(state["order_draft"].get("items", []))
        is_urgent = "срочно" in state["messages"][-1]["content"].lower()
        if items_count > 3 and is_urgent:
            return True, "complex_urgent_order"
    
    # 7. ORDER STATUS INQUIRIES (need to check existing orders)
    if state["last_intent"] == "order_status":
        return True, "order_status_check"
    
    return False, None
```

### Escalation Priority Levels

| Priority | Reason | Response Time SLA |
|----------|--------|-------------------|
| 🔴 High | Complaint, High-value order | < 5 minutes |
| 🟡 Medium | Customization, Complex order | < 15 minutes |
| 🟢 Low | Order status, Agent confusion | < 30 minutes |

---

## 💬 Professional Greeting Message

**First Message (Brand Introduction):**

```
Здравствуйте! 🍰

Вас приветствует Napoleon Tseh — авторские торты Наполеон премиум-класса.

Я — AI-ассистент компании, помогу вам оформить заказ или ответить на вопросы о наших изделиях. Все торты изготавливаются на заказ специально для вас — никаких готовых изделий с витрины!

Как я могу вам помочь?
```

**Subsequent Messages:**
- No repeated greeting
- Context-aware responses
- Natural conversation flow

---

## 📊 Example Conversation Flows

### Flow 1: Information Seeker → Order

```
User: "Здравствуйте, какие у вас торты?"
Intent: greeting + product_inquiry
Node: Product Inquiry
Response: 
    "Здравствуйте! 🍰
    
    У нас в Napoleon Tseh представлены авторские торты Наполеон:
    
    🎂 Наполеон Классический - 8000₸/кг
    🍫 Наполеон Шоколадный - 9000₸/кг
    🍓 Наполеон Клубничный - 9500₸/кг
    ☕ Наполеон Кофейный - 9000₸/кг
    
    Также у нас есть десертные наборы (6 порционных пирожных) - 4500₸
    
    Все изделия изготавливаются на заказ. Какой торт вас интересует?"

User: "А есть без орехов? У меня аллергия"
Intent: product_inquiry
Node: Product Inquiry → Tool: get_products(filter={"allergen_free": ["nuts"]})
Response:
    "Конечно! Без орехов у нас:
    
    ✅ Наполеон Классический
    ✅ Наполеон Шоколадный
    ✅ Наполеон Клубничный
    
    Все три варианта полностью без орехов. Хотите оформить заказ?"

User: "Да, хочу Наполеон классический 2кг на завтра в 16:00"
Intent: order_placement
Node: Order Collector
Tools: 
    - validate_item("Наполеон классический") ✓
    - add_to_cart([{product_id: "napoleon_classic", quantity: "2kg"}])
    - check_timing("tomorrow 16:00") ✓ (>4 hours)
Response:
    "Отлично! ✅
    
    Ваш заказ:
    • Наполеон Классический 2кг - 16,000₸
    
    Готово к самовывозу: завтра в 16:00
    
    Для подтверждения заказа нужны:
    1. Ваше имя и номер телефона
    2. Предоплата 100% (16,000₸)
    
    Как вас зовут?"

User: "Алия, +77001234567"
Intent: order_info_provision
Node: Order Collector (update customer info)
Response:
    "Спасибо, Алия! 📱
    
    Для оплаты переведите 16,000₸ на наш Kaspi:
    +7 700 123 4567 (Napoleon Tseh)
    
    После оплаты пришлите скриншот чека, и мы начнём готовить ваш торт! 🍰
    
    Адрес самовывоза: ул. Абая 50, Алматы
    Или можете вызвать Яндекс курьер к нам."

User: "Оплатила, вот чек [image]"
Intent: payment_inquiry
Node: Order Finalizer
Action: Save order to DB, mark as confirmed
Response:
    "Оплата получена! ✅
    
    Ваш заказ №2547 принят в работу:
    • Наполеон Классический 2кг
    • Готовность: 16 янв, 16:00
    • Самовывоз: ул. Абая 50
    
    Ждём вас завтра! Если будут вопросы, пишите. 🎉"
```

### Flow 2: Direct Order (No Questions)

```
User: "Хочу заказать Наполеон шоколадный 1.5кг и клубничный 1кг на пятницу в 18:00"
Intent: order_placement
Node: Order Collector
Tools:
    - validate_item("Наполеон шоколадный") ✓
    - validate_item("клубничный") ✓
    - add_to_cart([...])
    - check_timing("friday 18:00") ✓
Response:
    "Отлично! 🍰
    
    Ваш заказ:
    • Наполеон Шоколадный 1.5кг - 13,500₸
    • Наполеон Клубничный 1кг - 9,500₸
    ──────────────────────
    Итого: 23,000₸
    
    Готово к самовывозу: пятница, 18:00
    
    Для подтверждения нужны ваше имя и номер телефона."

[... continues with payment flow]
```

### Flow 3: Customization Request → Human Escalation

```
User: "Хочу торт на свадьбу, можно сердечко из крема сверху и надпись золотом?"
Intent: customization_request
Escalation Check: should_escalate_to_human() → True (customization)
Node: Human Escalation
Response:
    "Спасибо за ваш запрос! 💝
    
    Для индивидуального оформления (декор, надписи) я соединяю вас с нашим мастером-кондитером.
    
    Он свяжется с вами в ближайшее время и обсудит все детали вашего торта. ☕
    
    Ожидайте сообщение!"

[Conversation flagged, operator notified]
[AI stops responding to this conversation]
```

### Flow 4: Question Mid-Order (Context Switch)

```
User: "Хочу заказать торт на завтра"
Intent: order_placement
Node: Order Collector
Response:
    "С удовольствием! 🍰
    
    Какой торт хотите заказать? У нас есть:
    • Наполеон Классический (8000₸/кг)
    • Наполеон Шоколадный (9000₸/кг)
    • Наполеон Клубничный (9500₸/кг)
    • Наполеон Кофейный (9000₸/кг)"

User: "А какой у вас самый популярный?"
Intent: product_inquiry (context switch!)
Node: Product Inquiry
Response:
    "Наш хит — Наполеон Классический! 🌟
    
    Это наш фирменный рецепт: нежнейшие коржи, тающий крем, классический вкус. Именно его выбирают чаще всего.
    
    Хотите заказать Классический?"

User: "Да, 2кг"
Intent: order_placement
Node: Order Collector (resumes order)
Response:
    "Отлично! Наполеон Классический 2кг - 16,000₸
    
    На какое время готовить? (завтра)"

[... continues]
```

---

## 📦 Product Catalog Structure

### Database Schema

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    
    -- Identity
    product_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., "napoleon_classic"
    name VARCHAR(200) NOT NULL,              -- "Торт Наполеон Классический"
    category VARCHAR(50) NOT NULL,           -- "cake" | "dessert_set" | "pastry"
    
    -- Details
    description TEXT,
    price_per_kg DECIMAL(10, 2),             -- For cakes
    fixed_price DECIMAL(10, 2),              -- For sets
    available BOOLEAN DEFAULT true,
    
    -- Attributes
    sizes JSONB,                              -- ["1kg", "1.5kg", "2kg", "3kg"]
    ingredients JSONB,                        -- ["мука", "масло", "яйца", ...]
    allergens JSONB,                          -- ["глютен", "яйца", "молоко"]
    
    -- Business rules
    preparation_hours INTEGER DEFAULT 4,     -- Minimum lead time
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_available ON products(available);
```

### Sample Products Data

```json
[
  {
    "product_id": "napoleon_classic",
    "name": "Торт Наполеон Классический",
    "category": "cake",
    "description": "Наш фирменный торт с нежными коржами и классическим заварным кремом",
    "price_per_kg": 8000,
    "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
    "ingredients": ["мука", "масло", "яйца", "сахар", "молоко", "ваниль"],
    "allergens": ["глютен", "яйца", "молоко"],
    "preparation_hours": 4,
    "available": true
  },
  {
    "product_id": "napoleon_chocolate",
    "name": "Торт Наполеон Шоколадный",
    "category": "cake",
    "description": "Шоколадные коржи с нежным шоколадным кремом",
    "price_per_kg": 9000,
    "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
    "ingredients": ["мука", "масло", "яйца", "сахар", "какао", "шоколад"],
    "allergens": ["глютен", "яйца", "молоко"],
    "preparation_hours": 4,
    "available": true
  },
  {
    "product_id": "napoleon_strawberry",
    "name": "Торт Наполеон Клубничный",
    "category": "cake",
    "description": "Классические коржи с клубничным кремом и свежей клубникой",
    "price_per_kg": 9500,
    "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
    "ingredients": ["мука", "масло", "яйца", "сахар", "клубника", "сливки"],
    "allergens": ["глютен", "яйца", "молоко"],
    "preparation_hours": 4,
    "available": true
  },
  {
    "product_id": "napoleon_coffee",
    "name": "Торт Наполеон Кофейный",
    "category": "cake",
    "description": "Ароматные коржи с кофейным кремом для любителей кофе",
    "price_per_kg": 9000,
    "sizes": ["1kg", "1.5kg", "2kg", "3kg"],
    "ingredients": ["мука", "масло", "яйца", "сахар", "кофе", "сливки"],
    "allergens": ["глютен", "яйца", "молоко", "кофеин"],
    "preparation_hours": 4,
    "available": true
  },
  {
    "product_id": "mini_napoleon_set",
    "name": "Набор мини-Наполеонов",
    "category": "dessert_set",
    "description": "6 порционных пирожных Наполеон - идеально для чаепития",
    "fixed_price": 4500,
    "ingredients": ["мука", "масло", "яйца", "сахар", "молоко"],
    "allergens": ["глютен", "яйца", "молоко"],
    "preparation_hours": 4,
    "available": true
  }
]
```

---

## 🔄 LangGraph Implementation

### Graph Structure

```python
from langgraph.graph import StateGraph, END
from typing import Literal

# Create graph
workflow = StateGraph(ConversationState)

# Add nodes
workflow.add_node("pre_routing_check", pre_routing_check_node)
workflow.add_node("intent_classifier", classify_intent_node)
workflow.add_node("product_inquiry", handle_product_inquiry_node)
workflow.add_node("order_collector", collect_order_node)
workflow.add_node("order_finalizer", finalize_order_node)
workflow.add_node("human_escalation", escalate_to_human_node)
workflow.add_node("info_provider", provide_info_node)
workflow.add_node("small_talk", handle_small_talk_node)

# Entry point
workflow.set_entry_point("pre_routing_check")

# Pre-routing edges
def route_after_pre_check(state: ConversationState) -> Literal["human_queue", "greeting", "classifier"]:
    if state.get("flagged_for_human"):
        return "human_queue"
    if state.get("is_first_message"):
        return "greeting"
    return "classifier"

workflow.add_conditional_edges(
    "pre_routing_check",
    route_after_pre_check,
    {
        "human_queue": END,  # Stop AI processing
        "greeting": END,     # Send greeting and wait for next message
        "classifier": "intent_classifier"
    }
)

# Intent classifier routing
def route_by_intent(state: ConversationState) -> str:
    intent = state["last_intent"]
    
    intent_routing = {
        "greeting": "product_inquiry",  # Greet + offer help
        "product_inquiry": "product_inquiry",
        "order_placement": "order_collector",
        "order_info_provision": "order_collector",
        "customization_request": "human_escalation",
        "delivery_inquiry": "info_provider",
        "payment_inquiry": "info_provider",
        "order_status": "human_escalation",
        "complaint": "human_escalation",
        "small_talk": "small_talk"
    }
    
    return intent_routing.get(intent, "small_talk")

workflow.add_conditional_edges(
    "intent_classifier",
    route_by_intent,
    {
        "product_inquiry": "product_inquiry",
        "order_collector": "order_collector",
        "order_finalizer": "order_finalizer",
        "human_escalation": "human_escalation",
        "info_provider": "info_provider",
        "small_talk": "small_talk"
    }
)

# All nodes end after processing (wait for next message)
workflow.add_edge("product_inquiry", END)
workflow.add_edge("order_collector", END)
workflow.add_edge("order_finalizer", END)
workflow.add_edge("human_escalation", END)
workflow.add_edge("info_provider", END)
workflow.add_edge("small_talk", END)

# Compile
order_agent = workflow.compile()
```

---

## 💾 Database Schema Additions

### Enhanced Conversations Table

```sql
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS flagged_for_human BOOLEAN DEFAULT false;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS escalation_reason VARCHAR(100);
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS conversation_stage VARCHAR(50) DEFAULT 'browsing';
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS clarification_count INTEGER DEFAULT 0;
```

### Order Draft Auto-Save

Order draft is saved in `ai_generated_orders` table with:
- `validation_status = 'draft'` (while building)
- `validation_status = 'pending'` (awaiting payment)
- `validation_status = 'confirmed'` (payment received)

---

## 🎯 Success Metrics

### AI Performance KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Automation Rate** | 90% | (AI-handled / Total conversations) × 100 |
| **Escalation Rate** | 10% | (Human-escalated / Total conversations) × 100 |
| **Order Completion Rate** | 70% | (Orders finalized / Orders started) × 100 |
| **Avg Response Time** | <3 sec | Time from user message to AI reply |
| **Customer Satisfaction** | >4.5/5 | Post-conversation survey |
| **Intent Classification Accuracy** | >95% | Manual review sample |

### Escalation Breakdown Target

| Escalation Reason | % of Total Escalations |
|-------------------|------------------------|
| Customization requests | 40% |
| High-value orders | 20% |
| Complaints | 15% |
| Order status inquiries | 15% |
| Agent confusion | 5% |
| Explicit human requests | 5% |

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure ✅
- [ ] Enhanced `ConversationState` schema
- [ ] Products table migration
- [ ] Sample products data seeding
- [ ] Database schema updates (flagged_for_human, etc.)

### Phase 2: Intent Classification 🎯
- [ ] Intent classifier node with GPT-4o-mini
- [ ] Intent taxonomy prompts
- [ ] Routing logic implementation
- [ ] Testing with sample messages

### Phase 3: Specialized Nodes 🔨
- [ ] Product Inquiry Node + tools
- [ ] Order Collector Node + tools
- [ ] Order Finalizer Node
- [ ] Human Escalation Node
- [ ] Info Provider Node
- [ ] Small Talk Node

### Phase 4: Tool Layer 🔧
- [ ] `get_products()` tool
- [ ] `validate_item()` tool
- [ ] `check_timing()` tool
- [ ] `add_to_cart()` tool
- [ ] `calculate_total()` tool
- [ ] `finalize_order_db()` tool

### Phase 5: Integration & Testing 🧪
- [ ] LangGraph workflow assembly
- [ ] AI agent worker integration
- [ ] WhatsApp message flow testing
- [ ] End-to-end conversation testing
- [ ] Edge case handling

### Phase 6: Professional Greeting 💬
- [ ] First-message detection
- [ ] Brand-appropriate greeting
- [ ] No greeting loop bug

### Phase 7: Monitoring & Optimization 📊
- [ ] Logging system (intent accuracy, escalations)
- [ ] Performance metrics dashboard
- [ ] A/B testing prompts
- [ ] Token usage optimization

---

## 🔒 Security & Privacy

- **Data retention:** 90 days for conversations, indefinite for orders
- **PII handling:** Phone numbers, names stored securely
- **Payment info:** Never store payment credentials, only confirmation status
- **Operator access:** Human operators can view flagged conversations only
- **API keys:** OpenAI key stored in environment variables, not in code

---

## 📚 Technology Stack

### AI & ML
- **OpenAI GPT-4o-mini** - Intent classification, NLU, response generation
- **LangGraph** - Workflow orchestration, state management
- **LangChain** - LLM integration, prompt templates

### Backend
- **FastAPI** - API server, webhooks
- **PostgreSQL** - Relational database (products, orders, conversations)
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations

### Messaging
- **RabbitMQ** - Message queue
- **Pika** - Python RabbitMQ client
- **Green API** - WhatsApp integration

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

---

## 🔗 Related Documentation

- `README.md` - Project overview and setup
- `AI_AGENT_SETUP.md` - Original setup guide (to be deprecated)
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Service orchestration

---

## 📝 Notes & Future Enhancements

### Immediate Priorities
1. Implement Phase 1-3 (Core + Intent + Nodes)
2. Test with real conversations
3. Iterate on prompts based on accuracy

### Future Enhancements
- **Payment verification API integration** (Kaspi, Halyk transaction status check)
- **Order status tracking** (AI can check order progress)
- **Customer preferences memory** (remember favorite cakes)
- **Proactive reminders** ("Your order ready in 1 hour!")
- **Multi-language support** (Russian + Kazakh)
- **Voice notes support** (transcribe with Whisper API)
- **Image recognition** (identify cake in photo, suggest similar)
- **Operator dashboard** (view flagged conversations, respond directly)
- **Analytics dashboard** (conversation metrics, popular products)

### Known Limitations
- **Payment validation manual** - Operator must confirm payment screenshot
- **No delivery logistics** - Customer handles pickup/courier
- **No inventory management** - Assumes unlimited capacity
- **Single operator queue** - No load balancing between multiple operators

---

**End of Architecture Document**

*This document is the source of truth for Napoleon Tseh AI Agent architecture. All implementation should reference this document for consistency.*
