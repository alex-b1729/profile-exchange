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
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Repeat password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    class Meta:
        model = get_user_model()
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'})
        }

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
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'email': forms.TextInput(attrs={'autocomplete': 'email'}),
        }


class UserEditEmailForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('prefix', 'middle_name', 'suffix', 'nick_name',
                  'photo', 'home_page', 'headline', 'location',
                  'organization', 'title', 'role', 'work_url',
                  'birthday', 'anniversary',
                  'sex', 'gender')
        widgets = {
            'prefix': forms.TextInput(attrs={'autocomplete': 'honorific-prefix'}),
            'middle_name': forms.TextInput(attrs={'autocomplete': 'additional-name'}),
            'suffix': forms.TextInput(attrs={'autocomplete': 'honorific-suffix'}),
            'nick_name': forms.TextInput(attrs={'autocomplete': 'nickname'}),
            'organization': forms.TextInput(attrs={'autocomplete': 'organization'}),
            'title': forms.TextInput(attrs={'autocomplete': 'organization-title'}),
            'birthday': forms.TextInput(attrs={'autocomplete': 'bday'}),
            'gender': forms.TextInput(attrs={'autocomplete': 'sex'}),
        }


class EmailAddressForm(forms.ModelForm):
    class Meta:
        model = EmailAddress
        fields = ['email_type', 'email_address', 'is_primary']
        widgets = {
            'email_address': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }


EmailAddressFormSet = inlineformset_factory(
    get_user_model(),
    EmailAddress,
    form=EmailAddressForm,
    fields=['email_type', 'email_address', 'is_primary'],
    extra=1,
    min_num=0,
    can_delete=True
)


class PhoneForm(forms.ModelForm):
    class Meta:
        model = Phone
        fields = ['phone_number', 'phone_type']
        widgets = {
            'phone_number': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }


PhoneFormSet = inlineformset_factory(
    get_user_model(),
    Phone,
    form=PhoneForm,
    fields=['phone_number', 'phone_type'],
    extra=1,
    min_num=0,
    can_delete=True
)


class PostalAddressForm(forms.ModelForm):
    class Meta:
        model = PostalAddress
        fields = ['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country']
        widgets = {
            'street1': forms.TextInput(attrs={'autocomplete': 'address-line1'}),
            'street2': forms.TextInput(attrs={'autocomplete': 'address-line2'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'autocomplete': 'address-level1'}),
            'zip': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
            'country': forms.TextInput(attrs={'autocomplete': 'country'}),
        }


PostalAddressFormSet = inlineformset_factory(
    get_user_model(),
    PostalAddress,
    form=PostalAddressForm,
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
