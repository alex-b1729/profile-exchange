from django import forms
from django.contrib.auth import get_user_model

from .models import Profile, EmailAddress


class LoginForm(forms.Form):
    # todo: authentication using primary / verified email
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Repeat password',
        widget=forms.PasswordInput
    )

    class Meta:
        model = get_user_model()
        fields = ['email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['username', 'password2']

    # def save(self, commit=True):
    #     user = super(UserRegistrationForm, self).save(commit=False)
    #     user.username = user.email
    #     user.save(commit)
    #     email = EmailAddress(
    #         user=user,
    #         email_address=user.email,
    #         is_primary=True
    #     )
    #     email.save(commit)
    #     return user


class UserEditForm(forms.ModelForm):
    # todo: update username on email change?
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email')

    # def save(self, commit=True):
    #     user = super(UserEditForm, self).save(commit=False)
    #     user.username = user.email
    #     email = EmailAddress.objects.get(user=user.pk)
    #     email.email_address = user.email
    #     email.save(commit)
    #     user.save(commit)
    #     return user


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('date_of_birth', 'photo')
