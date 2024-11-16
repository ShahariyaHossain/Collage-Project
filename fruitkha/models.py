from django.db import models
from django.utils.timezone import now
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string

class Account(models.Model):
    # Validator for name with alphabetic characters and spaces only
    string_regex = RegexValidator(
        regex=r'^[a-zA-Z]+(?:\s[a-zA-Z]+)*$',
        message="Name can only contain alphabetic characters and spaces."
    )

    # Validator for a valid phone number
    mobile_validate = RegexValidator(
        regex=r'^\+?\d{1,4}?[\d\s]{7,20}$',
        message='Enter a valid mobile number with optional country code.'
    )

    name = models.CharField(max_length=100, validators=[string_regex])
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, validators=[mobile_validate])
    password = models.CharField(max_length=100)
    photos = models.ImageField(upload_to='profile_photos/', default='profile_photos/default.gif', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} | {self.email} | {self.phone} | {self.address or 'No Address'}"


class Product(models.Model):
    # Products categories
    CATEGORY_CHOICES = [
        ('strawberry', 'Strawberry'),
        ('berry', 'Berry'),
        ('lemon', 'Lemon'),
        ('apple', 'Apple'),
        ('avocado', 'Avocado'),
    ]

    name = models.CharField(max_length=100, help_text="Name of the product")
    description = models.TextField(max_length=500, help_text="Short description of the product")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)],
        help_text="Price of the product (minimum $0.01)."
    )
    photos = models.ImageField(
        upload_to='product_photos/', 
        default='product_photos/default-1.gif', 
        blank=True, 
        null=True,
        help_text="Product image."
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, help_text="Category of the product")
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Rating of the product (0.0 to 5.0).",
        default=0.0
    )
    
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, help_text="URL-friendly version of the name")

    def __str__(self):
        return f"{self.name} | ৳{self.price} | {self.category}"


# Utility function to ensure unique slugs
def generate_unique_slug(instance, new_slug=None):
    slug = new_slug or slugify(instance.name)
    Klass = instance.__class__
    if Klass.objects.filter(slug=slug).exists():
        random_suffix = get_random_string(length=6)  # Ensures uniqueness
        return generate_unique_slug(instance, f"{slug}-{random_suffix}")
    return slug


# Signal to automatically generate slugs if missing
def pre_save_product_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = generate_unique_slug(instance)


pre_save.connect(pre_save_product_receiver, sender=Product)


# CartItem Models
class CartItem(models.Model):
    accounts = models.ForeignKey('Account', on_delete=models.CASCADE, related_name="cart_users")
    products = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    say_something = models.TextField(max_length=500, blank=True, help_text="Optional message about this cart item.")
    coupon = models.CharField(max_length=50, blank=True, null=True, help_text="Coupon code for discount")
    # New fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Final total for this cart item after discount")

    def __str__(self):
        return f"{self.quantity} of {self.products.name} by {self.accounts.name}"

    def calculate_totals(self):
        self.subtotal = self.products.price * self.quantity
        self.total = self.subtotal - self.discount
        self.save()


# ===============Slider Model for the Home Page==============
class Slider(models.Model):
    TEXT_ALIGN_CHOICES = [
        ('col-lg-7 offset-lg-1 offset-xl-0', 'Left Align'),
        ('text-center', 'Center Align'),
        ('text-right', 'Right Align'),
    ]

    title = models.CharField(max_length=255, help_text="Main heading for the slider")
    subtitle = models.CharField(max_length=255, help_text="Subtitle for the slider")
    background_image = models.ImageField(upload_to='slider_photos/', help_text="Background image for the slider")
    text_align = models.CharField(max_length=250, choices=TEXT_ALIGN_CHOICES, default='text-center', help_text="Text alignment for the slider content")

    def __str__(self):
        return self.title


# ===============Testimonial for the Home Page==============
class Testimonial(models.Model):
    name = models.CharField(max_length=100, help_text="Client's name")
    title = models.CharField(max_length=100, help_text="Client's title or occupation")
    description = models.TextField(help_text="Testimonial content")
    photo = models.ImageField(upload_to='test_photos/', default='test_photos/default.gif', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.title}"


# ===============Blog for the Single News Page==============
class Blog(models.Model):
    author = models.CharField(max_length=100, help_text="Name of the author")
    title = models.CharField(max_length=255, help_text="Title of the blog post")
    description = models.TextField(help_text="Content of the blog post")
    date = models.DateTimeField(auto_now_add=True, help_text="Date when the blog was created")
    slug = models.SlugField(unique=True, blank=True, null=True, help_text="URL-friendly version of the title")
    tag = models.CharField(max_length=100, help_text="Tag for the blog post")
    photo = models.ImageField(upload_to='blog_photos/', help_text="Blog post image", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.author}"

# ===============Comment for the Single News Page==============
class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    users = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='user_comments')
    comment = models.TextField(help_text="User comment text")
    date = models.DateTimeField(auto_now_add=True, help_text="Date when the comment was created")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"Comment by {self.users.name} on {self.blog.title}"

# =============== Team Members ===============
class TeamMember(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the team member")
    role = models.CharField(max_length=250, help_text="Role of the team member")
    photo = models.ImageField(
        upload_to='team_photos/', 
        default='team_photos/team_default-1.jpg', 
        help_text="Team member image", 
        blank=True, 
        null=True
    )
    facebook = models.URLField(blank=True, null=True, help_text="Facebook account of the team member")
    linkedin = models.URLField(blank=True, null=True, help_text="LinkedIn account of the team member")
    github = models.URLField(blank=True, null=True, help_text="GitHub account of the team member")

    def __str__(self):
        return f"{self.name} - {self.role}"


# =============== Contact Messages ===============
class ContactMessage(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the person sending the message")
    email = models.EmailField(help_text="Email of the person sending the message")
    phone = models.CharField(max_length=15, help_text="Phone number of the person sending the message")
    subject = models.CharField(max_length=200, help_text="Subject of the message")
    message = models.TextField(help_text="The message content")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the message was created")

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


# =============== Contact Details ===============
class ContactDetails(models.Model):
    shop_address = models.TextField(help_text="Shop address")
    shop_hours = models.TextField(help_text="Operating hours of the shop")
    phone = models.CharField(max_length=15, help_text="Shop phone number")
    email = models.EmailField(help_text="Shop contact email")
    google_map_embed = models.TextField(help_text="Embed link for Google Maps")

    # Social Media Links
    facebook = models.URLField(blank=True, null=True, help_text="Facebook URL")
    x = models.URLField(blank=True, null=True, help_text="X (formerly Twitter) URL")  # Renamed from Twitter
    instagram = models.URLField(blank=True, null=True, help_text="Instagram URL")
    linkedin = models.URLField(blank=True, null=True, help_text="LinkedIn URL")
    github = models.URLField(blank=True, null=True, help_text="GitHub URL")  # Replaces Dribbble

    def __str__(self):
        return "Contact Details"



# Subscription
class Subscription(models.Model):
    email = models.EmailField(unique=True, help_text="Email address of the subscriber")
    subscribed_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the user subscribed")

    def __str__(self):
        return self.email
