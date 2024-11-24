from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),  # Root URL for this app
    path('news/', views.news_list, name = 'news-list'),
    path('news/<slug:slug>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('products/', views.products_list, name='product-list'),
    re_path(r'^product/(?P<slug>[\w-]+)/$', views.SingleProductView.as_view(), name='single-product'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('init-payment/', views.PaymentInitView.as_view(), name='init_payment'),
    path('payment-result/', views.PaymentResultView.as_view(), name='payment_result'),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    # path('home/', views.home_1, name='home_1'),  # Root URL for this app
    path('signup-b/', views.signup_b, name='signup-b'),  # /Sign-Up _b/ URL
    path('login-b/', views.login_b, name = 'login-b'),
    # path('animated_bg/', views.animated_bg, name = 'animate'),
    # path('shoping-cart/', views.shoping_cart, name='shoping-cart'),
    # path('success/', views.success, name='success_page'),  # /Succes/ URL
]
