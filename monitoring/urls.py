from django.urls import path
from . import views

urlpatterns = [
    path('', views.queue_list, name='queue_list'),
    path('queues/<str:queue_name>/', views.message_list, name='message_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('topics/', views.topic_list, name='topic_list'),
    path('topics/<str:topic_arn>/', views.topic_message_list, name='topic_message_list'),
    path('update/', views.update_messages, name='update_messages'),
] 