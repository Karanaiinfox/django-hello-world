
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import random

User = get_user_model()


def login_view(request):
    
    
    # Check if the request method is POST
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(username=username, password=password)
        print(username, password,'-----------=======================',user)
        # If the user is authenticated
        if user is not None:
            login(request, user)
            
            # Get the 'next' parameter from the request
            next_url = request.GET.get('next')
            print(next_url,"login view---------------------")
            # Redirect to the 'next' URL if it exists, otherwise redirect to home
            return redirect(next_url if next_url else '../')
        else:
            messages.error(request, "Invalid username or password.")
    
    # Render the login page
    return render(request, "login.html")

def logout_view(request):     
    logout(request)
    return redirect("main:login")


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        company= request.POST.get('company')
        print(username,email,password,password_confirm,company)

        # Validate passwords
        if password != password_confirm:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)

        # Check if the user already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already taken'}, status=400)

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=make_password(password),company=company,company_id=random.randint(000000000000,100000000000))
        return JsonResponse({'success': 'User created successfully!'}, status=201)
    return render(request, 'signup.html')

