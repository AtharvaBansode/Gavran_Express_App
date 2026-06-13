from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group

from rest_framework.permissions import IsAuthenticated,BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.conf import settings
import razorpay



from.models import Product,Cart,CartItem,Order,OrderItem,Feedback
from.serializers import CartSerializer,OrderSerializer
from.utils.email_utils import send_order_email_to_customer,send_order_email_to_admin
from.utils.delivery_utils import calculate_delivery_charge

# RC
class IsAdminUserGroup(BasePermission):
    def has_permission(self,request,view):
     return request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()
    
def is_admin(user):
    return user.groups.filter(name='Admin').exists()

# RU

@api_view(['POST'])
def register_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists"},status=400)
    
    user = User.objects.create_user(username=username,password=password)

       # AUTO ASSIGN CUSTOMER ROLE
    customer_group, _ = Group.objects.get_or_create(name='Customer')
    user.groups.add(customer_group)

    return Response({"message": "User created successfully",
                      "user_id": user.id
                    }, status=201)

# LC API

@api_view(['POST'])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    print("USERNAME:", username)
    print("PASSWORD:", password)

    user = authenticate(username=username,password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
    return Response({"success":False, "message": "Invalid Credentials"},status=400)


# Product
@api_view(['GET'])
def product_api(request):
    products = Product.objects.all()

    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "description": p.description,
            "image": request.build_absolute_uri(p.image.url) if p.image else ""
        })

    return Response(data)
    
# GET cart(Auth)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):

    user = request.user
    print("GET CART USER:", user)

 

    cart, created = Cart.objects.get_or_create(user=user)

    items = CartItem.objects.filter(cart=cart)

    if not cart:
        return Response([])


    items = CartItem.objects.filter(cart=cart)
    serializer = CartSerializer(
        items,
        many = True,
        context={'request': request}
    )
    return Response(serializer.data)

# add to cart
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):

    user = request.user

    
    product_id = request.data.get('product')
    quantity = int(request.data.get('quantity', 1))

    try:
        product = Product.objects.get(id=product_id)

          # STOCK CHECK
        if product.stock == "OUT_OF_STOCK":
           return Response(
            {"error": "Product is out of stock"},
            status=status.HTTP_400_BAD_REQUEST
          )
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=404)

    # get or create cart
    cart, _ = Cart.objects.get_or_create(user=user)

    
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,  
        
    )

    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity

    item.save()

  

    return Response({"message": "Added to cart"})
   

# Update cart
@api_view(['PUT'])
@permission_classes([IsAuthenticated])

def update_cart(request, pk):

    cart_item = get_object_or_404(CartItem,id=pk, cart__user=request.user)
    
    try:
     cart_item.quantity = int( request.data['quantity'])
     cart_item.save()
    except:
        return Response({"error": "Invalid quantity"}, status=400)

    return Response({"message":"Updated"})

# Delete Item
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])


def delete_cart(request, pk):

    cart_item = get_object_or_404(CartItem,id=pk,cart__user=request.user)
    cart_item.delete()

    return Response({"message":"Deleted"},status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])

def place_order(request):

    user = request.user
    data = request.data



  # get cart items
    cart_items = CartItem.objects.filter(cart__user=user)
    

    print("CART ITEMS COUNT:", cart_items.count())

    if not cart_items.exists():
       return Response({"error": "Cart is empty"},status=400)

   # PT
    total_amount = sum(
        item.product.price * item.quantity for item in cart_items
    )

    # TQ
    total_kg = sum(item.quantity for item in cart_items)

    # TFD
    distance_km = 5

    # DC
    delivery_data = calculate_delivery_charge(
        total_kg,
        distance_km
    )

    delivery_charge = delivery_data["charge"]
    vehicle = delivery_data["vehicle"]

    # FT
    grand_total = total_amount + delivery_charge
    

    # Create order
    order = Order.objects.create(
         user=user,
         full_name=data.get('full_name', ''),
         phone=data.get('phone', ''),
         email=data.get('email', ''),
         address=data.get('address', ''),
         city=data.get('city', ''),
         pincode=data.get('pincode', ''),
         total_amount=grand_total,
         delivery_charge=delivery_charge,
         vehicle=vehicle,
         payment_method=data.get('payment_method', 'COD'),
       )

    # Create OI
    for item in cart_items:
            OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
         )

    # Clear cart
    cart_items.delete()

    send_order_email_to_customer(order)
    send_order_email_to_admin(order)
    
    return Response({
    "message": "Order placed successfully",
    "order_id": order.id,
    "product_total": total_amount,
    "delivery_charge": delivery_charge,
    "vehicle": vehicle,
    "grand_total": grand_total
}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_razorpay_order(request):
    try:
        amount = int(request.data.get("amount"))

        

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

        payment = client.order.create({
            "amount": amount * 100,
            "currency": "INR",
            "payment_capture":1
        })

        return Response({
            "success":True,
            "order_id": payment["id"],
            "amount": amount,
            "key": settings.RAZORPAY_KEY_ID
        })

    except Exception as e:
        return Response({
            "success":False,
            "error" :str(e)
        },status=500)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('created_at')
    serializer = OrderSerializer(orders,many=True)

    return Response(serializer.data)

# Tracking
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return Response({
        "order_id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "created_at": order.created_at
    })

# Feedback
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request):
    order_id = request.data.get("order_id")
    order = get_object_or_404(Order, id=order_id, user=request.user)

    Feedback.objects.create(
        order=order,
        rating=(request.data.get("rating",0)),
        product_quality = request.data.get("product_quality"),
        delivery_experience = request.data.get("delivery_experience"),
        packaging = request.data.get("packaging"),
        comment = request.data.get("comment"),
    )

    return Response({"message": "Feedback Submitted"})