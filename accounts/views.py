from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from orders.models import Order
from .forms import AddressForm, RegisterForm
from .models import Address


def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f'Welcome to TOMMY.X, {user.username}!')
            return redirect('accounts:profile')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class TommyLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class TommyLogoutView(LogoutView):
    next_page = 'core:home'


@login_required
def profile_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = request.user.addresses.all()
    return render(request, 'accounts/profile.html', {'orders': orders, 'addresses': addresses})


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.update(is_default=False)
            address.save()
            messages.success(request, 'Address saved.')
            return redirect('accounts:addresses')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form})


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, 'Address removed.')
    return redirect('accounts:addresses')
