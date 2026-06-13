from rest_framework import serializers
from.models import Cart,Product,CartItem,Order,OrderItem

class ProductMiniSerializer(serializers.ModelSerializer):
    isAvailable = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product 
        fields = ['id','name','price','unit','image','isAvailable', 'stock']

    def get_isAvailable(self, obj):
        return obj.stock != "OUT_OF_STOCK"
    

    def get_stock(self, obj):   
        return obj.stock
    
    def get_image(self,obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

class CartSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer()

    class Meta:
        model = CartItem
        fields = ['id','product','quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name')
    

    class Meta:
        model = OrderItem
        fields = ['product_name','quantity','price']

    
    def get_price(self, obj):
        return str(obj.price) 


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'full_name',
            'total_amount',
            'status',
            'payment_status',
            'created_at',
            'items'
        ]

