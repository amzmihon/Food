from django.contrib import admin
from .models import Member, MealPrice, MealRecord, Payment


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['serial_number']


@admin.register(MealPrice)
class MealPriceAdmin(admin.ModelAdmin):
    list_display = ['date', 'price_per_meal', 'created_at']
    list_filter = ['date']
    ordering = ['-date']


@admin.register(MealRecord)
class MealRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'date', 'ate_meal', 'meal_count']
    list_filter = ['date', 'ate_meal', 'member']
    search_fields = ['member__name']
    ordering = ['-date', 'member__serial_number']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'amount', 'payment_date', 'note']
    list_filter = ['payment_date', 'member']
    search_fields = ['member__name', 'note']
    ordering = ['-payment_date']
