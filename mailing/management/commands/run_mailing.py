# mailing/management/commands/run_mailing.py
import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ...services import execute_mailing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Принудительно запускает рассылку по её ID, если текущее время находится в окне отправки.'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int, help='ID рассылки, которую нужно запустить.')

    def handle(self, *args, **options):
        mailing_id = options['mailing_id']

        try:
            from mailing.models import Mailing
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            raise CommandError(f'Рассылка с ID {mailing_id} не существует.')

        now = timezone.now()
        if not (mailing.start_time <= now <= mailing.end_time):
            raise CommandError(
                f'Текущее время ({now.strftime("%d.%m.%Y %H:%M")}) вне окна отправки '
                f'({mailing.start_time.strftime("%d.%m.%Y %H:%M")} - {mailing.end_time.strftime("%d.%m.%Y %H:%M")}).'
            )

        self.stdout.write(self.style.SUCCESS(f'Начинаю выполнение рассылки #{mailing_id}...'))

        # Выполнение вынесено в сервис
        execute_mailing(mailing_id)

        self.stdout.write(self.style.SUCCESS(f'Выполнение рассылки #{mailing_id} завершено.'))