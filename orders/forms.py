from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    address_line1 = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address_line2 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
