from django.urls import path
from . import views

app_name = 'ai_chat'

urlpatterns = [
    path('chat/message/', views.chat_message, name='message'),
]
