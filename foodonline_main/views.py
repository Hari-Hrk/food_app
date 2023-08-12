from django.shortcuts import render
from django.http import HttpResponse
from vendor.models import Vendor

def home(request):
    vendor = Vendor.objects.filter(is_approved=True,user__is_active=True)[:5]
    print('vendors are --> ',vendor)
    context = {
        'vendors':vendor
    }
    return render(request,"home.html",context)