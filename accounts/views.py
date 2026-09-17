from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from orders.models import Order

from .forms import (
    AddressForm,
    RegisterForm,
    TommyAuthenticationForm,
)
from .models import Address


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            auth_login(request, user)

            messages.success(
                request,
                f"Welcome to TOMMY.X, {user.username}!"
            )

            # -------------------------------------------------
            # Preserve Buy Now / checkout flow
            # -------------------------------------------------
            next_url = request.POST.get("next", "").strip()

            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            # Normal registration
            return redirect("accounts:profile")

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


class TommyLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = TommyAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        """
        Preserve the original destination after login.

        Example:
        Buy Now
            ↓
        Login
            ↓
        Successful login
            ↓
        Checkout
        """

        redirect_to = self.request.POST.get(
            "next",
            ""
        ).strip()

        if redirect_to and url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect_to

        redirect_to = self.request.GET.get(
            "next",
            ""
        ).strip()

        if redirect_to and url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return redirect_to

        return reverse("accounts:profile")


class TommyLogoutView(LogoutView):
    next_page = "core:home"


@login_required
def profile_view(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .order_by("-created_at")[:5]
    )

    addresses = request.user.addresses.all()

    return render(
        request,
        "accounts/profile.html",
        {
            "orders": orders,
            "addresses": addresses,
        },
    )


@login_required
def address_list(request):
    addresses = request.user.addresses.all()

    return render(
        request,
        "accounts/addresses.html",
        {
            "addresses": addresses,
        },
    )


@login_required
def address_add(request):
    if request.method == "POST":
        form = AddressForm(request.POST)

        if form.is_valid():
            address = form.save(commit=False)

            address.user = request.user

            # -------------------------------------------------
            # If this address is default,
            # remove default status from other addresses
            # -------------------------------------------------
            if address.is_default:
                request.user.addresses.update(
                    is_default=False
                )

            address.save()

            messages.success(
                request,
                "Address saved."
            )

            return redirect(
                "accounts:addresses"
            )

    else:
        form = AddressForm()

    return render(
        request,
        "accounts/address_form.html",
        {
            "form": form,
        },
    )


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(
        Address,
        pk=pk,
        user=request.user,
    )

    address.delete()

    messages.info(
        request,
        "Address removed."
    )

    return redirect(
        "accounts:addresses"
    )