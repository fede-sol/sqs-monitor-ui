import os
import sys
import django
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqs_monitor.settings')
django.setup()

from monitoring.aws_service import get_sqs_client, get_sns_client

def create_monitor_queue():
    # Obtener clientes
    sqs = get_sqs_client()
    sns = get_sns_client()
    
    # Nombre de la nueva cola para monitoreo
    queue_name = 'mentaqueue-monitor'
    
    try:
        # Crear la nueva cola SQS para monitoreo
        print(f"Creando nueva cola SQS: {queue_name}")
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'MessageRetentionPeriod': '86400',  # 1 día en segundos
                'VisibilityTimeout': '30',          # 30 segundos
                'ReceiveMessageWaitTimeSeconds': '20'  # Long polling
            }
        )
        
        queue_url = response.get('QueueUrl')
        print(f"Cola creada exitosamente: {queue_url}")
        
        # Obtener el ARN de la cola
        queue_attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attrs.get('Attributes', {}).get('QueueArn')
        print(f"ARN de la cola: {queue_arn}")
        
        # Lista de temas SNS a los que suscribir la cola
        topic_arns = [
            'arn:aws:sns:us-east-1:381492023522:appointments-topic',
            'arn:aws:sns:us-east-1:381492023522:userprofile-topic'
        ]
        
        # Suscribir la cola a cada tema SNS
        for topic_arn in topic_arns:
            # Crear una política que permita a SNS enviar mensajes a la cola
            statement = {
                "Sid": f"Allow-SNS-{topic_arn.split(':')[-1]}",
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "SQS:SendMessage",
                "Resource": queue_arn,
                "Condition": {
                    "ArnEquals": {
                        "aws:SourceArn": topic_arn
                    }
                }
            }
            
            # Establecer la política en la cola
            policy = {
                "Version": "2012-10-17",
                "Id": f"{queue_arn}/SQSDefaultPolicy",
                "Statement": [statement]
            }
            
            sqs.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={
                    'Policy': json.dumps(policy)
                }
            )
            print(f"Política establecida para tema {topic_arn}")
            
            # Suscribir la cola al tema SNS
            print(f"Suscribiendo cola al tema: {topic_arn}")
            sns.subscribe(
                TopicArn=topic_arn,
                Protocol='sqs',
                Endpoint=queue_arn
            )
            print(f"Cola suscrita al tema: {topic_arn}")
        
        print("\nProbar la nueva cola:")
        print(f"Publicando mensaje de prueba en el tema: {topic_arns[0]}")
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Mensaje de prueba de configuración'
        }
        
        response = sns.publish(
            TopicArn=topic_arns[0],
            Message=json.dumps(test_message),
            Subject='Prueba de configuración'
        )
        
        print(f"Mensaje publicado. MessageId: {response.get('MessageId')}")
        print("Esperando 5 segundos para que el mensaje se propague...")
        time.sleep(5)
        
        # Verificar si el mensaje llegó a la nueva cola
        receive_response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All'],
            AttributeNames=['All']
        )
        
        messages = receive_response.get('Messages', [])
        
        if messages:
            print(f"¡ÉXITO! Se recibieron {len(messages)} mensajes en la nueva cola")
            for msg in messages:
                # No eliminar el mensaje para que la aplicación pueda procesarlo
                print(f"  ID: {msg.get('MessageId')}")
                print(f"  Cuerpo: {msg.get('Body')[:100]}...")
        else:
            print("No se recibieron mensajes en la nueva cola")
        
        print("\nConfigura tu aplicación para usar la nueva cola:")
        print(f"URL de la nueva cola: {queue_url}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    create_monitor_queue() 