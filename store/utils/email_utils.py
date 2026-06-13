from django.core.mail import send_mail
from django.conf import settings

def send_order_email_to_customer(order):
    subject = "Order Confirmed - Gavran Store"
    message = f"""
    Hi {order.full_name},

    Your order has been placed successfully!

    Order ID: {order.id}
    Total: ₹{order.total_amount}

    Thank you for shopping with us.
    """

    send_mail(
        subject,
        message,
        "gavranexpress@gmail.com",
        [order.email],
        fail_silently=False,
    )

def send_order_email_to_admin(order):
    subject = "New Order Received"
    
    message = f"""
    New Order Alert

    Order ID: {order.id}
    Customer: {order.full_name}
    Phone: {order.phone}
    Email: {order.email}
    Address: {order.address}
    Total: ₹{order.total_amount}
    """

    send_mail(
        subject,
        message,
        "gavranexpress@gmail.com",
        ["atharvabansode2001@gmail.com"],
        fail_silently=False,
    )