from django.db import models

# Create your models here.

class Message(models.Model):
    message_id = models.CharField(max_length=255, unique=True)
    queue_name = models.CharField(max_length=255)
    topic_arn = models.CharField(max_length=512, blank=True, null=True)
    body = models.TextField()
    attributes = models.JSONField(blank=True, null=True)
    state = models.CharField(max_length=50, default='RECEIVED')
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.queue_name} - {self.message_id}'
