
from  django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
   path('login/', views.login_view, name='login'),


    path('register/', views.register_view, name='register'),

    path('user_view/', views.user_view, name='user_view'),

    path('deposit/', views.deposit, name='deposit'),
   
    path('product_create/', views.product_create, name='product_create'),
   
    path('product_update/<int:pk>', views.product_update, name='product_update'),

   path('product_view/', views.product_view, name='product_view'),

   path('buy_view/', views.buy_view, name='buy_view'),
    
    

    path('reset_deposit/', views.reset_deposit, name='reset_deposit'),

    path('reset/', views.logout_all_view, name='logout_all'),



        
    
    ]

