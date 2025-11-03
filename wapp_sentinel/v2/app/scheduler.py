"""
Scheduler for automated daily reports
"""
import os
import asyncio
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.database.database import SessionLocal
from app.services.daily_report_service import DailyReportService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyReportScheduler:
    """Scheduler for automated daily report sending"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.enabled = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"
        self.report_time = os.getenv("DAILY_REPORT_TIME", "08:00")  # HH:MM
        self.report_chat_id = os.getenv("DAILY_REPORT_CHAT_ID", "")
        self.timezone = os.getenv("DAILY_REPORT_TIMEZONE", "Asia/Almaty")
        
    def send_daily_report_job(self):
        """Job function that sends today's report"""
        try:
            logger.info("Starting scheduled daily report job...")
            
            if not self.report_chat_id:
                logger.error("DAILY_REPORT_CHAT_ID not configured. Skipping report.")
                return
            
            # Получаем сегодняшнюю дату
            today = date.today()
            
            # Создаем сессию БД
            db = SessionLocal()
            
            try:
                # Создаем сервис отчетов
                service = DailyReportService(db)
                
                # Генерируем и отправляем отчет
                # Используем asyncio для запуска асинхронной функции
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    service.generate_and_send_report(today, self.report_chat_id)
                )
                
                loop.close()
                
                logger.info(f"Daily report sent successfully: {result}")
                logger.info(f"Date: {today}, Orders: {result.get('orders_count', 0)}")
                
            except Exception as e:
                logger.error(f"Error generating/sending report: {e}", exc_info=True)
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in send_daily_report_job: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        if not self.enabled:
            logger.info("Scheduler is DISABLED (SCHEDULER_ENABLED=false)")
            return
        
        if not self.report_chat_id:
            logger.warning("Scheduler enabled but DAILY_REPORT_CHAT_ID not set!")
            return
        
        try:
            # Парсим время
            hour, minute = map(int, self.report_time.split(":"))
            
            # Добавляем задачу в расписание
            self.scheduler.add_job(
                self.send_daily_report_job,
                trigger=CronTrigger(
                    hour=hour,
                    minute=minute,
                    timezone=self.timezone
                ),
                id='daily_report_job',
                name='Send Daily Order Report',
                replace_existing=True
            )
            
            # Запускаем планировщик
            self.scheduler.start()
            
            logger.info("=" * 60)
            logger.info("📅 Daily Report Scheduler STARTED")
            logger.info(f"   Time: {self.report_time} ({self.timezone})")
            logger.info(f"   Chat ID: {self.report_chat_id}")
            logger.info(f"   Next run: {self.scheduler.get_jobs()[0].next_run_time}")
            logger.info("=" * 60)
            
        except ValueError as e:
            logger.error(f"Invalid DAILY_REPORT_TIME format: {self.report_time}. Use HH:MM format.")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}", exc_info=True)
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_status(self):
        """Get scheduler status"""
        if not self.enabled:
            return {"enabled": False, "message": "Scheduler is disabled"}
        
        if not self.scheduler.running:
            return {"enabled": True, "running": False, "message": "Scheduler not running"}
        
        jobs = self.scheduler.get_jobs()
        if not jobs:
            return {"enabled": True, "running": True, "jobs": []}
        
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger)
            })
        
        return {
            "enabled": True,
            "running": True,
            "chat_id": self.report_chat_id,
            "time": self.report_time,
            "timezone": self.timezone,
            "jobs": job_info
        }


# Глобальный экземпляр планировщика
scheduler_instance = DailyReportScheduler()
