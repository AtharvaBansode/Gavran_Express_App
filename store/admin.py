from django.contrib import admin
from .models import Product,Order,Feedback,Cart,CartItem,DeliverySetting
from django.utils import timezone


admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'full_name', 
        'phone', 
        'city',
        'pincode',
        'total_amount',
        'payment_status',
        'status', 
        'created_at')
    list_filter = ('status',)
    list_editable = ('status',)


    def save_model(self, request, obj, form, change):
        if obj.status == "Confirmed" and not obj.confirmed_at:
            obj.confirmed_at = timezone.now()
        elif obj.status == "Shipped" and not obj.shipped_at:
             obj.shipped_at = timezone.now()
        elif obj.status == "Out for Delivery" and not obj.out_for_delivery_at:
            obj.out_for_delivery_at = timezone.now()
        elif obj.status == "Delivered" and not obj.delivered_at:
            obj.delivered_at = timezone.now()

        super().save_model(request,obj,form,change)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('order','rating','product_quality','packaging','created_at')


@admin.register(DeliverySetting)
class DeliverySettingAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type','scooter_rate_per_km','rickshaw_rate_per_km','tempo_rate_per_km','minimum_delivery_charge','distance_km','delivery_charge',)
