
from django.urls import path
from . import views


urlpatterns = [
    path('', views.swagger_view, name='swagger'),
    path('old-index/', views.index_view, name='index'),


    path('categories/', views.categories_view, name='categories'),
    path('products/', views.products_view, name='products'),
    path('product/<int:product_id>/', views.product_view, name='product'),
    path('buy/', views.buy_view, name='buy'),



    path('categories', views.categories_view),
    path('products', views.products_view),
    path('product/<int:product_id>', views.product_view),
    path('buy', views.buy_view),
]