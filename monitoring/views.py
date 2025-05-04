from django.shortcuts import render, get_object_or_404, redirect
from .aws_service import list_queues, list_topics, fetch_all_messages, fetch_messages_by_topic
from .models import Message

# Vistas para colas SQS

def queue_list(request):
    """Lista las colas SQS y muestra el conteo de mensajes"""
    queues = list_queues()
    queue_names = [url.split('/')[-1] for url in queues]
    queue_info = []
    for url, name in zip(queues, queue_names):
        count = Message.objects.filter(queue_name=name).count()
        queue_info.append({'url': url, 'name': name, 'count': count})
    return render(request, 'monitoring/queue_list.html', {'queues': queue_info})


def message_list(request, queue_name):
    """Muestra los mensajes recibidos en la cola especificada"""
    messages = Message.objects.filter(queue_name=queue_name).order_by('-received_at')
    return render(request, 'monitoring/message_list.html', {'messages': messages, 'queue_name': queue_name})


def message_detail(request, pk):
    """Muestra detalle de un mensaje específico"""
    msg = get_object_or_404(Message, pk=pk)
    return render(request, 'monitoring/message_detail.html', {'message': msg})

# Vistas para topics SNS

def topic_list(request):
    """Lista los topics de SNS y muestra el conteo de mensajes"""
    # Actualiza la lista de mensajes antes de generar el reporte
    fetch_all_messages()
    topics = list_topics()
    topic_info = []
    for arn in topics:
        count = Message.objects.filter(topic_arn=arn).count()
        topic_info.append({'arn': arn, 'count': count})
    return render(request, 'monitoring/topic_list.html', {'topics': topic_info})


def topic_message_list(request, topic_arn):
    """Muestra los mensajes asociados a un topic específico"""
    # Actualiza los mensajes de las colas suscritas a este topic SNS
    fetch_messages_by_topic(topic_arn)
    messages = Message.objects.filter(topic_arn=topic_arn).order_by('-received_at')
    return render(request, 'monitoring/topic_message_list.html', {'messages': messages, 'topic_arn': topic_arn})

# Vista para actualizar mensajes desde AWS

def update_messages(request):
    """Ejecuta la recolección de mensajes desde AWS y redirige al dashboard"""
    fetch_all_messages()
    return redirect('queue_list')
