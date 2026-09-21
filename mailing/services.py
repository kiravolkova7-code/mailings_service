from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Mailing, SendLog


def execute_mailing(mailing_id: int):
    print(f"\n[SERVICE DEBUG] Функция запущена с ID: {mailing_id}")

    try:
        mailing = Mailing.objects.select_related("message").prefetch_related("recipients").get(pk=mailing_id)
        print(f"[SERVICE DEBUG] Объект Mailing загружен. Subject: '{mailing.message.subject}'")
    except Mailing.DoesNotExist:
        print(f"[SERVICE DEBUG ERROR] Рассылка с ID {mailing_id} не найдена!")
        return

    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        print(f"[SERVICE DEBUG TIME CHECK FAILED] Сейчас {now}, а окно: {mailing.start_time} - {mailing.end_time}")
        return

    recipients_qs = mailing.recipients.all()  # Префетч уже сработал выше
    total_count = recipients_qs.count()
    print(f"[SERVICE DEBUG] Найдено получателей: {total_count}")

    if total_count == 0:
        print("[SERVICE DEBUG] Получателей нет. Выход.")
        return

    with transaction.atomic():
        for idx, recipient in enumerate(recipients_qs):
            response_text = None
            log_status = "success"

            print(f"[SERVICE DEBUG LOOP] ---> Итерация {idx + 1}/{total_count}. Email: {recipient.email}")

            try:
                print(f"[SERVICE DEBUG SEND] Пытаюсь отправить письмо...")
                send_mail(
                    subject=mailing.message.subject,
                    message=mailing.message.body_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                print(f"[SERVICE DEBUG SEND SUCCESS] Письмо отправлено на {recipient.email}")

            except Exception as e:
                log_status = "Не успешно"
                response_text = str(e)
                print(f"[SERVICE DEBUG SEND FAILED] ОШИБКА на {recipient.email}: {response_text}")

            finally:
                print(
                    f"[SERVICE DEBUG DB WRITE] Создаю запись SendLog для {recipient.email} со статусом: {log_status}"
                )
                created_log = SendLog.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status=log_status,
                    server_response=response_text[:2000] if response_text else None,
                )
                print(f"[SERVICE DEBUG DB WRITE SUCCESS] Запись создана с PK: {created_log.pk}\n")

    print(f"[SERVICE DEBUG] Рассылка #{mailing.pk} полностью завершена.\n")
