"""Celery tasks."""
import asyncio
import time
import httpx
from datetime import datetime
from typing import Optional
from uuid import UUID

from celery import shared_task

from app.core.config import get_settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Rate limiting: 20 messages per second for Telegram
RATE_LIMIT_MESSAGES_PER_SECOND = 20
RATE_LIMIT_INTERVAL = 1.0 / RATE_LIMIT_MESSAGES_PER_SECOND  # 0.05 seconds


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3)
def process_generation(self, generation_id: str):
    """Process image generation task.
    
    This task is responsible for:
    1. Calling Wavespeed API
    2. Waiting for completion
    3. Updating generation status
    4. Storing results
    """
    try:
        logger.info("Processing generation", generation_id=generation_id)
        
        # TODO: Implement actual generation processing
        # This would involve:
        # 1. Getting generation from DB
        # 2. Calling Wavespeed API
        # 3. Polling for status
        # 4. Updating DB with results
        
        return {"status": "completed", "generation_id": generation_id}
        
    except Exception as exc:
        logger.error(
            "Generation processing failed",
            generation_id=generation_id,
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True)
def start_broadcast_task(self, broadcast_id: int):
    """Start a broadcast - prepare recipients and begin sending.
    
    This task:
    1. Updates broadcast status to running
    2. Gets filtered user list
    3. Queues individual send tasks
    """
    from app.db.session import sync_session_factory
    from app.db.models import Broadcast, BroadcastStatus
    
    logger.info("Starting broadcast", broadcast_id=broadcast_id)
    
    try:
        with sync_session_factory() as session:
            # Get broadcast
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if not broadcast:
                logger.error("Broadcast not found", broadcast_id=broadcast_id)
                return {"error": "Broadcast not found"}
            
            if broadcast.status != BroadcastStatus.pending:
                logger.warning("Broadcast not pending", broadcast_id=broadcast_id, status=broadcast.status.value)
                return {"error": f"Broadcast is {broadcast.status.value}"}
            
            # Update status to running
            broadcast.status = BroadcastStatus.running
            broadcast.started_at = datetime.utcnow()
            session.commit()
            
            # Get filtered user IDs
            user_ids = _get_filtered_user_ids(session, broadcast.filter_type, broadcast.filter_params)
            
            # Update total users count
            broadcast.total_users = len(user_ids)
            session.commit()
            
            logger.info("Broadcasting to users", broadcast_id=broadcast_id, total_users=len(user_ids))
            
            # Queue individual send tasks with rate limiting
            for telegram_id in user_ids:
                send_broadcast_message.apply_async(
                    args=[
                        broadcast_id,
                        telegram_id,
                        broadcast.content_type,
                        broadcast.text,
                        broadcast.media_file_id,
                        broadcast.inline_button_text,
                        broadcast.inline_button_url,
                    ],
                    countdown=0,  # Will be rate limited in the task
                )
        
        return {"status": "started", "total_users": len(user_ids)}
        
    except Exception as exc:
        logger.exception("Failed to start broadcast", broadcast_id=broadcast_id, error=str(exc))
        
        # Mark as failed
        try:
            with sync_session_factory() as session:
                broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                if broadcast:
                    broadcast.status = BroadcastStatus.failed
                    broadcast.completed_at = datetime.utcnow()
                    session.commit()
        except:
            pass
        
        return {"error": str(exc)}


def _get_filtered_user_ids(session, filter_type: str, filter_params: Optional[dict] = None) -> list:
    """Get user IDs matching the filter (sync version)."""
    from datetime import timedelta
    from sqlalchemy import func
    from app.db.models import User, LedgerEntry
    
    now = datetime.utcnow()
    
    if filter_type == "all":
        users = session.query(User.telegram_id).filter(User.is_banned == False).all()
    
    elif filter_type == "active_7d":
        cutoff = now - timedelta(days=7)
        users = session.query(User.telegram_id).filter(
            User.is_banned == False,
            User.last_active_at >= cutoff,
        ).all()
    
    elif filter_type == "active_30d":
        cutoff = now - timedelta(days=30)
        users = session.query(User.telegram_id).filter(
            User.is_banned == False,
            User.last_active_at >= cutoff,
        ).all()
    
    elif filter_type == "with_balance":
        balance_subq = (
            session.query(
                LedgerEntry.user_id,
                func.sum(LedgerEntry.amount).label("balance")
            )
            .group_by(LedgerEntry.user_id)
            .having(func.sum(LedgerEntry.amount) > 0)
            .subquery()
        )
        users = (
            session.query(User.telegram_id)
            .join(balance_subq, User.id == balance_subq.c.user_id)
            .filter(User.is_banned == False)
            .all()
        )
    
    elif filter_type == "paid_users":
        paid_subq = (
            session.query(LedgerEntry.user_id)
            .filter(LedgerEntry.entry_type == "deposit")
            .distinct()
            .subquery()
        )
        users = (
            session.query(User.telegram_id)
            .join(paid_subq, User.id == paid_subq.c.user_id)
            .filter(User.is_banned == False)
            .all()
        )
    
    elif filter_type == "new_users":
        cutoff = now - timedelta(days=7)
        users = session.query(User.telegram_id).filter(
            User.is_banned == False,
            User.created_at >= cutoff,
        ).all()
    
    else:
        users = session.query(User.telegram_id).filter(User.is_banned == False).all()
    
    return [u[0] for u in users]


@shared_task(bind=True, max_retries=2, rate_limit='20/s')
def send_broadcast_message(
    self,
    broadcast_id: int,
    telegram_id: int,
    content_type: str,
    text: Optional[str] = None,
    media_file_id: Optional[str] = None,
    inline_button_text: Optional[str] = None,
    inline_button_url: Optional[str] = None,
):
    """Send broadcast message to a single user.
    
    Rate limited to 20 messages per second by Celery.
    """
    from sqlalchemy import update
    from app.db.session import sync_session_factory
    from app.db.models import Broadcast, BroadcastRecipient, BroadcastStatus, User
    
    try:
        # Check if broadcast is still running
        with sync_session_factory() as session:
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if not broadcast or broadcast.status == BroadcastStatus.cancelled:
                logger.info("Broadcast cancelled, skipping", broadcast_id=broadcast_id, telegram_id=telegram_id)
                return {"status": "skipped", "reason": "cancelled"}
            
            admin_id = broadcast.admin_id
        
        # Send message via Telegram Bot API
        result = _send_telegram_message(
            telegram_id=telegram_id,
            content_type=content_type,
            text=text,
            media_file_id=media_file_id,
            inline_button_text=inline_button_text,
            inline_button_url=inline_button_url,
        )
        
        # Update counters atomically
        with sync_session_factory() as session:
            # Use atomic update to avoid race conditions
            if result["success"]:
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(sent_count=Broadcast.sent_count + 1)
                )
                status = "sent"
            elif result.get("blocked"):
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(blocked_count=Broadcast.blocked_count + 1)
                )
                status = "blocked"
            else:
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(failed_count=Broadcast.failed_count + 1)
                )
                status = "failed"
            
            # Get user_id from telegram_id
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            user_id = user.id if user else None
            
            # Add recipient record
            if user_id:
                recipient = BroadcastRecipient(
                    broadcast_id=broadcast_id,
                    user_id=user_id,
                    telegram_id=telegram_id,
                    status=status,
                    error_message=result.get("error"),
                    sent_at=datetime.utcnow(),
                )
                session.add(recipient)
            
            session.commit()
            
            # Re-fetch broadcast to check completion
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if broadcast:
                total_processed = (
                    (broadcast.sent_count or 0) +
                    (broadcast.failed_count or 0) +
                    (broadcast.blocked_count or 0)
                )
                if total_processed >= broadcast.total_users and broadcast.status != BroadcastStatus.completed:
                    broadcast.status = BroadcastStatus.completed
                    broadcast.completed_at = datetime.utcnow()
                    session.commit()
                    
                    logger.info("Broadcast completed", broadcast_id=broadcast_id)
                    
                    # Send notification to admin
                    _notify_admin_broadcast_completed(
                        admin_id=admin_id,
                        broadcast_id=broadcast_id,
                        public_id=broadcast.public_id,
                        total=broadcast.total_users,
                        sent=broadcast.sent_count or 0,
                        failed=broadcast.failed_count or 0,
                        blocked=broadcast.blocked_count or 0,
                    )
        
        return result
        
    except Exception as exc:
        logger.error(
            "Broadcast message failed",
            broadcast_id=broadcast_id,
            telegram_id=telegram_id,
            error=str(exc),
        )
        
        # Update failed counter atomically
        try:
            from sqlalchemy import update
            from app.db.session import sync_session_factory
            from app.db.models import Broadcast, BroadcastStatus
            
            with sync_session_factory() as session:
                session.execute(
                    update(Broadcast)
                    .where(Broadcast.id == broadcast_id)
                    .values(failed_count=Broadcast.failed_count + 1)
                )
                session.commit()
                
                # Check completion
                broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
                if broadcast:
                    total_processed = (
                        (broadcast.sent_count or 0) +
                        (broadcast.failed_count or 0) +
                        (broadcast.blocked_count or 0)
                    )
                    if total_processed >= broadcast.total_users and broadcast.status != BroadcastStatus.completed:
                        broadcast.status = BroadcastStatus.completed
                        broadcast.completed_at = datetime.utcnow()
                        session.commit()
                        
                        _notify_admin_broadcast_completed(
                            admin_id=broadcast.admin_id,
                            broadcast_id=broadcast_id,
                            public_id=broadcast.public_id,
                            total=broadcast.total_users,
                            sent=broadcast.sent_count or 0,
                            failed=broadcast.failed_count or 0,
                            blocked=broadcast.blocked_count or 0,
                        )
        except Exception as inner_exc:
            logger.error("Failed to update broadcast counter", error=str(inner_exc))
        
        # Return error instead of retrying (message may have been sent)
        return {"success": False, "error": str(exc)}


def _notify_admin_broadcast_completed(
    admin_id: int,
    broadcast_id: int,
    public_id: str,
    total: int,
    sent: int,
    failed: int,
    blocked: int,
) -> None:
    """Send notification to admin when broadcast is completed."""
    bot_token = settings.bot_token
    if not bot_token:
        logger.warning("BOT_TOKEN not configured, skipping admin notification")
        return
    
    success_rate = (sent / total * 100) if total > 0 else 0
    
    message = (
        f"✅ <b>Broadcast Completed!</b>\n\n"
        f"📋 ID: <code>{public_id}</code>\n\n"
        f"📊 <b>Results:</b>\n"
        f"👥 Total: {total}\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"🚫 Blocked: {blocked}\n"
        f"📈 Success Rate: {success_rate:.1f}%"
    )
    
    try:
        import httpx
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "HTML",
                },
            )
            if not response.json().get("ok"):
                logger.warning(
                    "Failed to send admin notification",
                    admin_id=admin_id,
                    error=response.json(),
                )
    except Exception as e:
        logger.error("Failed to send admin notification", error=str(e))


def _send_telegram_message(
    telegram_id: int,
    content_type: str,
    text: Optional[str] = None,
    media_file_id: Optional[str] = None,
    inline_button_text: Optional[str] = None,
    inline_button_url: Optional[str] = None,
) -> dict:
    """Send a message via Telegram Bot API (sync)."""
    bot_token = settings.bot_token
    if not bot_token:
        return {"success": False, "error": "BOT_TOKEN not configured"}
    
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    # Build inline keyboard if button provided
    reply_markup = None
    if inline_button_text and inline_button_url:
        reply_markup = {
            "inline_keyboard": [[
                {"text": inline_button_text, "url": inline_button_url}
            ]]
        }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            if content_type == "text":
                payload = {
                    "chat_id": telegram_id,
                    "text": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendMessage", json=payload)
            
            elif content_type == "photo":
                payload = {
                    "chat_id": telegram_id,
                    "photo": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendPhoto", json=payload)
            
            elif content_type == "video":
                payload = {
                    "chat_id": telegram_id,
                    "video": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendVideo", json=payload)
            
            elif content_type == "audio":
                payload = {
                    "chat_id": telegram_id,
                    "audio": media_file_id,
                    "caption": text or "",
                    "parse_mode": "HTML",
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                response = client.post(f"{base_url}/sendAudio", json=payload)
            
            elif content_type == "sticker":
                payload = {
                    "chat_id": telegram_id,
                    "sticker": media_file_id,
                }
                response = client.post(f"{base_url}/sendSticker", json=payload)
            
            else:
                return {"success": False, "error": f"Unknown content type: {content_type}"}
            
            data = response.json()
            
            if data.get("ok"):
                return {"success": True, "telegram_id": telegram_id}
            else:
                error_code = data.get("error_code", 0)
                description = data.get("description", "Unknown error")
                
                # Check if user blocked bot
                if error_code == 403 or "blocked" in description.lower() or "deactivated" in description.lower():
                    return {"success": False, "blocked": True, "error": description}
                
                return {"success": False, "error": description}
    
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_generations():
    """Cleanup expired/stuck generations.
    
    This task runs periodically to:
    1. Find stuck generations (pending > 30 minutes)
    2. Mark them as failed
    3. Refund credits if applicable
    """
    logger.info("Running generation cleanup")
    
    # TODO: Implement cleanup logic
    
    return {"cleaned_up": 0}


@shared_task
def send_daily_report(admin_ids: list[int]):
    """Send daily report to admins."""
    logger.info("Sending daily report", admin_ids=admin_ids)
    
    # TODO: Implement daily report generation and sending
    
    return {"sent_to": len(admin_ids)}


@shared_task(bind=True)
def process_broadcast(self, broadcast_id: str):
    """Process entire broadcast.
    
    This task:
    1. Gets all active users
    2. Queues individual messages
    3. Tracks progress
    """
    try:
        logger.info("Starting broadcast", broadcast_id=broadcast_id)
        
        # TODO: Implement broadcast processing
        # This would:
        # 1. Get broadcast details
        # 2. Get all active users
        # 3. Queue send_broadcast_message for each user
        # 4. Update broadcast status
        
        return {"status": "completed", "broadcast_id": broadcast_id}
        
    except Exception as exc:
        logger.error(
            "Broadcast processing failed",
            broadcast_id=broadcast_id,
            error=str(exc),
        )
        raise
