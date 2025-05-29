from django import forms
from django.contrib.auth.models import User
from database.manga.models import Manga, Volume, Chapter
from django.core.exceptions import ValidationError

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control border-top-0 border-left-0 border-right-0 rounded-0 bg-transparent text-white', 'required': True})
    )
    password_repeat = forms.CharField(
        label="Repeat Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control border-top-0 border-left-0 border-right-0 rounded-0 bg-transparent text-white', 'required': True})
    )

    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control border-top-0 border-left-0 border-right-0 rounded-0 bg-transparent text-white', 'required': True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")

        if password and password_repeat and password != password_repeat:
            self.add_error('password_repeat', "Passwords do not match.")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'class': 'form-control border-top-0 border-left-0 border-right-0 rounded-0 bg-transparent text-white', 'required': True})
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control border-top-0 border-left-0 border-right-0 rounded-0 bg-transparent text-white', 'required': True})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Invalid username or password.")
            cleaned_data['user'] = user  # So the view can use it

        return cleaned_data
    

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']