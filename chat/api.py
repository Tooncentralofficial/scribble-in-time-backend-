from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

class AdminMessageAPI(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request, *args, **kwargs):
        """
        Send a message as admin to a specific user or conversation
        Required data: {
            "message": "Your admin message",
            "recipient_id": "user_123" or "conversation_456",
            "is_direct_message": true/false
        }
        """
        data = request.data
        message = data.get('message')
        recipient_id = data.get('recipient_id')
        is_direct = data.get('is_direct_message', True)
        
        if not all([message, recipient_id]):
            return Response(
                {"error": "Message and recipient_id are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determine the group name based on message type
        group_name = f"direct_message_{recipient_id}" if is_direct else f"chat_{recipient_id}"
        
        # Prepare the message to send
        message_data = {
            'type': 'chat.message',
            'message': message,
            'sender': 'admin',
            'is_admin': True,
            'recipient_id': recipient_id
        }
        
        # Send the message to the channel layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            message_data
        )
        
        return Response({"status": "Message sent"}, status=status.HTTP_200_OK)
