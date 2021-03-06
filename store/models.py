from uuid import uuid4

from django.conf import settings
from django.contrib import admin
from django.db import models

User = settings.AUTH_USER_MODEL

class Collection(models.Model):
    title       = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.title

class Product(models.Model):
    title       = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    unit_price  = models.DecimalField(max_digits=6, decimal_places=2)
    inventory   = models.IntegerField()
    last_update = models.DateTimeField(auto_now=True)
    collection  = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name='products')

    def __str__(self) -> str:
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='store/images')

class Customer(models.Model):
    MEMBERSHIP_BRONZE = 'B'
    MEMBERSHIP_SILVER = 'S'
    MEMBERSHIP_GOLD = 'G'

    MEMBERSHIP_CHOICES = [
        (MEMBERSHIP_BRONZE, 'Bronze'),
        (MEMBERSHIP_SILVER, 'Silver'),
        (MEMBERSHIP_GOLD, 'Gold'),
    ]
    phone = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    membership = models.CharField(
        max_length=1, choices=MEMBERSHIP_CHOICES, default=MEMBERSHIP_BRONZE)
    user        = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'
    
    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name

    class Meta:
        ordering = ['user__first_name', 'user__last_name']
    
    

class Cart(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid4)
    created_at  = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart        = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity    = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = [['cart', 'product']]


class Order(models.Model):
    PAYMENT_STATUS_PENDING = 'P'
    PAYMENT_STATUS_COMPLETE = 'C'
    PAYMENT_STATUS_FAILED = 'F'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, 'Pending'),
        (PAYMENT_STATUS_COMPLETE, 'Complete'),
        (PAYMENT_STATUS_FAILED, 'Failed')
    ]
    placed_at   = models.DateTimeField(auto_now_add=True)
    address     = models.TextField(blank=False)
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)

class OrderItem(models.Model):
    order       = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity    = models.PositiveSmallIntegerField()
    unit_price  = models.DecimalField(max_digits=6, decimal_places=2)
