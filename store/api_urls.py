from django.urls import path
from.api_views import login_user,register_user, product_api,get_cart,add_to_cart,update_cart,delete_cart,place_order,my_orders,track_order,submit_feedback
from.import api_views

urlpatterns = [  
    path('login/',login_user),
    path('register/', register_user),
    path('products/', product_api, name='product_api'),

    path('cart/', get_cart),
    path('cart/add/', add_to_cart),
    path('cart/update/<int:pk>/',update_cart),
    path('cart/delete/<int:pk>/',delete_cart),

    path('checkout/', place_order),
    path('create-razorpay-order/', api_views.create_razorpay_order),
    path('my-orders/',my_orders),
    path('order/<int:order_id>/',track_order),
    path('feedback/', submit_feedback),
    
]