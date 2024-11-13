from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile
from django.forms import ModelForm


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(label='Username',
                               widget=forms.TextInput(
                                   attrs={'class': 'form-control', 'placeholder': 'Введите ваш username'}))
    email = forms.EmailField(label='Электронная почта',
                             widget=forms.EmailInput(
                                 attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # Присваиваем пароль в виде хеша

        user.role = 'user'  # Устанавливаем роль по умолчанию
        if commit:
            user.save()
        return user

class EditProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['username', 'email', 'password', 'avatar', 'first_name', 'last_name', 'avatar', 'address', 'phone_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя пользователя'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите свою электронную почту'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вашу фамилию'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Загрузите ваше фото'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш номер телефона'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш адрес'})
        }


