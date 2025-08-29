from django.http import JsonResponse
from django.views import View

class TestView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'success',
            'path': request.path,
            'method': request.method,
            'headers': dict(request.headers)
        })
    
    def post(self, request, *args, **kwargs):
        return JsonResponse({
            'status': 'success',
            'path': request.path,
            'method': request.method,
            'data': request.POST.dict() or {},
            'headers': dict(request.headers)
        })
