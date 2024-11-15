# ===============================================================================================
# =============================  Import Built-in Modules  =======================================
# ===============================================================================================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from django.contrib import messages
import uuid
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# # from requests
    
# ===============================================================================================
# ============================  Import Shop Models & Forms  =====================================
# ===============================================================================================
from .models import Account, Product, CartItem, Slider, Testimonial, Blog, Comment
# from .forms import SignupForm
from django.db.models import Count

# # STORE_ID = "onsho5f1d196bdff9c"
# # STORE_PASSWORD = "onsho5f1d196bdff9c@ssl"
# # API_URL = "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"



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




# def home(request):
#     context = {
#         'key1': 'value1',
#         'key2': 'value2',
#         # Add other context variables as needed
#     }
#     return render(request, 'home.html', context)


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

        # Pass top-level comments (exclude nested rendering in template)
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
        Comment.objects.create(
            blog=blog,
            users=request.user,
            comment=comment_text,
            parent=parent_comment
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





# ===============================================================================================
# =================================  Handling User Signup  ======================================
# ===============================================================================================
# def signup(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
        
#         # Check if "agree-term" is checked
#         if not request.POST.get('agree-term'):
#             form.add_error(None, "You must agree to the Terms and Conditions.")
        
#         if form.is_valid():
#             users = form.save()  # Save the users data to the database
#             return redirect('login')  # Send user to the login page

#     else:
#         form = SignupForm()

#     return render(request, 'signup.html', {'form': form})


# ===============================================================================================
# ===================================  Handling User Login  =====================================
# ===============================================================================================
# def login(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
        
#         if form.is_valid():
#             # Save the user data (commit=True saves it to the database)
#             user = form.save()
#             return redirect('home')  # Replace with the URL of your success page

#     else:
#         form = SignupForm()

#     return render(request, 'login_23.html', {'form': form})


# def animated_bg(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
        
#         if form.is_valid():
#             # Save the user data (commit=True saves it to the database)
#             user = form.save()
#             return redirect('success_page')  # Replace with the URL of your success page

#     else:
#         form = SignupForm()

#     return render(request, 'animated_bg.html', {'form': form})


def success(request):
    context = {'key': 'value'}
    return render(request, 'cart.html', context)

def home_1(request):
    context = {'key': 'value'}
    return render(request, 'home.html', context)

def shoping_cart(request):
    context = {'key': 'value'}
    return render(request, 'shoping-cart.html', context)


# def home(request):
#     products = Product.objects.all()
#     if request.method == 'POST':
#         if 'signup' in request.POST:
#             form = UserCreationForm(request.POST)
#             if form.is_valid():
#                 user = form.save()
#                 login(request, user)
#                 return redirect('home')
#         elif 'login' in request.POST:
#             pass
#     else:
#         form = UserCreationForm()
#     return render(request, 'home.html', {'products': products, 'form': form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('home')

@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total_amount = sum(item.total_price for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_amount': total_amount})

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if 'increase' in request.POST:
        cart_item.quantity += 1
        cart_item.save()
    elif 'decrease' in request.POST:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('cart')

@login_required
def make_payment(request):
    cart_items = CartItem.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Your cart is empty!")
        return redirect('home')

    total_amount = sum([item.total_price for item in cart_items])
    tran_id = str(uuid.uuid4())

    post_body = {
        'store_id': "examp66eead598747c",
        'store_passwd': "examp66eead598747c@ssl",
        'total_amount': total_amount,
        'currency': 'BDT',
        'tran_id': tran_id,
        'success_url': request.build_absolute_uri(reverse('payment_result')),
        'fail_url': request.build_absolute_uri(reverse('payment_result')),
        'cancel_url': request.build_absolute_uri(reverse('payment_result')),
        'emi_option': 0,
        'cus_name': request.user.username,
        'cus_email': request.user.email,
        'cus_add1': 'Dhaka',
        'cus_city': 'Dhaka',
        'cus_country': 'Bangladesh',
    }

    # response = requests.post('https://sandbox.sslcommerz.com/gwprocess/v3/api.php', data=post_body)

    # if response.status_code == 200:
    #     response_data = response.json()
    #     if 'GatewayPageURL' in response_data:
    #         return redirect(response_data['GatewayPageURL'])
    #     else:
    #         messages.error(request, "Invalid response from the payment gateway.")
    #         return redirect('cart')
    # else:
    #     messages.error(request, "Payment initiation failed.")
    #     return redirect('cart')



@csrf_exempt
def payment_result(request):
    if request.method == 'POST':
        status = request.POST.get('status', 'FAILED')
        failed_reason = request.POST.get('failedreason', 'No reason provided')
        tran_id = request.POST.get('tran_id', '')

        if status == 'VALID':
            # Payment successful
            messages.success(request, f"Payment was successful for transaction ID: {tran_id}")
            return render(request, 'payment_result.html', {'status': 'Success', 'username': request.user.username})
        else:
            # Payment failed or was canceled
            messages.error(request, f"Payment failed: {failed_reason}")
            return render(request, 'payment_result.html', {'status': 'Failed', 'username': request.user.username, 'reason': failed_reason})

    return JsonResponse({'error': 'Invalid request method'}, status=405)




# Further.....





