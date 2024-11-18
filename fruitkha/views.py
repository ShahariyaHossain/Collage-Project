# ===============================================================================================
# =============================  Import Built-in Modules  =======================================
# ===============================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ
import uuid
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from requests

# ===============================================================================================
# ============================  Import Shop Models & Forms  =====================================
# ===============================================================================================
from .models import Account, Product, CartItem, Slider, Testimonial, Blog, Comment, TeamMember, ContactMessage, ContactDetails, Subscription
from django.db.models import Count
from .forms import SignUpForm
from decimal import Decimal
from .signals import multi_signal

# ===============================================================================================
# ================================  Handling Home Page  =========================================
# ===============================================================================================

class HomePageView(ListView):
    model = Slider
    template_name = 'home.html'
    context_object_name = 'sliders'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)

        # Add products, testimonials, and recent blogs to the context
        context['products'] = Product.objects.all().order_by('-id')[:3]  # Fetch only 4 products
        context['testimonials'] = Testimonial.objects.all()  # Fetch all testimonials
        context['blogs'] = Blog.objects.order_by('-date')[:3]  # Fetch latest 3 blog posts
        return context


def news_list(request):
    blogs = Blog.objects.order_by('-date')
    paginator = Paginator(blogs, 6)  # 6 posts per page
    
    page = request.GET.get('page')
    try:
        blogs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        blogs = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results
        blogs = paginator.page(paginator.num_pages)

    return render(request, 'news.html', {'blogs': blogs})


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'single-news.html'
    context_object_name = 'blog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pass top-level comments
        context['comments'] = Comment.objects.filter(blog=self.object).select_related('users', 'parent')

        # Recent posts
        context['recent_posts'] = Blog.objects.exclude(slug=self.object.slug).order_by('-date')[:5]

        # Archive posts
        context['archive_posts'] = (
            Blog.objects
            .exclude(slug=self.object.slug)
            .dates('date', 'month', order='DESC')
            .distinct()
        )

        # Archive filter handling
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        if year and month:
            context['archive_filtered'] = Blog.objects.filter(
                date__year=year, date__month=month
            ).exclude(slug=self.object.slug).order_by('-date')
        else:
            context['archive_filtered'] = None

        # Tags
        context['tags'] = Blog.objects.values_list('tag', flat=True).distinct()
        tag_filter = self.request.GET.get('tag')
        if tag_filter:
            context['tag_filtered'] = Blog.objects.filter(tag__iexact=tag_filter).exclude(slug=self.object.slug).order_by('-date')
        else:
            context['tag_filtered'] = None

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        blog = self.object

        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to post a comment.")
            return redirect('login')

        # Get submitted comment data
        comment_text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')

        # Get parent comment if replying
        parent_comment = None
        if parent_id:
            parent_comment = get_object_or_404(Comment, id=parent_id)

        # Create the comment
        comment = Comment.objects.create(
            blog=blog,
            users=request.user,
            comment=comment_text,
            parent=parent_comment
        )

        # Trigger the multi_signal for comment notification
        multi_signal.send_robust(
            sender=Comment,
            subject="New Comment on Your Blog",
            message=f"A new comment has been posted by {request.user.username} on your blog '{blog.title}'.",
            recipient_list=[blog.author.email]  # Replace with blog author's email
        )

        messages.success(request, "Your comment has been added successfully.")
        return redirect('blog-detail', slug=blog.slug)


def products_list(request):
    products = Product.objects.order_by('-id')  # Order by the latest product
    paginator = Paginator(products, 6)  # 6 products per page
    
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results
        products = paginator.page(paginator.num_pages)

    # Get unique categories from the model's CATEGORY_CHOICES
    categories = dict(Product.CATEGORY_CHOICES).keys()

    return render(request, 'products.html', {'products': products, 'categories': categories})


class SingleProductView(DetailView):
    model = Product
    template_name = 'single-product.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        return Product.objects.get(slug=self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Fetch related products based on the same category, excluding the current product
        context['related_products'] = Product.objects.filter(
            category=self.object.category
        ).exclude(slug=self.object.slug)[:3]  # Limit to 3 related products

        return context


class CartView(LoginRequiredMixin, TemplateView):
    template_name = 'cart.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_items = CartItem.objects.filter(accounts=self.request.user)
        
        # Calculate subtotal, discount, and total for the cart
        subtotal = sum(item.products.price * item.quantity for item in cart_items)
        discount = sum(item.discount for item in cart_items)
        total = subtotal - discount

        context.update({
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
        })
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        cart_item_id = request.POST.get('id')
        coupon_code = request.POST.get('coupon', '')

        # Handle 'update' action: Update cart item quantity
        if action == 'update':
            cart_item = get_object_or_404(CartItem, id=cart_item_id)
            cart_item.quantity = int(request.POST.get('quantity', 1))
            cart_item.calculate_totals()

        # Handle 'remove' action: Remove the item from the cart
        elif action == 'remove':
            cart_item = get_object_or_404(CartItem, id=cart_item_id)
            cart_item.delete()

        # Handle 'apply_coupon' action: Apply coupon logic
        elif action == 'apply_coupon':
            # Simulate coupon logic
            cart_items = CartItem.objects.filter(accounts=request.user)
            for cart_item in cart_items:
                if coupon_code == 'DISCOUNT10':  # Replace with your coupon validation logic
                    cart_item.discount = min(cart_item.subtotal, Decimal('10.00'))
                else:
                    cart_item.discount = Decimal('0.00')
                cart_item.calculate_totals()

        # Refresh cart data and return updated context
        cart_items = CartItem.objects.filter(accounts=request.user)
        subtotal = sum(item.products.price * item.quantity for item in cart_items)
        discount = sum(item.discount for item in cart_items)
        total = subtotal - discount

        data = {
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
        }

        # Return updated data as a JSON response
        return JsonResponse(data)



class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'checkout.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cart_items = CartItem.objects.filter(accounts=user)

        subtotal = sum(item.subtotal for item in cart_items)
        discount = sum(item.discount for item in cart_items)
        total = subtotal - discount + 50  # Fixed shipping cost

        context.update({
            'user': get_object_or_404(Account, id=user.id),  # Fetch user details from Account model
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
        })
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles form submissions (e.g., saving 'say_something' from billing form).
        """
        action = request.POST.get('action', '')
        if action == 'save_billing':
            # Save 'say_something' for each cart item (if multiple exist)
            for item in CartItem.objects.filter(accounts=request.user):
                item.say_something = request.POST.get('say_something', '')
                item.save()
            return JsonResponse({'message': 'Billing info saved successfully!'})

        # Default response
        return JsonResponse({'error': 'Invalid action'}, status=400)

# ===============================================================================================
# =================================  Handling User Signup  ======================================
# ===============================================================================================


class SignUpView(View):
    def get(self, request):
        """Render the sign-up page with the registration form."""
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request):
        """Handle form submission for user registration."""
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save the account (custom model)
            account = form.save(commit=False)
            account.set_password(form.cleaned_data['password'])  # Encrypt the password
            account.save()

            # Log the user in automatically after registration
            login(request, account)
            
            # Display success message
            messages.success(request, "Account created successfully.")
            
            # Trigger the signal to send a welcome email
            multi_signal.send_robust(
                sender=account.__class__,
                subject="Welcome to Fruitkha",
                message="Hello! Thank you for joining Fruitkha.",
                recipient_list=[account.email]  # Correct recipient
            )
            
            return redirect('home')  # Redirect to home or another suitable page
        else:
            messages.error(request, "Error during registration. Please try again.")
        
        return render(request, 'signup.html', {'form': form})



# ===============================================================================================
# ===================================  About View  ==============================================
# ===============================================================================================
class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team_members'] = TeamMember.objects.all()  # Fetch all team members
        context['testimonials'] = Testimonial.objects.all()  # Fetch all testimonials
        return context

# ===============================================================================================
# ===================================  Contact View  ============================================
# ===============================================================================================
class ContactView(TemplateView):
    template_name = 'contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = ContactDetails.objects.first() # or None  # Load the first contact details entry
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Validate and save the message
        if not name or not email or not message:
            messages.error(request, "Name, email, and message are required.")
            return redirect('contact')
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        
        # Fetch all recipient emails
        recipient_emails = ContactDetails.objects.filter(email__isnull=False).values_list('email', flat=True)
        recipient_email_list = list(recipient_emails)

        if not recipient_email_list:
            messages.error(request, "No recipient email configured. Please contact support.")
            return redirect('contact')

        # Trigger the multi_signal to notify admin
        multi_signal.send_robust(
            sender=ContactMessage,
            subject=f"New Contact Message from {name}",
            message=f"""
                You have received a new message:
                
                Name: {name}
                Email: {email}
                Phone: {phone}
                Subject: {subject}
                Message: {message}
            """,
            recipient_list=recipient_email_list
        )

        # Notify user and redirect back to the contact page
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')

# ===============================================================================================
# ===================================  Handling Payment  =====================================
# ===============================================================================================

class PaymentInitView(View):
    def post(self, request, *args, **kwargs):
        user = request.user
        cart_items = CartItem.objects.filter(accounts=user)

        if not cart_items.exists():
            return JsonResponse({'error': 'No items in your cart.'}, status=400)

        # Calculate total amount
        total_amount = sum((item.subtotal - item.discount) for item in cart_items) + 50

        # Generate unique transaction ID
        tran_id = str(uuid.uuid4())

        # SSLCommerz settings
        ssl_settings = settings.SSLCOMMERZ_SETTINGS
        sslcommez = SSLCOMMERZ(ssl_settings)

        # Payment information
        post_body = {
            'total_amount': str(total_amount),
            'currency': 'BDT',
            'tran_id': tran_id,
            'success_url': request.build_absolute_uri('/payment-success/'),
            'fail_url': request.build_absolute_uri('/payment-failure/'),
            'cancel_url': request.build_absolute_uri('/payment-cancel/'),
            'emi_option': 0,
            'cus_name': user.name,
            'cus_email': user.email,
            'cus_phone': user.phone,
            'cus_add1': 'Customer Address',
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'shipping_method': 'Courier',
            'num_of_item': len(cart_items),
            'product_name': 'Cart Items',
            'product_category': 'General',
            'product_profile': 'general'
        }

        response = sslcommez.createSession(post_body)
        return redirect(response['GatewayPageURL'])


# PaymentResultView for Handling Results
class PaymentResultView(TemplateView):
    template_name = 'payment_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tran_id': self.request.GET.get('tran_id'),
            'status': self.request.GET.get('status'),
            'amount': self.request.GET.get('amount'),
            'currency': self.request.GET.get('currency'),
            'payment_method': self.request.GET.get('card_type'),
            'date': self.request.GET.get('tran_date'),
            'cus_name': self.request.GET.get('cus_name')
        })
        return context



# @login_required
# def make_payment(request):
#     cart_items = CartItem.objects.filter(user=request.user)
#     if not cart_items.exists():
#         messages.error(request, "Your cart is empty!")
#         return redirect('home')

#     total_amount = sum([item.total_price for item in cart_items])
#     tran_id = str(uuid.uuid4())

#     post_body = {
#         'store_id': "examp66eead598747c",
#         'store_passwd': "examp66eead598747c@ssl",
#         'total_amount': total_amount,
#         'currency': 'BDT',
#         'tran_id': tran_id,
#         'success_url': request.build_absolute_uri(reverse('payment_result')),
#         'fail_url': request.build_absolute_uri(reverse('payment_result')),
#         'cancel_url': request.build_absolute_uri(reverse('payment_result')),
#         'emi_option': 0,
#         'cus_name': request.user.username,
#         'cus_email': request.user.email,
#         'cus_add1': 'Dhaka',
#         'cus_city': 'Dhaka',
#         'cus_country': 'Bangladesh',
#     }

#     response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v3/api.php', data=post_body)

#     if response.status_code == 200:
#         response_data = response.json()
#         if 'GatewayPageURL' in response_data:
#             return redirect(response_data['GatewayPageURL'])
#         else:
#             messages.error(request, "Invalid response from the payment gateway.")
#             return redirect('cart')
#     else:
#         messages.error(request, "Payment initiation failed.")
#         return redirect('cart')



# @csrf_exempt
# def payment_result(request):
#     if request.method == 'POST':
#         status = request.POST.get('status', 'FAILED')
#         failed_reason = request.POST.get('failedreason', 'No reason provided')
#         tran_id = request.POST.get('tran_id', '')

#         if status == 'VALID':
#             # Payment successful
#             messages.success(request, f"Payment was successful for transaction ID: {tran_id}")
#             return render(request, 'payment_result.html', {'status': 'Success', 'username': request.user.username})
#         else:
#             # Payment failed or was canceled
#             messages.error(request, f"Payment failed: {failed_reason}")
#             return render(request, 'payment_result.html', {'status': 'Failed', 'username': request.user.username, 'reason': failed_reason})

#     return JsonResponse({'error': 'Invalid request method'}, status=405)


# @login_required
# def add_to_cart(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
#     if not created:
#         cart_item.quantity += 1
#         cart_item.save()
#     return redirect('home')

# @login_required
# def cart(request):
#     cart_items = CartItem.objects.filter(user=request.user)
#     total_amount = sum(item.total_price for item in cart_items)
#     return render(request, 'cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

# @login_required
# def update_cart(request, item_id):
#     cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
#     if 'increase' in request.POST:
#         cart_item.quantity += 1
#         cart_item.save()
#     elif 'decrease' in request.POST:
#         if cart_item.quantity > 1:
#             cart_item.quantity -= 1
#             cart_item.save()
#         else:
#             cart_item.delete()
#     return redirect('cart')




# Further.....
class SubscribeView(View):
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if email:
            if not Subscription.objects.filter(email=email).exists():
                Subscription.objects.create(email=email)
                return JsonResponse({'status': 'success', 'message': "Thank you for subscribing!"})
            else:
                return JsonResponse({'status': 'info', 'message': "You are already subscribed."})
        else:
            return JsonResponse({'status': 'error', 'message': "Please enter a valid email."})




