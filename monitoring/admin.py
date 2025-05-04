from django.contrib import admin
from .models import Message

# Register your models here.

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'queue_name', 'state', 'received_at')
    search_fields = ('message_id', 'queue_name', 'topic_arn')
    list_filter = ('state',)
