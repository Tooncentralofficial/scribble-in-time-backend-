import logging
from django.urls import path, re_path
from django.views.generic import RedirectView
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.views import View
from . import api_views

logger = logging.getLogger(__name__)

class DebugView(View):
    def dispatch(self, request, *args, **kwargs):
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        if request.method == 'POST':
            logger.info(f"Request POST data: {request.POST.dict()}")
            logger.info(f"Request body: {request.body}")
        
        response = super().dispatch(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        return response
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'success',
            'message': 'GET request received',
            'path': request.path,
            'method': request.method,
            'headers': dict(request.headers)
        })
    
    def post(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'success',
            'message': 'POST request received',
            'path': request.path,
            'method': request.method,
            'data': request.POST.dict() or {},
            'body': request.body.decode('utf-8') if request.body else None,
            'headers': dict(request.headers)
        })
    
    def options(self, request, *args, **kwargs):
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
        return response

# Debug endpoint to test URL routing
debug_view = DebugView.as_view()

urlpatterns = [
    # Debug endpoint
    re_path(r'^debug/?$', debug_view, name='debug-view'),
    re_path(r'^debug/(?P<path>.+)/?$', debug_view, name='debug-view-catchall'),
    
    # Root endpoint
    re_path(r'^$', api_views.ChatAPIHome.as_view(), name='chat-api-home'),
    
    # Message sending endpoint - handles with or without trailing slash and newlines
    re_path(r'^messages/send[/\s]*$', api_views.SendMessageView.as_view(), name='send-message'),
    
    # Get messages endpoint
    re_path(r'^messages/conversation/(?P<user_id>[^/]+)/?$', 
           api_views.GetMessagesView.as_view(), 
           name='get-messages'),
    
    # Admin message endpoint
    re_path(r'^admin/send-message/?$', 
           api_views.AdminMessageAPI.as_view(), 
           name='admin-send-message'),
    
    # Document upload endpoint
    path('documents/upload/', api_views.DocumentUploadView.as_view(), name='upload_document'),
    
    # Log and redirect any malformed URLs
    re_path(r'^messages/send/.*$', 
           lambda request: JsonResponse(
               {'error': 'Invalid URL', 'suggested_url': '/api/chat/messages/send/', 'original_path': request.path},
               status=400
           )),
           
    # Catch-all for any other patterns
    re_path(r'^.*$', 
           lambda request: JsonResponse(
               {'error': 'Not found', 'path': request.path},
               status=404
           )),
]
