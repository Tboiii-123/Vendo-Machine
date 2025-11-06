
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import  Product,UserSession
from .serializers import UserCreateSerializer, ProductSerializer

from .utils import COINS, calc_change
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate





    
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):

    serializer =UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        return Response({
            "data": serializer.data
        }, status =201)
    
    return Response({
        "error":serializer.errors
    }, status=400)

    


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")
    user = authenticate(request, username=email, password=password)
    
    if not user:
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check for existing session
    if UserSession.objects.filter(user=user).exists():
        return Response({"message": "There is already an active session using your account"}, status=status.HTTP_403_FORBIDDEN)
    
    # Create token
    refresh = RefreshToken.for_user(user)
    
    # Save session
    UserSession.objects.create(
        user=user,
        refresh_token=str(refresh),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        ip_address=request.META.get('REMOTE_ADDR')
    )
    

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view(request):
    user = request.user

    return Response({
        'id':user.id,
        'user_name':user.user_name,
        "email":user.email,
        "role":user.role,
        "deposit":user.deposit

    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):

    user =request.user

    if user.role =="buyer":

        coin =request.data.get('coin')

        try:
            coin =int(coin)
            if coin not in COINS:
                return Response({"detail": f"Coin must be one of {COINS}"},status=status.HTTP_400_BAD_REQUEST)
            
        except ValueError:
            return Response({"detail": "Invalid coin format."}, status=status.HTTP_400_BAD_REQUEST)
    
        user.deposit +=coin
        user.save(update_fields=['deposit'])
        return Response({'deposit': user.deposit}, status=status.HTTP_200_OK)
    
    return Response(
        {"detail": "Only buyers can deposit."},
        status=status.HTTP_403_FORBIDDEN
    )






#Product View
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_create(request):

    user =request.user

    if user.role =='seller':
            

        data = request.data.copy()   
        data['seller'] = user.id     

        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        "message":"User Permission denied"
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
def product_view(request):

    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)

    return Response({
        "data":serializer.data
    })




#Update,Delete product
@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_update(request,pk):

    
        
    
    user =request.user

    if user.role =='seller':
        product =get_object_or_404(Product, pk=pk, seller =request.user)
    
            

        if request.method == 'PUT' or request.method == 'PATCH':

            serializer = ProductSerializer(product, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Product updated", "data": serializer.data}, status=status.HTTP_200_OK)
            

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            

            product.delete()
            return Response({"message": "Product deleted successfully"}, status=status.HTTP_200_OK)



        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    return Response({
        "message":"User Permission denied"
    
    }, status=status.HTTP_403_FORBIDDEN)

    







#Buy Enndpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])

def buy_view(request):

    user =request.user

    if user.role =='buyer':
            


        product_id =request.data.get('product_id')
        amount =int(request.data.get('amount',1))

        try:
            amount = int(amount)
            if amount <= 0:
                return Response({'detail': 'Amount must be a positive integer'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'detail': 'Amount must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

   
        if not product_id:
            return Response({'detail': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)


        product =get_object_or_404(Product,pk=product_id)
        total_cost =product.cost * amount

        if product.amount_available< amount:
            return Response({'detail':'Not enough product available'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.deposit < total_cost:
            return Response({'detail':'Insufficient deposit'}, status=status.HTTP_400_BAD_REQUEST)

        #Updating the product

        product.amount_available -=amount
        product.save(update_fields=['amount_available'])

        user.deposit -= total_cost
        user.save(update_fields=['deposit'])

        change =calc_change(user.deposit)
        spent =total_cost

        order ={
            'product_id':product.id,
            'product_name':product.product_name,
            'amount':amount,
            'cost_each':product.cost,
            'total_cost':total_cost
        }
        return_change =change
        return Response({
        'total_spent':spent,
        'product':order,
        'change':return_change

    }, status=status.HTTP_200_OK)

        
    return Response({'detail':'Only buyers can buy'}, status=status.HTTP_403_FORBIDDEN)


    
       




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_deposit(request):

    user =request.user

    if user.role !='buyer':
        return Response({"detail": "Only buyers can reset deposit"}, status=status.HTTP_403_FORBIDDEN)
        


    user.deposit =0

    user.save(update_fields=['deposit'])

    return Response({"message": "Deposit reset successfully"}, status=status.HTTP_200_OK)
    






    



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_all_view(request):
    UserSession.objects.filter(user=request.user).delete()
    return Response({"message": "Session Terminated"})
