from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth import get_user_model

from .models import (
    Profile,
    EmailAddress,
    Phone,
    PostalAddress,
    SocialProfile,
)


class LoginForm(forms.Form):
    email = forms.CharField()
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
        fields = ['username', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']

    def clean_email(self):
        data = self.cleaned_data['email']
        if get_user_model().objects.filter(email=data).exists():
            raise forms.ValidationError('Email is already registered.')
        return data

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


class UserEditNameForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email')


class UserEditEmailForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email',)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('prefix', 'middle_name', 'suffix', 'nick_name',
                  'photo', 'home_page', 'headline', 'location',
                  'organization', 'title', 'role', 'work_url',
                  'birthday', 'anniversary',
                  'sex', 'gender')


EmailAddressFormSet = inlineformset_factory(
    get_user_model(),
    EmailAddress,
    fields=['email_type', 'email_address', 'is_primary'],
    extra=1,
    min_num=0,
    can_delete=True
)
PhoneFormSet = inlineformset_factory(
    get_user_model(),
    Phone,
    fields=['phone_number', 'phone_type'],
    extra=1,
    min_num=0,
    can_delete=True
)
PostalAddressFormSet = inlineformset_factory(
    get_user_model(),
    PostalAddress,
    fields=['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country'],
    extra=1,
    min_num=0,
    can_delete=True
)
SocialProfileFormset = inlineformset_factory(
    get_user_model(),
    SocialProfile,
    fields=['url'],
    extra=1,
    min_num=0,
    can_delete=True
)
