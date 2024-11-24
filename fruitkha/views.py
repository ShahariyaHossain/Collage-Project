# ===============================================================================================
# =============================  Import Built-in Modules  =======================================
# ===============================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
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
import requests

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


# class CartView(TemplateView):
#     template_name = 'cart.html'
#     # login_url = '/login/'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # cart_items = CartItem.objects.filter(accounts=self.request.user)
        
#         # Ensure the request user is an instance of Account
#         user = self.request.user
#         account = None

#         if isinstance(user, Account):
#             account = user
#             cart_items = CartItem.objects.filter(accounts=account)
#         else:
#             cart_items = []  # Unauthenticated or non-Account user sees an empty cart

#         # Calculate subtotal, discount, and total for the cart
#         subtotal = sum(item.products.price * item.quantity for item in cart_items)
#         discount = sum(item.discount for item in cart_items)
#         total = subtotal - discount

#         context.update({
#             'cart_items': cart_items,
#             'subtotal': subtotal,
#             'discount': discount,
#             'total': total,
#         })
#         return context

#     def post(self, request, *args, **kwargs):
#         action = request.POST.get('action')
#         cart_item_id = request.POST.get('id')
#         coupon_code = request.POST.get('coupon', '')
        
#         # Ensure the request user is an instance of Account
#         user = request.user
#         if not isinstance(user, Account):
#             return JsonResponse({'error': 'Invalid user'}, status=400)

#         cart_items = CartItem.objects.filter(accounts=user)

#         # Handle 'update' action: Update cart item quantity
#         if action == 'update':
#             cart_item = get_object_or_404(CartItem, id=cart_item_id)
#             cart_item.quantity = int(request.POST.get('quantity', 1))
#             cart_item.calculate_totals()

#         # Handle 'remove' action: Remove the item from the cart
#         elif action == 'remove':
#             cart_item = get_object_or_404(CartItem, id=cart_item_id)
#             cart_item.delete()

#         # Handle 'apply_coupon' action: Apply coupon logic
#         elif action == 'apply_coupon':
#             # Simulate coupon logic
#             cart_items = CartItem.objects.filter(accounts=request.user)
#             for cart_item in cart_items:
#                 if coupon_code == 'DISCOUNT10':  # Replace with your coupon validation logic
#                     cart_item.discount = min(cart_item.subtotal, Decimal('10.00'))
#                 else:
#                     cart_item.discount = Decimal('0.00')
#                 cart_item.calculate_totals()

#         # Refresh cart data and return updated context
#         # cart_items = CartItem.objects.filter(accounts=request.user)
#         subtotal = sum(item.products.price * item.quantity for item in cart_items)
#         discount = sum(item.discount for item in cart_items)
#         total = subtotal - discount

#         data = {
#             'subtotal': subtotal,
#             'discount': discount,
#             'total': total,
#         }

#         # Return updated data as a JSON response
#         return JsonResponse(data)

class CartView(TemplateView):
    template_name = 'cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Use session-based cart only for unauthorized users
        session_cart = self.request.session.get('cart', [])
        cart_items = self._get_session_cart_items(session_cart)

        subtotal = sum(item['products'].price * item['quantity'] for item in cart_items)
        discount = sum(item['discount'] for item in cart_items)
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
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        session_cart = request.session.get('cart', [])

        if not product_id and action in ['remove', 'update', 'add']:
            return JsonResponse({'error': 'Product ID is required for this action'}, status=400)

        if action == 'add':
            return self._add_to_cart(request, product_id, quantity, session_cart)
        elif action == 'update':
            return self._update_cart(request, product_id, quantity, session_cart)
        elif action == 'remove':
            return self._remove_from_cart(request, product_id, session_cart)
        elif action == 'apply_coupon':
            coupon_code = request.POST.get('coupon', '')
            return self._apply_coupon(request, coupon_code, session_cart)

        return JsonResponse({'error': 'Invalid action'}, status=400)

    def _get_session_cart_items(self, session_cart):
        """Return session cart items in proper format."""
        return [
            {
                'id': item['product_id'],
                'products': Product.objects.get(id=item['product_id']),
                'quantity': item['quantity'],
                'discount': Decimal(item.get('discount', 0)),
                'subtotal': Decimal(item['subtotal']),
                'total': Decimal(item['total']),
            }
            for item in session_cart
        ]

    def _add_to_cart(self, request, product_id, quantity, session_cart):
        """Handles adding products to the cart."""
        product = get_object_or_404(Product, id=product_id)

        for item in session_cart:
            if item['product_id'] == product.id:
                item['quantity'] += quantity
                item['subtotal'] = float(product.price * item['quantity'])
                item['total'] = item['subtotal'] - float(item.get('discount', Decimal('0.00')))
                break
        else:
            session_cart.append({
                'product_id': product.id,
                'quantity': quantity,
                'subtotal': float(product.price * quantity),
                'total': float(product.price * quantity),
                'discount': 0.0,
            })
        request.session['cart'] = session_cart

        return self._refresh_cart_context()

    def _update_cart(self, request, product_id, quantity, session_cart):
        """Handles updating product quantities in the cart."""
        for item in session_cart:
            if item['product_id'] == int(product_id):
                item['quantity'] = quantity
                item['subtotal'] = float(Product.objects.get(id=product_id).price * quantity)
                item['total'] = item['subtotal'] - float(item.get('discount', 0))
                break
        request.session['cart'] = session_cart

        return self._refresh_cart_context()

    def _remove_from_cart(self, request, product_id, session_cart):
        """Handles removing products from the cart."""
        session_cart = [item for item in session_cart if item['product_id'] != int(product_id)]
        request.session['cart'] = session_cart

        return self._refresh_cart_context()

    def _apply_coupon(self, request, coupon_code, session_cart):
        """Handles applying a coupon to the cart."""
        discount_amount = 10.0 if coupon_code == 'DISCOUNT10' else 0.0

        for item in session_cart:
            item['discount'] = discount_amount
            item['total'] = item['subtotal'] - discount_amount
        request.session['cart'] = session_cart

        return self._refresh_cart_context()

    def _refresh_cart_context(self):
        cart_items, subtotal, discount, total = self._get_cart_data()

        # Generate updated items for the frontend
        updated_items = {
            str(item['id']): {
                'total': str(item['total']),
            }
            for item in cart_items
        }

        return JsonResponse({
            'subtotal': str(subtotal),
            'discount': str(discount),
            'total': str(total),
            'updated_items': updated_items,
        })


    def _get_cart_data(self):
        """Fetch current cart items and totals."""
        session_cart = self.request.session.get('cart', [])
        cart_items = self._get_session_cart_items(session_cart)

        subtotal = sum(item['products'].price * item['quantity'] for item in cart_items)
        discount = sum(item['discount'] for item in cart_items)
        total = subtotal - discount

        return cart_items, subtotal, discount, total




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
from django.contrib.auth.hashers import make_password
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm
from .models import Account
import json

class SignUpView(View):
    template_name = 'signup.html'

    def get(self, request):
        """Render the sign-up page with the registration form."""
        form = SignUpForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Handle AJAX email validation and form submission."""
        if request.content_type == 'application/json':  # AJAX email validation
            try:
                data = json.loads(request.body)
                email = data.get('email', '').strip()

                # Check if email already exists
                if Account.objects.filter(email=email).exists():
                    return JsonResponse({'success': False, 'errors': {'email': 'This email is already registered.'}})
                return JsonResponse({'success': True})
            except Exception:
                return JsonResponse({'success': False, 'errors': {'general': 'An error occurred. Please try again.'}})

        # Regular form submission
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Save account and hash the password
            account = form.save(commit=False)
            account.set_password(form.cleaned_data['password'])
            account.save()

            # Log in the user
            login(request, account)
            messages.success(request, "Account created successfully.")
            return JsonResponse({'success': True, 'redirect_url': redirect('home').url})  # Replace 'home' with your URL name
        else:
            # Collect form errors
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({'success': False, 'errors': errors})



# ===============================================================================================
# =================================  Handling User Signup  ======================================
# ===============================================================================================
class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        """Render the login page."""
        return render(request, self.template_name)

    def post(self, request):
        """Handle AJAX login requests."""
        import json
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        remember = data.get('remember', False)

        # Initialize response data
        response_data = {'success': False, 'errors': {}}

        # Validate email
        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            response_data['errors']['email'] = 'Email not found.'
            return JsonResponse(response_data)

        # Validate password
        if not check_password(password, user.password):
            response_data['errors']['password'] = 'Invalid password.'
            return JsonResponse(response_data)

        # Authenticate and login user
        user = authenticate(request, username=user.email, password=password)
        if user is not None:
            # Login user
            login(request, user)

            # Set session expiry based on "Remember Me"
            if remember:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(172800)  # 2 days

            # Success response
            response_data['success'] = True
            response_data['redirect_url'] = '/'  # Redirect to home or a custom URL
            return JsonResponse(response_data)
        else:
            response_data['errors']['password'] = 'Authentication failed.'
            return JsonResponse(response_data)




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
        # Check if user is authenticated and is an Account instance
        if isinstance(request.user, Account):
            cart_items = CartItem.objects.filter(accounts=request.user)
        else:
            # Use session-based cart for non-Account users
            session_cart = request.session.get('cart', [])
            cart_items = [
                {
                    'subtotal': Decimal(item['subtotal']),
                    'discount': Decimal(item['discount']),
                }
                for item in session_cart
            ]

        # Ensure cart has items
        if not cart_items:
            return JsonResponse({'error': 'No items in your cart.'}, status=400)

        # Calculate total amount
        total_amount = sum((item['subtotal'] - item['discount']) for item in cart_items) + Decimal('50.00')

        # Generate unique transaction ID
        tran_id = str(uuid.uuid4())

        # SSLCommerz settings
        ssl_settings = settings.SSLCOMMERZ_SETTINGS
        sslcommez = SSLCOMMERZ(ssl_settings)

        # All payment results point to the same view, differentiated by query parameters
        result_url = request.build_absolute_uri(reverse('payment_result'))
        
        """
        If you use dummy sslcommerz_lib,
        then turn in the two store_id and store password from post_body,
        otherwise turn off them
        """
        # Payment information
        post_body = {
            'store_id': "examp66eead598747c",
            'store_passwd': "examp66eead598747c@ssl",
            'total_amount': str(total_amount),
            'currency': 'BDT',
            'tran_id': tran_id,
            'success_url': result_url,
            'fail_url': result_url,
            'cancel_url': result_url,
            'emi_option': 0,
            'cus_name': request.user.name if isinstance(request.user, Account) else 'Guest',
            'cus_email': request.user.email if isinstance(request.user, Account) else 'guest@example.com',
            'cus_phone': request.user.phone if isinstance(request.user, Account) else '0000000000',
            'cus_add1': 'Customer Address',
            'cus_city': 'Dhaka',
            'cus_country': 'Bangladesh',
            'shipping_method': 'Courier',
            'num_of_item': len(cart_items),
            'product_name': 'Cart Items',
            'product_category': 'General',
            'product_profile': 'general'
        }
        """ turn in this two line if you use the real sslcommer_lib
        response = sslcommez.createSession(post_body)
        return redirect(response['GatewayPageURL'])
        
        # and if you use dummy sslcommerz_lib, the turn in the below code block
        """
        response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v3/api.php', data=post_body)

        if response.status_code == 200:
            try:
                response_data = response.json()
                gateway_url = response_data.get('GatewayPageURL')
                if gateway_url:
                    return redirect(gateway_url)
                else:
                    messages.error(request, "Invalid response from the payment gateway.")
            except ValueError:
                messages.error(request, "Failed to parse response from the payment gateway.")
        else:
            messages.error(request, "Payment initiation failed. Please try again later.")
            return redirect('cart')

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render
from django.views.generic import TemplateView

@method_decorator(csrf_exempt, name='dispatch')
class PaymentResultView(TemplateView):
    template_name = 'payment_result.html'

    def post(self, request, *args, **kwargs):
        # Extract necessary data from POST request
        status = request.POST.get('status', 'FAILED')
        failed_reason = request.POST.get('failedreason', 'No reason provided')
        tran_id = request.POST.get('tran_id', '')
        amount = request.POST.get('amount', 'N/A')
        currency = request.POST.get('currency', 'N/A')
        payment_method = request.POST.get('card_type', 'N/A')
        date = request.POST.get('tran_date', 'N/A')
        cus_name = request.POST.get('cus_name', 'Guest')

        # Prepare context for the template
        context = {
            'status': 'Success' if status == 'VALID' else 'Failed',
            'tran_id': tran_id,
            'reason': failed_reason if status != 'VALID' else None,
            'username': request.user.username if request.user.is_authenticated else cus_name,
            'amount': amount,
            'currency': currency,
            'payment_method': payment_method,
            'date': date,
        }

        # Provide user feedback based on payment status
        if status == 'VALID':
            messages.success(request, f"Payment was successful for transaction ID: {tran_id}")
        else:
            messages.error(request, f"Payment failed: {failed_reason}")

        return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        # Handle cases where GET requests might be sent
        return JsonResponse({'error': 'Invalid request method'}, status=405)




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



def signup_b(request):
    return render(request, 'signup-b.html')
def login_b(request):
    return render(request, 'login-b.html')
