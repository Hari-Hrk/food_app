from . import models

def RequestObjectMiddleware(get_response):
    def middleware(request):
        # code excute for each request before
        models.request_object = request
        response = get_response(request)

        return response
    return middleware