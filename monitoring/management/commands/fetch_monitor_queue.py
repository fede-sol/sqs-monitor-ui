from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.aws_service import fetch_monitor_messages
import time

class Command(BaseCommand):
    help = 'Obtiene mensajes de la cola SQS de monitoreo y los guarda en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            dest='continuous',
            help='Ejecutar en modo continuo, monitoreando constantemente la cola',
        )
        parser.add_argument(
            '--interval',
            type=int,
            dest='interval',
            default=5,
            help='Intervalo en segundos entre verificaciones (en modo continuo)',
        )
        parser.add_argument(
            '--max-messages',
            type=int,
            dest='max_messages',
            default=10,
            help='Número máximo de mensajes a recibir por solicitud',
        )
        parser.add_argument(
            '--wait-time',
            type=int,
            dest='wait_time',
            default=5,
            help='Tiempo de espera en segundos para recibir mensajes (long polling)',
        )

    def handle(self, *args, **options):
        continuous = options['continuous']
        interval = options['interval']
        max_messages = options['max_messages']
        wait_time = options['wait_time']
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando monitoreo de cola SQS dedicada para monitoreo')
        )
        
        if continuous:
            self.stdout.write(
                self.style.WARNING(f'Modo continuo activado. Presiona Ctrl+C para detener.')
            )
            while True:
                try:
                    self._fetch_messages(max_messages, wait_time)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('Monitoreo detenido por el usuario'))
                    break
        else:
            self._fetch_messages(max_messages, wait_time)
    
    def _fetch_messages(self, max_messages, wait_time):
        start_time = timezone.now()
        messages = fetch_monitor_messages(max_messages=max_messages, wait_time=wait_time)
        end_time = timezone.now()
        
        if messages:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se procesaron {len(messages)} mensajes en {(end_time - start_time).total_seconds():.2f} segundos'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No se encontraron mensajes nuevos')
            ) 