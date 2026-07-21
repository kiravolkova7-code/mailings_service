
import logging
import traceback
from django.utils import timezone
from django.core.mail import send_mail, BadHeaderError
import smtplib
from django.conf import settings
from .models import Mailing, SendLog

logger = logging.getLogger(__name__)


def execute_mailing(mailing_id: int):
    try:
        mailing = Mailing.objects.select_related('message').prefetch_related('recipients').get(pk=mailing_id)
    except Mailing.DoesNotExist:
        logger.error(f"Рассылка с ID {mailing_id} не найдена.")
        return

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        allowed_window = f"{mailing.start_time.strftime('%d.%m.%Y %H:%M')} - {mailing.end_time.strftime('%d.%m.%Y %H:%M')}"
        error_msg = f"Сейчас {now.strftime('%d.%m.%Y %H:%M')}. Рассылку можно запустить только в интервале: {allowed_window}."
        logger.warning(error_msg)
        return

    recipients_qs = mailing.recipients.all()
    total_count = recipients_qs.count()

    if total_count == 0:
        logger.info(f"В рассылке #{mailing.pk} нет получателей.")
        return

    logger.info(f"Старт рассылки #{mailing.pk} для {total_count} получателей.")

    for recipient in recipients_qs:
        response_text = None
        log_status = 'success'

        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
        except (BadHeaderError, smtplib.SMTPException, ConnectionError) as e:
            log_status = 'failed'
            response_text = str(e)
            logger.error(f"[{log_status.upper()}] Ошибка отправки на {recipient.email}: {response_text}")

        except Exception as e:
            log_status = 'failed'
            response_text = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.exception(f"[CRITICAL] Неожиданная ошибка при отправке на {recipient.email}")


        finally:
            SendLog.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=log_status,
                server_response=response_text[:2000] if response_text else None
            )

    logger.info(f"Рассылка #{mailing.pk} завершена.")