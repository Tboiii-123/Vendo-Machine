from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=20,  unique=True,null=False, blank=False)
    user_name =models.CharField(max_length=20,  unique=True, blank=False, null=False)
    ROLE_CHOICES = (("buyer", "Buyer"), ("seller", "Seller"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    deposit = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"  # This tells Django to use email for login
    REQUIRED_FIELDS = ["user_name","role"]  # Required when creating superuser

    


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    amount_available = models.PositiveIntegerField()
    cost = models.PositiveIntegerField()  # cents, multiple of 5
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    

    def __str__(self):
        return f"{self.product_name} ({self.amount_available}) @ {self.cost}c"
    






class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255, unique=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)