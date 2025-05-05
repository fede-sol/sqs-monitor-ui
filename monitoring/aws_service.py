import boto3
from django.conf import settings
from .models import Message
import json

def get_sqs_client():
    """Inicializa el cliente de SQS usando las credenciales configuradas"""
    # Parámetros básicos incluyendo región
    params = {'region_name': settings.AWS_REGION}
    # Si se configuran credenciales, inclúyelas (con token opcional)
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        params.update({
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        })
        # Token de sesión opcional para credenciales temporales
        if getattr(settings, 'AWS_SESSION_TOKEN', None):
            params['aws_session_token'] = settings.AWS_SESSION_TOKEN
    return boto3.client('sqs', **params)

def list_queues():
    """Devuelve la lista de URLs de las colas SQS"""
    client = get_sqs_client()
    response = client.list_queues()
    return response.get('QueueUrls', [])

def fetch_messages_from_queue(queue_url, max_messages=10, wait_time=1):
    """Recibe mensajes de una cola y los guarda en la base de datos"""
    client = get_sqs_client()
    response = client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=max_messages,
        WaitTimeSeconds=wait_time,
        MessageAttributeNames=['All'],
        AttributeNames=['All']
    )
    messages = response.get('Messages', [])
    for msg in messages:
        msg_id = msg['MessageId']
        # Evitar duplicados
        if not Message.objects.filter(message_id=msg_id).exists():
            raw_body = msg.get('Body')
            attrs = msg.get('MessageAttributes', {})
            topic_arn = None
            subject = None
            # Si TopicArn viene como atributo
            if 'TopicArn' in attrs:
                topic_arn = attrs['TopicArn']['StringValue']
            body = raw_body
            # Si es mensaje de SNS suscrito en SQS, parsear JSON
            try:
                payload = json.loads(raw_body)
                if isinstance(payload, dict):
                    # Extraer TopicArn del payload
                    if not topic_arn and payload.get('TopicArn'):
                        topic_arn = payload.get('TopicArn')
                    # Extraer Subject del payload
                    if payload.get('Subject'):
                        subject = payload.get('Subject')
                    # Reemplazar body con el contenido real del mensaje
                    body = payload.get('Message', raw_body)
            except (ValueError, TypeError):
                pass
            Message.objects.create(
                message_id=msg_id,
                queue_name=queue_url.split('/')[-1],
                topic_arn=topic_arn,
                subject=subject,
                body=body,
                attributes=attrs,
                state='RECEIVED'
            )
        # Eliminar el mensaje para evitar re-procesarlo
        receipt_handle = msg.get('ReceiptHandle')
        if receipt_handle:
            client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    return messages

def fetch_all_messages():
    """Recorre todas las colas y obtiene sus mensajes"""
    queues = list_queues()
    for queue_url in queues:
        fetch_messages_from_queue(queue_url)

def fetch_monitor_messages(max_messages=10, wait_time=5):
    """Obtiene mensajes específicamente de la cola de monitoreo"""
    # URL de la cola de monitoreo
    monitor_queue_url = 'https://sqs.us-east-1.amazonaws.com/381492023522/mentaqueue-monitor'
    return fetch_messages_from_queue(monitor_queue_url, max_messages=max_messages, wait_time=wait_time)

def get_sns_client():
    """Inicializa el cliente de SNS usando las credenciales configuradas"""
    params = {'region_name': settings.AWS_REGION}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        params.update({
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
        })
        if getattr(settings, 'AWS_SESSION_TOKEN', None):
            params['aws_session_token'] = settings.AWS_SESSION_TOKEN
    return boto3.client('sns', **params)

def list_topics():
    """Devuelve la lista de ARNs de los topics SNS"""
    client = get_sns_client()
    response = client.list_topics()
    topics = response.get('Topics', [])
    return [t['TopicArn'] for t in topics]

def list_subscriptions_for_topic(topic_arn):
    """Devuelve la lista de suscripciones de SNS para un topic"""
    client = get_sns_client()
    subs = []
    paginator = client.get_paginator('list_subscriptions_by_topic')
    for page in paginator.paginate(TopicArn=topic_arn):
        subs.extend(page.get('Subscriptions', []))
    return subs

def get_queue_url_from_arn(queue_arn):
    """Dado un ARN de cola SQS, devuelve su URL si existe"""
    sqs = get_sqs_client()
    queue_name = queue_arn.split(':')[-1]
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        return response.get('QueueUrl')
    except sqs.exceptions.QueueDoesNotExist:
        return None

def fetch_messages_by_topic(topic_arn, max_messages=10, wait_time=1):
    """Recorre las colas suscritas a un topic SNS y guarda sus mensajes"""
    messages = []
    subs = list_subscriptions_for_topic(topic_arn)
    for sub in subs:
        if sub.get('Protocol') == 'sqs' and sub.get('Endpoint'):
            queue_url = get_queue_url_from_arn(sub['Endpoint'])
            if queue_url:
                msgs = fetch_messages_from_queue(queue_url, max_messages=max_messages, wait_time=wait_time)
                messages.extend(msgs)
    return messages 