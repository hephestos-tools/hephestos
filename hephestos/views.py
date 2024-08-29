from django.http import HttpResponse


def default(request):
    return HttpResponse("This is the default endpoint")
