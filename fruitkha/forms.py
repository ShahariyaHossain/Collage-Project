from django import forms
from django.core.exceptions import ValidationError
from .models import Account

class SignUpForm(forms.ModelForm):
    # Additional fields for validation
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Account
        fields = ['name', 'email', 'phone', 'password', 'password_confirm']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Account.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please use another.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        phone = cleaned_data.get("phone")

        # Password match validation
        if password != password_confirm:
            raise ValidationError("Passwords do not match.")

        # Phone validation (ensure regex in model is respected)
        if not phone or not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        
        return cleaned_data
