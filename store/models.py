from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()

    short_description_en = models.CharField(max_length=120,blank=True,null=True)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    unit = models.CharField(max_length=20, default='per kg')
    image = models.ImageField(upload_to='products/')

    # Stock field with dropdown options
    STOCK_CHOICES = [
        ('IN_STOCK', 'In Stock'),
        ('LOW_STOCK', 'Low Stock'),
        ('OUT_OF_STOCK', 'Out of  Stock'),
    ]
    stock = models.CharField(max_length=20, choices=STOCK_CHOICES, default='IN_STOCK')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def price_with_unit(self):
        return f"{self.price} Rs {self.unit}"
    

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Cart"
    
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


    class Meta:
        unique_together = ('cart', 'product') 

   
    @property
    def total_price(self):
        return self.product.price * self.quantity

    
    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    


class Order(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    PAYMENT_CHOICES = (
        ("COD", "Cash On Delivery"),
        ("ONLINE", "Razorpay"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(default="Not Provided")
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, default= "COD")

    payment_status = models.CharField(max_length=20, default="Pending")

    razorpay_order_id = models.CharField(max_length=100, blank=True,null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    delivery_charge = models.FloatField(default=0)

    vehicle = models.CharField(max_length=50,default="Scooter")


    

    created_at = models.DateTimeField(auto_now_add=True)

    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        if self.user:
          return f"Order {self.id} - {self.user.username}"
        return f"Order {self.id} - Guest"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10,decimal_places=2)

    @property
    def total_price(self):
        return self.price * self.quantity
    
    def __str__(self):
        return self.product.name


class Feedback(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)

    rating = models.IntegerField(default=5)
    product_quality = models.CharField(max_length=50)
    delivery_experience = models.CharField(max_length=50)
    packaging = models.CharField(max_length=50)

    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Order {self.order.id}"
    
class DeliverySetting(models.Model):
    scooter_rate_per_km = models.FloatField(default=5)
    rickshaw_rate_per_km = models.FloatField(default=8)
    tempo_rate_per_km = models.FloatField(default=12)

    scooter_weight_limit = models.IntegerField(default=25)
    rickshaw_weight_limit = models.IntegerField(default=100)

    minimum_delivery_charge = models.FloatField(default=25)

    distance_km = models.FloatField(default=0)
    delivery_charge = models.FloatField(default=0)
    vehicle_type = models.CharField(max_length=50,default="Scooter")

    def __str__(self):
        return "Delivery Settings" 
    