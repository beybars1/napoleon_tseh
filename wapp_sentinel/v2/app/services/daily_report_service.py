"""
Service for generating and sending daily order reports
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os
import httpx

from app.database.models import Order


class DailyReportService:
    """Service to generate and send daily order reports"""
    
    def __init__(self, db: Session):
        self.db = db
        self.green_api_base_url = os.getenv("GREEN_API_BASE_URL", "https://api.green-api.com")
        self.instance_id = os.getenv("GREENAPI_INSTANCE")
        self.token = os.getenv("GREENAPI_TOKEN")
    
    def get_orders_for_date(self, target_date: date) -> List[Order]:
        """
        Get all orders for a specific delivery date, sorted by delivery time
        
        Args:
            target_date: Date to filter orders by
            
        Returns:
            List of Order objects sorted by estimated_delivery_datetime
        """
        # Создаем datetime для начала и конца дня
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        orders = self.db.query(Order).filter(
            and_(
                Order.estimated_delivery_datetime >= start_of_day,
                Order.estimated_delivery_datetime <= end_of_day
            )
        ).order_by(Order.estimated_delivery_datetime.asc()).all()
        
        return orders
    
    def format_header(self, target_date: date, order_count: int) -> str:
        """
        Format the header message for the daily report
        
        Args:
            target_date: Date for the report header
            order_count: Total number of orders
            
        Returns:
            Formatted header text
        """
        if order_count == 0:
            return f"📋 ЗАКАЗЫ НА {target_date.strftime('%d.%m.%Y')}\n\nЗаказов на эту дату нет."
        
        return f"📋 ЗАКАЗЫ НА {target_date.strftime('%d.%m.%Y')}\nВсего заказов: {order_count}"
    
    def format_single_order(self, order: Order, order_number: int) -> str:
        """
        Format a single order as a message
        
        Args:
            order: Order object
            order_number: Order sequence number in the report
            
        Returns:
            Formatted order text
        """
        order_lines = [
            "─" * 20,
            f"ЗАКАЗ #{order_number}"
        ]
        
        # Время доставки
        if order.estimated_delivery_datetime:
            delivery_time = order.estimated_delivery_datetime.strftime('%H:%M')
            order_lines.append(f"🕐 Время доставки: {delivery_time}")
        
        # Статус оплаты
        if order.payment_status is not None:
            payment = "✅ Оплачено" if order.payment_status else "❌ Не оплачено"
            order_lines.append(f"💳 {payment}")
        
        # Имя клиента
        if order.client_name:
            order_lines.append(f"👤 Клиент: {order.client_name}")
        
        # Контакты
        if order.contact_number_primary:
            order_lines.append(f"📱 Контакт: {order.contact_number_primary}")
        if order.contact_number_secondary:
            order_lines.append(f"📱 Доп: {order.contact_number_secondary}")
        
        # Товары
        if order.items:
            order_lines.append("📦 Товары:")
            for item in order.items:
                item_name = item.get('name', 'Неизвестно')
                item_qty = item.get('quantity', '')
                if item_qty:
                    order_lines.append(f"   • {item_name} - {item_qty}")
                else:
                    order_lines.append(f"   • {item_name}")
        
        # Дата принятия заказа
        if order.order_accepted_date:
            accepted = order.order_accepted_date.strftime('%d.%m.%Y %H:%M')
            order_lines.append(f"📅 Принят: {accepted}")
        
        order_lines.append("─" * 20)
        
        return "\n".join(order_lines)
    
    def format_statistics(self, orders: List[Order]) -> str:
        """
        Format statistics message for the daily report
        
        Args:
            orders: List of Order objects
            
        Returns:
            Formatted statistics text
        """
        paid_count = sum(1 for o in orders if o.payment_status is True)
        unpaid_count = sum(1 for o in orders if o.payment_status is False)
        
        stats_lines = [
            "─" * 20,
            "📊 СТАТИСТИКА:",
            f"   • Всего заказов: {len(orders)}",
            f"   • Оплачено: {paid_count}",
            f"   • Не оплачено: {unpaid_count}",
            "─" * 20,
        ]
        
        return "\n".join(stats_lines)
    
    def format_report(self, orders: List[Order], target_date: date) -> str:
        """
        Format orders into a readable text report
        
        Args:
            orders: List of Order objects
            target_date: Date for the report header
            
        Returns:
            Formatted text report
        """
        if not orders:
            return f"📋 ЗАКАЗЫ НА {target_date.strftime('%d.%m.%Y')}\n\nЗаказов на эту дату нет."
        
        # Заголовок
        report_lines = [
            f"📋 ЗАКАЗЫ НА {target_date.strftime('%d.%m.%Y')}",
            f"Всего заказов: {len(orders)}",
            ""
        ]
        
        # Каждый заказ
        for idx, order in enumerate(orders, 1):
            order_lines = [
                "─" * 20,
                f"ЗАКАЗ #{idx}"
            ]
            
            # Время доставки
            if order.estimated_delivery_datetime:
                delivery_time = order.estimated_delivery_datetime.strftime('%H:%M')
                order_lines.append(f"🕐 Время доставки: {delivery_time}")
            
            # Статус оплаты
            if order.payment_status is not None:
                payment = "✅ Оплачено" if order.payment_status else "❌ Не оплачено"
                order_lines.append(f"💳 {payment}")
            
            # Имя клиента
            if order.client_name:
                order_lines.append(f"👤 Клиент: {order.client_name}")
            
            # Контакты
            if order.contact_number_primary:
                order_lines.append(f"📱 Контакт: {order.contact_number_primary}")
            if order.contact_number_secondary:
                order_lines.append(f"📱 Доп: {order.contact_number_secondary}")
            
            # Товары
            if order.items:
                order_lines.append("📦 Товары:")
                for item in order.items:
                    item_name = item.get('name', 'Неизвестно')
                    item_qty = item.get('quantity', '')
                    if item_qty:
                        order_lines.append(f"   • {item_name} - {item_qty}")
                    else:
                        order_lines.append(f"   • {item_name}")
            
            # Дата принятия заказа
            if order.order_accepted_date:
                accepted = order.order_accepted_date.strftime('%d.%m.%Y %H:%M')
                order_lines.append(f"📅 Принят: {accepted}")
            
            # Добавляем заказ к отчету
            report_lines.extend(order_lines)
            report_lines.append("")  # Пустая линия после заказа
        
        # Итоговая статистика
        paid_count = sum(1 for o in orders if o.payment_status is True)
        unpaid_count = sum(1 for o in orders if o.payment_status is False)
        
        report_lines.extend([
            "─" * 20,
            "📊 СТАТИСТИКА:",
            f"   • Всего заказов: {len(orders)}",
            f"   • Оплачено: {paid_count}",
            f"   • Не оплачено: {unpaid_count}",
            "─" * 20,
        ])
        
        return "\n".join(report_lines)
    
    async def send_report_to_whatsapp(self, chat_id: str, message: str) -> dict:
        """
        Send formatted report to WhatsApp via GreenAPI
        
        Args:
            chat_id: WhatsApp chat ID to send to
            message: Formatted message text
            
        Returns:
            Response from GreenAPI
        """
        if not self.instance_id or not self.token:
            raise ValueError("GreenAPI credentials not configured")
        
        send_url = f"{self.green_api_base_url}/waInstance{self.instance_id}/sendMessage/{self.token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                send_url,
                json={
                    "chatId": chat_id,
                    "message": message
                },
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def send_multiple_messages(
        self, 
        chat_id: str, 
        messages: List[str], 
        delay_seconds: float = 1.5
    ) -> List[dict]:
        """
        Send multiple messages to WhatsApp with delay between each
        
        Args:
            chat_id: WhatsApp chat ID to send to
            messages: List of message texts to send
            delay_seconds: Delay between messages in seconds (default: 1.5)
            
        Returns:
            List of responses from GreenAPI for each message
        """
        import asyncio
        
        results = []
        
        for idx, message in enumerate(messages):
            try:
                result = await self.send_report_to_whatsapp(chat_id, message)
                results.append({
                    "message_index": idx + 1,
                    "status": "success",
                    "response": result
                })
                
                # Добавляем задержку между сообщениями (кроме последнего)
                if idx < len(messages) - 1:
                    await asyncio.sleep(delay_seconds)
                    
            except Exception as e:
                results.append({
                    "message_index": idx + 1,
                    "status": "failed",
                    "error": str(e)
                })
                # Продолжаем отправку остальных сообщений даже при ошибке
                
        return results
    
    async def generate_and_send_report(
        self, 
        target_date: date, 
        chat_id: str,
        split_messages: bool = True,
        delay_seconds: float = 1.5
    ) -> dict:
        """
        Main method to generate and send daily report
        
        Args:
            target_date: Date to generate report for
            chat_id: WhatsApp chat ID to send to
            split_messages: If True, send as multiple messages (default: True)
            delay_seconds: Delay between messages when split_messages=True (default: 1.5)
            
        Returns:
            Dict with status and details
        """
        # Получаем заказы
        orders = self.get_orders_for_date(target_date)
        
        if split_messages:
            # Отправляем несколькими сообщениями
            messages = []
            
            # 1. Заголовок
            header = self.format_header(target_date, len(orders))
            messages.append(header)
            
            # 2. Если есть заказы, добавляем каждый заказ отдельно
            if orders:
                for idx, order in enumerate(orders, 1):
                    order_text = self.format_single_order(order, idx)
                    messages.append(order_text)
                
                # 3. Статистика
                statistics = self.format_statistics(orders)
                messages.append(statistics)
            
            # Отправляем все сообщения
            send_results = await self.send_multiple_messages(chat_id, messages, delay_seconds)
            
            # Проверяем статус отправки
            failed_count = sum(1 for r in send_results if r.get("status") == "failed")
            
            return {
                "status": "success" if failed_count == 0 else "partial_success",
                "date": target_date.isoformat(),
                "chat_id": chat_id,
                "orders_count": len(orders),
                "messages_sent": len(messages),
                "messages_failed": failed_count,
                "split_mode": True,
                "greenapi_responses": send_results
            }
        else:
            # Отправляем одним сообщением (старый метод)
            report_text = self.format_report(orders, target_date)
            send_result = await self.send_report_to_whatsapp(chat_id, report_text)
            
            return {
                "status": "success",
                "date": target_date.isoformat(),
                "chat_id": chat_id,
                "orders_count": len(orders),
                "split_mode": False,
                "greenapi_response": send_result
            }
