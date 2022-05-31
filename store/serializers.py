from django.db import transaction
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (Cart, CartItem, Collection, Customer, Order, OrderItem,
                     Product, ProductImage)
from .signals import order_created
from .validators import (validate_file_size, validate_phone,
                         validate_product_title_no_fuck)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        # ...

        return token

class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)
    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']

    def validate_title(self, value):
        qs = Product.objects.filter(title__iexact=value)
        if qs.exists():
            raise serializers.ValidationError(f"{value} is already a collection name.")
        return value

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(validators=[validate_file_size])
    class Meta:
        model = ProductImage
        fields = ['id', 'image']
    
    def create(self, validated_data):
        product_id = self.context['product_id']
        return ProductImage.objects.create(product_id=product_id, **validated_data)

class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(validators=[validate_product_title_no_fuck])
    price = serializers.DecimalField(max_digits=6, decimal_places=2, source='unit_price')
    collection = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all())
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'price', 'inventory', 'collection', 'images']

    def validate_title(self, value):
        qs = Product.objects.filter(title__iexact=value)
        if qs.exists():
            raise serializers.ValidationError(f"{value} is already a product name.")
        return value

class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']

    product_id = serializers.IntegerField()

    def validate_quantity(self, quantity, **kwargs):
        product = Product.objects.get(id=self.initial_data['product_id'])
        if quantity > product.inventory:
            raise serializers.ValidationError('Dont have enough inventory.')
        return quantity


    def validate_product_id(self, value, **kwargs):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError('No product with the given ID was found.')
        return value

    def save(self, **kwargs):
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        product = Product.objects.get(id=product_id)

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            if cart_item.quantity + quantity > product.inventory:
                raise serializers.ValidationError('Dont have enough inventory.')
            else:
                cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)
        
        return self.instance

class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def validate_quantity(self, quantity, **kwargs):
        cart_item_id = self.context['cart_item_id']
        product = Product.objects.get(id=cart_item_id)
        if quantity > product.inventory:
            raise serializers.ValidationError('Dont have enough inventory.')
        return quantity

class CartItemProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']

class CartItemSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField(method_name='get_total_price')
    product = CartItemProductSerializer()
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']

    def get_total_price(self, cartItem:CartItem):
        return cartItem.quantity * cartItem.product.unit_price

class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)                                                                                                                                                                                                                                                                                                                                                                                                                           
    cart_total_price = serializers.SerializerMethodField(method_name='get_cart_total_price')
    class Meta:
        model = Cart
        fields = ['id', 'items', 'cart_total_price']

    def get_cart_total_price(self, cart):
        return sum([item.quantity * item.product.unit_price for item in cart.items.all()])

class UpdateCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['phone', 'birth_date']

class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    phone = serializers.CharField(max_length=10, validators=[validate_phone])

    class Meta:
        model = Customer
        fields = ['id', 'user_id', 'phone', 'birth_date', 'membership']

class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'unit_price']

class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']

class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_total_price = serializers.SerializerMethodField(method_name='get_order_total_price')
    class Meta:
        model = Order
        fields = ['id', 'customer', 'placed_at', 'address', 'payment_status', 'items', 'order_total_price']
    
    def get_order_total_price(self, order):
        return sum([item.quantity * item.product.unit_price for item in order.items.all()])    

class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    address = serializers.CharField(max_length=255)

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(id=cart_id).exists():
            raise serializers.ValidationError('No cart with the given ID was found.')
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError('The cart is empty.')
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer = Customer.objects.get(user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer, address=self.validated_data['address'])
            cart_items = CartItem.objects.select_related('product') \
                                        .filter(cart_id=cart_id)
            order_items = [
                OrderItem(
                    order=order, 
                    product=item.product, 
                    unit_price=item.product.unit_price,
                    quantity=item.quantity
                ) for item in cart_items
            ]

            OrderItem.objects.bulk_create(order_items)

            # update product inventory
            for item in cart_items:
                product = Product.objects.get(id=item.product_id)
                inventory = product.inventory - item.quantity
                Product.objects.filter(id=item.product.id).update(inventory=inventory)

            Cart.objects.filter(id=cart_id).delete()
            
            order_created.send_robust(self.__class__, order=order)

            return order




