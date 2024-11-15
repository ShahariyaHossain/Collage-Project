from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),  # Root URL for this app
    path('news/', views.news_list, name = 'news-list'),
    path('news/<slug:slug>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('products/', views.products_list, name='product-list'),
    re_path(r'^product/(?P<slug>[\w-]+)/$', views.SingleProductView.as_view(), name='single-product'),
    # path('cart/', views.CartView.as_view(), name='cart'),
    # path('home/', views.home_1, name='home_1'),  # Root URL for this app
    # path('signup/', views.signup, name='signup'),  # /Sign-Up/ URL
    # path('login/', views.login, name = 'login'),
    # path('animated_bg/', views.animated_bg, name = 'animate'),
    # path('shoping-cart/', views.shoping_cart, name='shoping-cart'),
    # path('success/', views.success, name='success_page'),  # /Succes/ URL
]
