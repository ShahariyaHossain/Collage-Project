from django import forms
from django.core.exceptions import ValidationError
from .models import Account

class SignUpForm(forms.ModelForm):
    # Add a confirm password field
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = Account
        fields = ['name', 'email', 'password', 'password_confirm', 'address']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        
        # Check if passwords match
        if password != password_confirm:
            raise ValidationError("Passwords do not match.")
        
        return cleaned_data
