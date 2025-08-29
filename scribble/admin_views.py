from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.db.models import Count, Q, F
import json
from datetime import timedelta

from .models import Conversation, Message, Document
from .serializers import ConversationSerializer, MessageSerializer, DocumentSerializer


class AdminDashboardView(TemplateView):
    template_name = 'admin_dashboard/dashboard.html'
    
    @method_decorator(login_required)
    @method_decorator(staff_member_required)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the first 5 recent conversations
        recent_conversations = Conversation.objects.order_by('-updated_at')[:5]
        
        # Get message statistics
        total_messages = Message.objects.count()
        messages_today = Message.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        context.update({
            'page_title': 'Dashboard',
            'recent_conversations': recent_conversations,
            'total_messages': total_messages,
            'messages_today': messages_today,
            'active_tab': 'dashboard',
        })
        
        return context


class DashboardStatsView(generics.RetrieveAPIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        from django.db.models import Count, Q, F
        from django.utils import timezone
        from datetime import timedelta

        # Get conversation statistics
        total_conversations = Conversation.objects.count()
        active_conversations = Conversation.objects.filter(is_active=True).count()
        conversations_today = Conversation.objects.filter(
            created_at__date=timezone.now().date()
        ).count()

        # Get message statistics
        total_messages = Message.objects.count()
        messages_today = Message.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        ai_responses = Message.objects.filter(sender='ai').count()

        # Get recent conversations
        recent_conversations = Conversation.objects.order_by('-updated_at')[:5]
        
        # Calculate AI response rate
        ai_response_rate = (ai_responses / total_messages) * 100 if total_messages > 0 else 0

        data = {
            'conversations': {
                'total': total_conversations,
                'active': active_conversations,
                'today': conversations_today,
            },
            'messages': {
                'total': total_messages,
                'today': messages_today,
                'ai_responses': ai_responses,
                'ai_response_rate': round(ai_response_rate, 1)
            },
            'recent_conversations': ConversationSerializer(recent_conversations, many=True).data
        }

        return Response(data)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = Conversation.objects.all().order_by('-updated_at')
        
        # Apply filters
        search = self.request.query_params.get('search', '')
        status_filter = self.request.query_params.get('status', 'all')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(messages__content__icontains=search)
            ).distinct()
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'archived':
            queryset = queryset.filter(is_active=False)
        
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset


class ConversationDetailView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'


class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return Message.objects.filter(conversation_id=conversation_id).order_by('created_at')
    
    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = Conversation.objects.get(id=conversation_id)
        serializer.save(conversation=conversation, sender='admin')


class ToggleAIResponseView(generics.UpdateAPIView):
    queryset = Conversation.objects.all()
    permission_classes = [IsAdminUser]
    
    def patch(self, request, *args, **kwargs):
        conversation = self.get_object()
        enable = request.data.get('enable', not conversation.ai_enabled)
        conversation.ai_enabled = enable
        conversation.save()
        
        # Create a system message about the change
        Message.objects.create(
            conversation=conversation,
            sender='system',
            content=f'AI responses have been turned {"on" if enable else "off"} by an admin.'
        )
        
        return Response({
            'status': 'success',
            'ai_enabled': conversation.ai_enabled
        })


class DocumentListView(generics.ListCreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAdminUser]
    
    def perform_update(self, serializer):
        serializer.save()
    
    def perform_destroy(self, instance):
        # Delete the file from storage
        instance.file.delete()
        instance.delete()


class MarkMessagesAsReadView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    
    def patch(self, request, *args, **kwargs):
        conversation_id = kwargs.get('conversation_id')
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).update(is_read=True)
        
        return Response({'status': 'success'})


class AdminConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # Get all conversations with their messages
        return Conversation.objects.prefetch_related('messages').order_by('-updated_at')
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        
        # Mark user messages as read when admin views them
        if not request.query_params.get('no_read'):
            conversation.messages.filter(sender='user', is_read=False).update(is_read=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'Message content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the message
        message = Message.objects.create(
            conversation=conversation,
            content=content,
            sender='admin',
            is_read=False,
            sender_username=request.user.email if request.user.is_authenticated else 'Admin'
        )
        
        # Update conversation's updated_at
        conversation.save()
        
        # Notify WebSocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{conversation.id}',
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message.id),
                    'content': message.content,
                    'sender': message.sender,
                    'conversation': str(message.conversation.id),
                    'created_at': message.created_at.isoformat(),
                    'is_read': message.is_read,
                    'sender_name': message.sender_username or 'Admin'
                }
            }
        )
        
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class AdminMessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        # Get all messages across all conversations
        return Message.objects.select_related('conversation').order_by('-created_at')
    
    def get_serializer_context(self):
        return {'request': self.request}


class AdminSearchViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def list(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search in messages
        messages = Message.objects.filter(
            Q(content__icontains=query)
        ).select_related('conversation').order_by('-created_at')
        
        # Search in conversations (by user email)
        conversations = Conversation.objects.filter(
            Q(user__email__icontains=query)
        ).prefetch_related('messages').order_by('-updated_at')
        
        message_serializer = MessageSerializer(messages, many=True)
        conversation_serializer = ConversationSerializer(conversations, many=True)
        
        return Response({
            'messages': message_serializer.data,
            'conversations': conversation_serializer.data
        })
