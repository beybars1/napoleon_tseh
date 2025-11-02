import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class OpenAIOrderParser:
    """Service for parsing order messages using OpenAI GPT-3.5-turbo"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        self.system_prompt = """
Вы - помощник для парсинга заказов из мессенджера WhatsApp.
Извлекайте информацию о заказах в структурированном JSON формате.

Сообщения могут быть на русском, казахском, английском или смешанном языке.

ПРАВИЛА ПАРСИНГА:

1. Дата и время доставки (estimated_delivery_datetime):
   - "01.11.25 на 14:00" → "2025-11-01 14:00:00"
   - "1 ноября к 2 часам" → "2025-11-01 14:00:00"
   - "завтра на 10:00" → следующий день + время
   - Если только дата без времени → добавьте 00:00:00
   - Формат: "YYYY-MM-DD HH:MM:SS"

2. Статус оплаты (payment_status):
   - "Оплачено", "paid", "төленген", "оплата прошла" → true
   - "Не оплачено", "unpaid", "төленбеген", "наличные", "при получении" → false
   - Если не указано → null

3. Товары (items):
   - Каждый товар как {"name": "название", "quantity": "количество"}
   - Количество может быть: "1кг", "2шт", "на компанию", "6", "1" и т.д.
   - Извлекайте ВСЕ товары из сообщения

4. Контакты (phone numbers):
   - Извлекайте все номера телефонов (обычно 11 цифр)
   - Первый номер → contact_number_primary
   - Второй номер (если есть) → contact_number_secondary

5. Сотрудник (accepted_by):
   - Обычно имя в конце сообщения
   - Примеры: "Айнур", "Мария", "Асель", "Айгерим"

6. Уверенность (confidence):
   - "high" - дата доставки И товары И контакт найдены
   - "medium" - найдено 2 из 3 ключевых полей
   - "low" - найдено меньше 2 ключевых полей

Возвращайте ТОЛЬКО валидный JSON, без markdown и дополнительного текста.
"""
    
    def parse_order_message(self, message_text: str) -> Dict[str, Any]:
        """
        Parse order message using OpenAI
        
        Args:
            message_text: Raw message text from WhatsApp
            
        Returns:
            Dict with parsed order information
        """
        try:
            user_prompt = f"""
Распарсите следующее сообщение заказа:

{message_text}

Верните JSON в точно таком формате:
{{
  "estimated_delivery_datetime": "YYYY-MM-DD HH:MM:SS или null",
  "payment_status": true/false/null,
  "contact_number_primary": "номер или null",
  "contact_number_secondary": "номер или null",
  "items": [
    {{"name": "название товара", "quantity": "количество"}}
  ],
  "accepted_by": "имя сотрудника или null",
  "confidence": "high/medium/low"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500
            )
            
            # Извлекаем JSON из ответа
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Валидация и нормализация данных
            return self._validate_and_normalize(parsed_data)
            
        except Exception as e:
            print(f"Error parsing order with OpenAI: {e}")
            return self._get_default_response()
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the parsed data"""
        
        # Нормализуем estimated_delivery_datetime
        if data.get('estimated_delivery_datetime'):
            try:
                # Пытаемся распарсить дату
                dt_str = data['estimated_delivery_datetime']
                # Если OpenAI вернул только дату, добавляем время
                if len(dt_str) == 10:  # YYYY-MM-DD
                    dt_str += " 00:00:00"
                data['estimated_delivery_datetime'] = dt_str
            except:
                data['estimated_delivery_datetime'] = None
        
        # Убеждаемся что items это список
        if not isinstance(data.get('items'), list):
            data['items'] = []
        
        # Убеждаемся что payment_status это bool или None
        if data.get('payment_status') not in [True, False, None]:
            data['payment_status'] = None
        
        # Убеждаемся что confidence есть
        if data.get('confidence') not in ['high', 'medium', 'low']:
            data['confidence'] = 'low'
        
        return data
    
    def _get_default_response(self) -> Dict[str, Any]:
        """Return default response when parsing fails"""
        return {
            'estimated_delivery_datetime': None,
            'payment_status': None,
            'contact_number_primary': None,
            'contact_number_secondary': None,
            'items': [],
            'accepted_by': None,
            'confidence': 'low'
        }


# Для тестирования
if __name__ == "__main__":
    parser = OpenAIOrderParser()
    
    test_message = """
Заказ на 01.11.25 
На 14:00
Наполеон фисташковый 1кг 
Наполеон классический на компанию 
Сет 6 

Оплачено 
87078303832
Айнур
"""
    
    result = parser.parse_order_message(test_message)
    print("Parsed order:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
