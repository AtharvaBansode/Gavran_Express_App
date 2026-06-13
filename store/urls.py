from django.urls import path
from.views import login_view,products
from . import views

urlpatterns = [
    path('', views.products, name='home'),
    path('login/', views.login_view, name="login"),
    path('register/', views.register_view, name='register'),
    path('products/', views.products, name="products"),
    path('add-to-cart/', views.add_to_cart, name="add_to_cart"),
    path('cart/', views.cart_view, name='cart'),
    path('cart/increase/<int:cart_id>/', views.increase_quantity, name="increase_quantity"),
    path('cart/decrease/<int:cart_id>/', views.decrease_quantity, name="decrease_quantity"),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name="remove_from_cart"),
    path('cart/update/<int:cart_id>/', views.update_quantity, name="update_quantity"),
    path('checkout/', views.checkout_view, name="checkout"),
    path('order-success/<int:order_id>/', views.order_success, name="order_success"),
    path('place-order/', views.place_order, name="place_order"),
    path('my-orders/', views.order_history, name="order_history"),
    path('track-order/', views.track_order, name='track_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('success/', views.success, name='success'),
    path('failure/', views.failure, name='failure'),
    path('feedback/<int:order_id>/', views.feedback_view, name='feedback'),


]  





  
