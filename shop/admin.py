from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Manufacturer, Category, Product, Customer,
    Order, Employee, AboutCompany, News,
    FAQ, Contact, Vacancy, Review, PromoCode
)

# Register your models here.
# This allows you to add/edit orders directly on the Customer's page
class OrderInline(admin.TabularInline):
    model = Order
    extra = 1
    fields = ('product', 'quantity', 'delivery_date')

class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Данные профиля (Клиент)'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (CustomerInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_city')

    def get_city(self, instance):
        return instance.customer.city if hasattr(instance, 'customer') else '-'

    get_city.short_description = 'Город'

# Перерегистрация User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin Classes
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'city', 'email', 'phone', 'age')
    list_filter = ('city',)
    search_fields = ('full_name', 'email', 'phone')
    inlines = [OrderInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'unit', 'manufacturer')
    list_filter = ('category', 'manufacturer')  # Filtering by category and manufacturer
    search_fields = ('title',)
    list_editable = ('price',) # Quick price edits from the list view

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'product', 'quantity', 'created_at', 'delivery_date')
    list_filter = ('created_at', 'delivery_date')
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'created_at')
    list_filter = ('rating',) # Required: Filtering by rating/score

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publish_date')
    search_fields = ('title', 'content')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_archived')
    list_filter = ('is_archived',)

admin.site.register(Manufacturer)
admin.site.register(Category)
admin.site.register(Employee)
admin.site.register(AboutCompany)
admin.site.register(FAQ)
admin.site.register(Vacancy)