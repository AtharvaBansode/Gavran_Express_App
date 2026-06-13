from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login
from django.contrib import messages
from.models import Product

from .models import Cart, CartItem,Order,OrderItem,Feedback
from django.db.models import Sum, F
from django.contrib.auth.decorators import login_required
import razorpay
from django.conf import settings 

import hmac
import hashlib
import json
import threading

from django.http import JsonResponse,HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response





def login_view(request):
    if request.method=="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_staff:
                return redirect('/admin/')
            else:
                return redirect('products')

        else:
            messages.error(request, "Invalid username or password")
            
       

    return render(request, 'store/login.html')
    
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        first_name = request.POST.get("first_name")

        if password1 != password2:
            messages.error(request,"Passwords do not match")
            return redirect("login")
        
        if User.objects.filter(username=username).exists():
            messages.error(request,"Username already exist")
            return redirect("login")
        
        user = User.objects.create_user(
            username=username,
            password=password1,
            first_name=first_name
        )
        user.save()

        messages.success(request,"Account created successfully!")
        return redirect("login")
    return redirect("login")



def products(request):
    products = Product.objects.all()
    quantities = [1, 2, 5, 10, 30]
    
    total_price = None
    selected_quantity = None
    selected_product_id = None

    

    if request.method=="POST":
        selected_product_id = request.POST.get('product_id')
        selected_quantity = request.POST.get('quantity')

        if selected_product_id and selected_quantity:
            product = Product.objects.get(id=selected_product_id)
            total_price = product.price * int(selected_quantity)
        
    context={
        'products': products,
        'quantities': quantities,
        'total_price': total_price,
        'selected_quantity': selected_quantity,
        'selected_product_id': selected_product_id,
        
    }

    return render(request, "store/products.html", context)

@login_required
def checkout_view(request):
    cart = Cart.objects.filter(user=request.user).first()

    if not cart:
        return redirect("cart")
    
    cart_items = CartItem.objects.filter(cart=cart)

    
    if not cart_items.exists():
        return redirect("cart")
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    total_weight =  sum( item.quantity for item in cart_items)
    
    # Delivery Charge
    if total_weight <=5:
        delivery_charge = 20
    elif total_weight <=10:
        delivery_charge = 30
    elif total_weight <=20:
        delivery_charge = 50
    else:
        delivery_charge = 70
    
    final_amount = total + delivery_charge

    # Razorpay Payment
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    payment = client.order.create({
        "amount":int(final_amount * 100),
        "currency":"INR",
        "payment_capture":1
    })

    return render(request, 'store/checkout.html', {
        "cart_items": cart_items,
        "total": total,
        "delivery_charge": delivery_charge,
        "final_amount": final_amount,
        "total_weight": total_weight,
        "payment": payment,
        "key_id": settings.RAZORPAY_KEY_ID
        
    })

    

  

@login_required    
def add_to_cart(request):
    if request.method=="POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity"))

        product = Product.objects.get(id=product_id)

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if not item_created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity

        cart_item.save()
    return redirect('products')

@login_required
def cart_view(request):
    cart = Cart.objects.filter(user=request.user).first()
    cart_items = CartItem.objects.filter(cart=cart) if cart else[]
    
    grand_total =  sum(item.product.price * item.quantity for item in cart_items)



    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "grand_total": grand_total 
    })

def increase_quantity(request,cart_id):
    cart_item = CartItem.objects.get(id=cart_id,cart__user=request.user)
    cart_item.quantity +=1
    cart_item.save()
    return redirect("cart")

def decrease_quantity(request,cart_id):
    cart_item = CartItem.objects.get(id=cart_id,cart__user=request.user)

    if cart_item.quantity > 1:
       cart_item.quantity -=1
       cart_item.save()
    else:
        cart_item.delete()

    return redirect("cart")

def remove_from_cart(request, cart_id):
    cart_item = CartItem.objects.get(id=cart_id,cart__user=request.user)
    cart_item.delete()
    return redirect("cart")

def update_quantity(request, cart_id):
    if request.method == "POST":
        cart_item = CartItem.objects.get(id=cart_id,cart__user=request.user)
        new_quantity = int(request.POST.get("quantity"))

        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()

            return redirect("cart")


@login_required
def order_success(request, order_id):
    order = Order.objects.get(id=order_id)
    order_items = order.items.all()

    total = sum(item.price * item.quantity for item in order_items)
    total_weight = sum(item.quantity for item in order_items)
    
    # Delivery logic
    if total_weight <= 5:
        delivery_charge = 20
    elif total_weight <= 10:
        delivery_charge = 30
    elif total_weight <= 20:
        delivery_charge = 50
    else:
        delivery_charge = 70
    
    final_amount = total + delivery_charge
    
    context = {
        "order":order,
        "order_items":order_items,
        "total": total,
        "delivery_charge": delivery_charge,
        "final_amount": final_amount,
        "total_weight": total_weight
    }


    return render(request, "store/order_success.html", context)


@login_required
def place_order(request):
    if request.method== "POST":
        
        cart = Cart.objects.filter(user=request.user).first()

        if not cart:
            return redirect("cart")
    
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return redirect("cart")
        
        # Get form data
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        address = request.POST.get("address")
        city = request.POST.get("city")
        pincode = request.POST.get("pincode")
        payment_method = request.POST.get("payment_method")  

        total_amount = 0
    
        for item in cart_items:
         total_amount += item.product.price * item.quantity
        
       
         
        # Create Order(pending initially)
        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            city=city,
            pincode=pincode,
            total_amount=total_amount,
            payment_method=payment_method,
            status="Pending",
            payment_status="Pending"
        )

        # Create Order Items

        order_items = [
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            for item in cart_items
        ]
        OrderItem.objects.bulk_create(order_items)

        cart_items.delete()

        # Email

        def send_emails():
            send_order_email_to_customer(order)
            send_order_email_to_admin(order)

        threading.Thread(target=send_emails).start()

        # Payment Flow

        # COD Flow
        if payment_method == "COD":
            order.status = "Confirmed"
            order.payment_status = "Pending"
            order.save()
            return redirect("order_success", order_id=order.id)
        

        # ONLINE Payment Flow

        elif payment_method == "Online":
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            payment = client.order.create({
                "amount": int(total_amount * 100),
                "currency": "INR"
            })

            # Save Razorpay order id
            order.razorpay_order_id = payment["id"]
            order.save()

            return render(request, "store/payment.html", {
                "order": order,
                "payment": payment,
                "key_id": settings.RAZORPAY_KEY_ID
            })


      
  

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('created_at')

    return render(request, "store/order_history.html", {
        "orders":orders
    })


def track_order(request):
    order = None
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            order = None
    return render(request, "store/track_order.html", {"order":order})



def verify_payment(request):
    if request.method != "POST":
        return JsonResponse({"status": "invalid_request"})
    
    try:
        data = json.loads(request.body)

        order_id = data.get('razorpay_order_id')
        payment_id = data.get('razorpay_payment_id')
        signature = data.get('razorpay_signature')


        if not order_id or not payment_id or not signature:
            return JsonResponse({"status": "invalid_data"})

        generated_signature = hmac.new(
            bytes(settings.RAZORPAY_KEY_SECRET,'utf-8'),
            bytes(order_id + "|" + payment_id, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != signature:
            return JsonResponse({"status": "failure"})
        

        try:
            order = Order.objects.get(razorpay_order_id=order_id)
        
        except Order.DoesNotExist:
            return JsonResponse({"status": "order_not_found"})
            

        order.razorpay_payment_id = payment_id
        order.payment_status = "Paid"
        order.status = "Confirmed"
        order.save()

        def send_confirmation_email():
            send_mail(
                "Gavran Express - Order Confirmed",
                f"""
Hello {order.full_name},

Your order has been successfully placed.

Order ID: {order.id}
Amount: ₹{order.total_amount}
Payment Status: Paid

Thank you for shopping with Gavran Express!
""",
                settings.EMAIL_HOST_USER,
                [order.email],
            )

        threading.Thread(target=send_confirmation_email).start()
        return JsonResponse({"status": "success"})
            
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
   




# Success Page
def success(request):
    return render(request, "success.html")



# Failure Page
def failure(request):
    return render (request, "failure.html")

@login_required
def feedback_view(request, order_id):
    order = Order.objects.get(id=order_id)

    # only allowed if delivered
    if order.status !="Delivered":
        return HttpResponse("Feedback allowed only after delivery")
    
    if hasattr(order, 'feedback'):
        return HttpResponse("Feedback already submitted")
    
    if request.method == "POST":
        rating = request.POST.get("rating")
        quality = request.POST.get("quality")
        delivery = request.POST.get("delivery")
        packaging = request.POST.get("packaging")
        comment = request.POST.get("comment")

        Feedback.objects.create(
            order=order,
            rating=rating,
            product_quality=quality,
            delivery_experience=delivery,
            packaging=packaging,
            comment=comment
        )

        return redirect("order_success", order_id=order_id)
    return render(request, "store/feedback.html", {"order":order})


