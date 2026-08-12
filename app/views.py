from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages

def login(request):
    error = None
    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Support login via Username OR Email
        user_obj = User.objects.filter(username__iexact=login_input).first() or User.objects.filter(email__iexact=login_input).first()
        username = user_obj.username if user_obj else login_input

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                error = "This account is disabled. Please contact system administrator."
        else:
            error = "Invalid username/email or password. Please try again."
            
    return render(request, 'register/login.html', {'error': error})

def forgot_password(request):
    message = None
    error = None
    if request.method == 'POST':
        identity = request.POST.get('identity', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        user_obj = User.objects.filter(username__iexact=identity).first() or User.objects.filter(email__iexact=identity).first()
        
        if not user_obj:
            error = "No account found with the provided username or email address."
        elif new_password != confirm_password:
            error = "Passwords do not match. Please try again."
        elif len(new_password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            user_obj.set_password(new_password)
            user_obj.save()
            message = f"Password for user '{user_obj.username}' has been reset successfully! You can now log in below."

    return render(request, 'register/forgot_password.html', {'message': message, 'error': error})

def dashboard(request):
    return render(request, 'dashboard.html', {'active_menu': 'dashboard'})
