from django.shortcuts import render
from vendor.models import Vendor
from django.shortcuts import get_object_or_404
from menu.models import Category,FoodItem
from django.db.models import Prefetch
from django.http import HttpResponse,JsonResponse
from . models import Cart
from marketplace.context_processors import get_cart_counter,get_cart_amount
from django.contrib.auth.decorators import login_required

# Create your views here.
def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True,user__is_active=True)
    vendor_count = vendors.count()
    context = {
        'vendors':vendors,
        'vendor_count' : vendor_count
    }
    return render(request,'marketplace/listings.html',context)

def vendor_detail(request,vendor_slug):
    vendor = get_object_or_404(Vendor,vendor_slug=vendor_slug)
    # get categories
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset=FoodItem.objects.filter(is_avalible=True)
        )
    )

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None

    context = {
        'vendor':vendor,
        'categories' : categories,
        'cart_items':cart_items
    }
    return render(request,'marketplace/vendor_detail.html',context)


def add_to_cart(request,food_id = None):
    if request.user.is_authenticated:
        if request.is_ajax():
            # check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # check if the user has alredy added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user,fooditem=fooditem)
                    # inc the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse({'status':'success','message':'Increased the cart quantity','cart_counter':get_cart_counter(request),'qty':chkCart.quantity,'cart_amount':get_cart_amount(request)})
                except:
                    chkCart = Cart.objects.create(user=request.user,fooditem=fooditem,quantity=1)
                    return JsonResponse({'status':'success','message':'Added the food to the cart','cart_counter':get_cart_counter(request),'qty':chkCart.quantity,'cart_amount':get_cart_amount(request)})
            except:
                return JsonResponse({'status':'failed','message':'This food does not exists'})
        else:
            return JsonResponse({'status':'failed','message':'Invalid request'})
    else:
        return JsonResponse({'status':'login_required','message':'Please login in continue'})
    
def decrease_cart(request,food_id = None):
    if request.user.is_authenticated:
        if request.is_ajax():
            # check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # check if the user has alredy added that food to the cart
                try:
                    chkCart = Cart.objects.get(user=request.user,fooditem=fooditem)
                    if chkCart.quantity > 1:
                        # decrease the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity=0
                    return JsonResponse({'status':'success','cart_counter':get_cart_counter(request),'qty':chkCart.quantity,'cart_amount':get_cart_amount(request)})
                except:
                    return JsonResponse({'status':'failed','message':'You do not have tis item in your cart'})
            except:
                return JsonResponse({'status':'failed','message':'This food does not exists'})
        else:
            return JsonResponse({'status':'failed','message':'Invalid request'})
    else:
        return JsonResponse({'status':'login_required','message':'Please login in continue'})

@login_required(login_url='login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        "cart_items":cart_items
    }
    return render(request,'marketplace/cart.html',context)

@login_required(login_url='login')
def delete_cart(request,cart_id):
    if request.user.is_authenticated:
        if request.is_ajax():
            try:
                # check if the cart item exists
                cart_items = Cart.objects.get(user=request.user,id=cart_id)
                if cart_items:
                    cart_items.delete()
                    return JsonResponse({'status':'success',"message":'Cart item has been deleted!','cart_counter':get_cart_counter(request),'cart_amount':get_cart_amount(request)})
            except:
                return JsonResponse({'status':'failed','message':'Cart item does not exists'})
        else:
            return JsonResponse({"status":'failed','message':'Inavalid request'})
