
from rest_framework import serializers
from .models import User, Product

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id','user_name','password','email','role','deposit')
        read_only_fields = ('deposit','id')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user





class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('id','product_name','amount_available','cost','seller')

    def validate_cost(self, value):
        if value % 5 != 0:
            raise serializers.ValidationError('Cost must be a multiple of 5 cents')
        if value <= 0:
            raise serializers.ValidationError('Cost must be positive')
        return value

    
