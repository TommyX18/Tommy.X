from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, UserProfile


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email address",
                "autocomplete": "email",
            }
        ),
    )

    phone = forms.CharField(
        required=True,
        max_length=10,
        min_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter 10-digit mobile number",
                "inputmode": "numeric",
                "autocomplete": "tel",
                "maxlength": "10",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Choose a username",
                "autocomplete": "username",
            }
        )

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Create a password",
                "autocomplete": "new-password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm your password",
                "autocomplete": "new-password",
            }
        )

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        # Keep numbers only
        phone = "".join(
            character
            for character in phone
            if character.isdigit()
        )

        # Must be exactly 10 digits
        if len(phone) != 10:
            raise forms.ValidationError(
                "Enter a valid 10-digit mobile number."
            )

        # Indian mobile numbers normally start with 6, 7, 8, or 9
        if not phone.startswith(("6", "7", "8", "9")):
            raise forms.ValidationError(
                "Enter a valid Indian mobile number."
            )

        # Prevent duplicate phone numbers
        if UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "This phone number is already registered."
            )

        return phone

    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            UserProfile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
            )

        return user


class TommyAuthenticationForm(AuthenticationForm):
    """
    Allows users to login using either:

    1. Username + Password
    2. Phone Number + Password
    """

    username = forms.CharField(
        label="Username or Phone Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username or phone number",
                "autocomplete": "username",
            }
        ),
    )

    def clean(self):
        username_or_phone = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if not username_or_phone or not password:
            return super().clean()

        username_or_phone = username_or_phone.strip()

        # Start with the entered value as username
        login_username = username_or_phone

        # Remove non-digit characters to check for a phone number
        phone = "".join(
            character
            for character in username_or_phone
            if character.isdigit()
        )

        # If it looks like an Indian 10-digit mobile number,
        # find the related UserProfile
        if len(phone) == 10 and phone.startswith(("6", "7", "8", "9")):

            profile = (
                UserProfile.objects
                .select_related("user")
                .filter(phone=phone)
                .first()
            )

            if profile:
                login_username = profile.user.username

        # Authenticate using the resolved username
        user = authenticate(
            self.request,
            username=login_username,
            password=password,
        )

        if user is None:
            raise forms.ValidationError(
                "Invalid username/phone number or password."
            )

        if not user.is_active:
            raise forms.ValidationError(
                "This account is inactive."
            )

        self.confirm_login_allowed(user)

        self.user_cache = user

        return self.cleaned_data


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address

        fields = [
            "full_name",
            "phone",
            "line1",
            "line2",
            "city",
            "state",
            "pincode",
            "is_default",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full name",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                    "inputmode": "numeric",
                    "maxlength": "15",
                }
            ),

            "line1": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Address line 1",
                }
            ),

            "line2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Address line 2 (optional)",
                }
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "City",
                }
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "State",
                }
            ),

            "pincode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "PIN code",
                    "inputmode": "numeric",
                    "maxlength": "6",
                }
            ),

            "is_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }