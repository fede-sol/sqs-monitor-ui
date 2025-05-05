import os
import sys
import django
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sqs_monitor.settings')
django.setup()

from monitoring.aws_service import get_sqs_client, get_sns_client

def fix_monitor_queue_policy():
    # Obtener clientes
    sqs = get_sqs_client()
    sns = get_sns_client()
    
    # URL de la cola de monitoreo
    queue_url = 'https://sqs.us-east-1.amazonaws.com/381492023522/mentaqueue-monitor'
    
    try:
        # Obtener el ARN de la cola
        queue_attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = queue_attrs.get('Attributes', {}).get('QueueArn')
        
        if not queue_arn:
            print("No se pudo obtener el ARN de la cola")
            return
        
        print(f"ARN de la cola: {queue_arn}")
        
        # Lista de temas SNS a incluir en la política
        topic_arns = [
            'arn:aws:sns:us-east-1:381492023522:appointments-topic',
            'arn:aws:sns:us-east-1:381492023522:userprofile-topic'
        ]
        
        # Crear declaraciones para ambos temas
        statements = []
        for topic_arn in topic_arns:
            statements.append({
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
            })
        
        # Crear la política completa
        policy = {
            "Version": "2012-10-17",
            "Id": f"{queue_arn}/SQSDefaultPolicy",
            "Statement": statements
        }
        
        # Actualizar la política de la cola
        print("Actualizando política de la cola...")
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                'Policy': json.dumps(policy)
            }
        )
        print("Política actualizada exitosamente")
        
        # Verificar la nueva política
        updated_policy = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['Policy']
        ).get('Attributes', {}).get('Policy', 'No hay política')
        
        print(f"Nueva política: {updated_policy}")
        
        # Publicar mensajes de prueba en ambos temas
        for topic_arn in topic_arns:
            print(f"\nPublicando mensaje en: {topic_arn}")
            test_message = {
                'test': True,
                'timestamp': time.time(),
                'source': f'test_{topic_arn.split(":")[-1]}'
            }
            
            response = sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(test_message),
                Subject=f'Prueba {topic_arn.split(":")[-1]}'
            )
            print(f"Mensaje publicado. MessageId: {response.get('MessageId')}")
        
        # Esperar a que los mensajes lleguen
        print("\nEsperando 10 segundos para que los mensajes se propaguen...")
        time.sleep(10)
        
        # Verificar si los mensajes llegaron
        receive_response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,
            MessageAttributeNames=['All'],
            AttributeNames=['All']
        )
        
        messages = receive_response.get('Messages', [])
        
        if messages:
            print(f"\n¡ÉXITO! Se recibieron {len(messages)} mensajes en la cola")
            for i, msg in enumerate(messages):
                print(f"\nMensaje {i+1}:")
                print(f"  ID: {msg.get('MessageId')}")
                body = msg.get('Body', '{}')
                
                # Intentar analizar el cuerpo JSON si viene de SNS
                try:
                    body_json = json.loads(body)
                    print(f"  Tema SNS: {body_json.get('TopicArn', 'N/A')}")
                    print(f"  Asunto: {body_json.get('Subject', 'N/A')}")
                except:
                    pass
        else:
            print("\nNo se recibieron mensajes en la cola")
        
        print("\nAhora debes modificar tu aplicación para usar esta nueva cola:")
        print(f"URL de la cola: {queue_url}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    fix_monitor_queue_policy() 