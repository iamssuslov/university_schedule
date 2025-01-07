from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        try:
            validate_password(password) 
        except ValidationError as e:
            self.add_error('password1', e)
        return password

    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'password1', 'password2')
