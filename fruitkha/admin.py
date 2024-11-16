from django.contrib import admin
from .models import Account, Product, CartItem, Slider, Testimonial, Blog, Comment

# Registering the Account model
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'address')  # Display these fields in the admin list view
    search_fields = ('name', 'email', 'phone')  # Enable search by name, email, and phone
    list_filter = ('address',)  # Filter by address

# Registering the Product model
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'rating', 'category')  # Show these fields in the admin list view
    search_fields = ('name', 'category')  # Enable search by product name and category
    list_filter = ('category',)  # Enable filtering by category

# Registering the CartItem model
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('accounts', 'products', 'quantity', 'total')  # Display these fields in the admin list view
    search_fields = ('accounts__name', 'products__name')  # Search by account name and product name
    list_filter = ('accounts',)  # Filter by account
    readonly_fields = ('total',)  # Make total_price read-only in the admin

# Registering the Slider model
@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'subtitle', 'text_align', 'background_image')  # Show slider details in the list view
    search_fields = ('title', 'subtitle')  # Search sliders by title and subtitle

# Registering the Testimonial model
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    search_fields = ('name', 'title')

# Registering the Blog model
@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'date', 'tag')  # Display these fields in the list view
    prepopulated_fields = {'slug': ('title',)}  # Automatically generate slug from title
    search_fields = ('title', 'author', 'tag')  # Add search functionality
    list_filter = ('date', 'tag')  # Filter blogs by date and tag


# Registering the Comment model
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('users', 'blog', 'date', 'parent')  # Display these fields in the list view
    search_fields = ('users__name', 'comment', 'blog__title')  # Allow searching by user name, comment, and blog title
    list_filter = ('date', 'blog')  # Filter comments by date and associated blog
    autocomplete_fields = ['users', 'blog', 'parent']  # Enable autocomplete for foreign keys
