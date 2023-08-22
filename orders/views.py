from django.shortcuts import render,redirect
from marketplace.models import Cart,Tax
from marketplace.context_processors import get_cart_amount
from .forms import OrderForm
from .models import Order,Payment,OrderedFood
import json
from .utils import generate_order_number,order_total_by_vendor
from django.http import HttpResponse,JsonResponse
from accounts.utils import send_notification
from django.contrib.auth.decorators import login_required
from menu.models import FoodItem
from django.contrib.sites.shortcuts import get_current_site

# Create your views here.
@login_required(login_url='login')
def place_order(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')
    
    vendors_ids = []
    for i in cart_items:
        if i.fooditem.vendor.id not in vendors_ids:
            vendors_ids.append(i.fooditem.vendor.id)

    # {"vendor_id":{"subtotal":{"tax_type":{"tax_percentag":"tax_amount"}}}}  ---> json format for tax data
    get_tax = Tax.objects.filter(is_active=True)
    subtotal = 0
    total_data = {}
    list1 = {}
    for i in cart_items:
        fooditem = FoodItem.objects.get(pk=i.fooditem.id,vendor_id__in=vendors_ids)
        id_of_vendors = fooditem.vendor.id
        if id_of_vendors in list1:
            subtotal = list1[id_of_vendors]
            subtotal += (fooditem.price * i.quantity)
            list1[id_of_vendors] = subtotal
        else:
            subtotal = (fooditem.price * i.quantity)
            list1[id_of_vendors] = subtotal
    
        # calculate tax data
        tax_dict = {}
        for i in get_tax:
            tax_type = i.tax_type
            tax_percentage = i.tax_percentage
            tax_amount = round((tax_percentage * subtotal)/100,2)
            tax_dict.update({tax_type: {str(tax_percentage): str(tax_amount)}})
        # construct total data
        total_data.update({fooditem.vendor.id: {str(subtotal):str(tax_dict)}})

        # op of total_data is ==> 7}, {7: {'6.00': "{'CGST': {'9.00': '0.54'}, 'SGST': {'7.00': '0.42'}}"}}
        # here 7is vendor ID & 6.00 is subtotal ,0.54 is 9% of CGST & 0.42 is 7% of SGST


    subtotal = get_cart_amount(request)['subtotal']
    total_tax = get_cart_amount(request)['tax']
    grand_total = get_cart_amount(request)['grand_total']
    tax_data = get_cart_amount(request)['tax_dict']

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order()
            order.first_name = form.cleaned_data['first_name']
            order.last_name = form.cleaned_data['last_name']
            order.phone_number = form.cleaned_data['phone_number']
            order.email = form.cleaned_data['email']
            order.address = form.cleaned_data['address']
            order.country = form.cleaned_data['country']
            order.state = form.cleaned_data['state']
            order.city = form.cleaned_data['city']
            order.pincode = form.cleaned_data['pincode']
            order.user = request.user
            order.total = grand_total
            order.tax_data = json.dumps(tax_data)
            order.total_data = json.dumps(total_data)
            order.total_tax = total_tax
            order.payment_method = request.POST['payment_method']
            order.save() # here order id is created
            order.order_number = generate_order_number(order.id)
            order.vendors.add(*vendors_ids)
            order.save()
            context = {
                'order':order,
                'cart_items' : cart_items
            }
            return render(request,'orders/place_order.html',context)
        else:
            print(form.errors)

    return render(request,'orders/place_order.html')

@login_required(login_url='login')
def payments(request):
    # CHECK IF THE REQUEST IS AJAX OR NOT
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "POST":
        # STORE THE PAYMENT DETAILS IN THE PAYMENT MODEL
            # here user send status = verified change as status = completed
        status_mapping = { 'VERIFIED': 'COMPLETED'  }
        received_status = request.POST.get('status')
        backend_status = status_mapping.get(received_status, 'UNKNOWN')  # Use 'UNKNOWN' as a default
        order_number = request.POST.get('order_number')
        transaction_id = request.POST.get('transaction_id')
        status = backend_status
        payment_method = request.POST.get('payment_method')
        
        order = Order.objects.get(user = request.user,order_number = order_number)
        payment = Payment(
            user = request.user,
            transaction_id = transaction_id,
            payment_method = payment_method,
            amount = order.total,
            status  = status
        )
        payment.save()

        #UPDATE THE ORDER MODEL
        order.payment = payment
        order.is_ordered = True
        order.save()

        # MOVE THE CART ITEMS TO ORDERED FOOD MODEL
        cart_items = Cart.objects.filter(user = request.user)
        for item in cart_items:
            ordered_food = OrderedFood()
            ordered_food.order = order
            ordered_food.payment = payment
            ordered_food.user = request.user
            ordered_food.fooditem = item.fooditem
            ordered_food.quantity = item.quantity
            ordered_food.price = item.fooditem.price
            ordered_food.amount = item.fooditem.price * item.quantity
            ordered_food.save()

        # SEND ORDER CONFIRMATION EMAIL TO THE CUSTOMER

        mail_subject = 'Thank you for ordering with us'
        mail_template = 'orders/order_confirmation_email.html'
        ordered_food = OrderedFood.objects.filter(order=order)
        customer_subtotal = 0
        for item in ordered_food:
            customer_subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)
        context = {
            'user':request.user,
            'order':order,
            'to_email':order.email,
            'ordered_food':ordered_food,
            'domain':get_current_site(request),
            'customer_subtotal' : customer_subtotal,
            'tax_data':tax_data
        }
        send_notification(mail_subject,mail_template,context)

        # SEND ORDER RECEIVED EMAIL TO THE VENDEOR
        mail_subject = 'You have recevied a new order'
        mail_template = 'orders/new_order_recevied.html'
        to_emails = []
        for i in cart_items:
            if i.fooditem.vendor.user.email not in to_emails:
                to_emails.append(i.fooditem.vendor.user.email)

            # vendor specific fooditem
            ordered_food_to_vendor = OrderedFood.objects.filter(order=order,fooditem__vendor = i.fooditem.vendor)

            context = {
                'order':order,
                'to_email':i.fooditem.vendor.user.email,
                'ordered_food_to_vendor' : ordered_food_to_vendor,
                'vendor_subtotal' : order_total_by_vendor(order,i.fooditem.vendor.id)['subtotal'],
                'tax_data': order_total_by_vendor(order,i.fooditem.vendor.id)['tax_dict'],
                'vendor_grand_total' : order_total_by_vendor(order,i.fooditem.vendor.id)['grand_total']
            }
            send_notification(mail_subject,mail_template,context)
    
        #CLEAR THE CART IF THE PAYMENT IS SUCCESSS
        #cart_items.delete()

        # RETURN BACK TO AJAX WITH THE STATUS SUCCESS OR FAILURE
        response = {
            'order_number' : order_number,
            'transaction_id' :  transaction_id
        }
        return JsonResponse(response)

    return HttpResponse('payemnts views')

# def order_complete(request):
#     order_number = request.GET.get('order_no')
#     transaction_id = request.GET.get('trans_id')
#     print('req',request.GET)
#     try:
#         order = Order.objects.get(order_number=order_number,payment__transaction_id = transaction_id,is_ordered = True)
#         ordered_food = OrderedFood.objects.filter(order=order)
#         subtotal = 0
#         for item in ordered_food:
#             subtotal += (item.price * item.quantity)
#         tax_data = json.loads(order.tax_data)
#         #print('tax data --> ',tax_data)
#         context = {
#             'order':order,
#             'ordered_food':ordered_food,
#             'subtotal':subtotal,
#             'tax_data' : tax_data
#         }
#         print('context ---> ',context)
#         return render(request,'orders/order_complete.html',context)
#     except:
#         return redirect('home')


def order_complete(request):
    order_number = request.GET.get('order_no')
    transaction_id = request.GET.get('trans_id')
    
    try:
        order = Order.objects.get(order_number=order_number,payment__transaction_id = transaction_id,is_ordered = True)
        ordered_food = OrderedFood.objects.filter(order=order)
        
        subtotal = 0
        for item in ordered_food:
            subtotal += (item.price * item.quantity)
        tax_data = json.loads(order.tax_data)
        context = {
            'order' : order,
            'ordered_food' : ordered_food,
            'subtotal' : subtotal,
            'tax_data' : tax_data
        }

    except:
        return redirect('home')
    return render(request,'orders/order_complete.html',context)

