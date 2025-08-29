from functools import wraps
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from functools import wraps
from django.views.decorators.csrf import csrf_exempt

def bypass_csrf(view_func):
    """Completely bypass CSRF protection for a view."""
    @csrf_exempt
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    return wrapped_view

def bypass_csrf_for_api(view_class):
    """Class decorator to bypass CSRF for all methods in a class-based view."""
    orig_dispatch = view_class.dispatch
    
    @wraps(orig_dispatch)
    def dispatch(self, request, *args, **kwargs):
        return orig_dispatch(self, request, *args, **kwargs)
    
    dispatch.csrf_exempt = True
    view_class.dispatch = dispatch
    return view_class
