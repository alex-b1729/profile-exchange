from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
from djangoyearlessdate.forms import YearlessDateField, YearlessDateSelect

from .models import (
    Card,
    Address,
    Phone,
    Email,
    Title,
    Role,
    Org,
    Tag,
    Url,
    Profile,
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

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password2'])
        user.save(commit)
        return user


class CardNameForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    class Meta:
        widgets = {
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'})
        }


# class UserEditNameForm(forms.ModelForm):
#     class Meta:
#         model = get_user_model()
#         fields = ('first_name', 'last_name')
#         widgets = {
#             'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
#             'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
#         }


class UserEditEmailForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }


class CardEditForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = (
            'kind',
            'prefix', 'first_name', 'middle_name', 'last_name', 'suffix', 'nickname',
            'photo',
            'birthday', 'birthday_year', 'anniversary', 'anniversary_year',
            'sex', 'gender',
            'note'
        )
        widgets = {
            'prefix': forms.TextInput(attrs={'autocomplete': 'honorific-prefix'}),
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'middle_name': forms.TextInput(attrs={'autocomplete': 'additional-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'suffix': forms.TextInput(attrs={'autocomplete': 'honorific-suffix'}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country']
        widgets = {
            'street1': forms.TextInput(attrs={'autocomplete': 'address-line1'}),
            'street2': forms.TextInput(attrs={'autocomplete': 'address-line2'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'autocomplete': 'address-level1'}),
            'zip': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
            'country': forms.TextInput(attrs={'autocomplete': 'country'}),
        }


AddressFormSet = inlineformset_factory(
    Card,
    Address,
    form=AddressForm,
    fields=['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country'],
    extra=1,
    min_num=0,
    can_delete=True
)


class PhoneForm(forms.ModelForm):
    class Meta:
        model = Phone
        fields = ['phone_type', 'phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'autocomplete': 'tel'}),
        }


PhoneFormSet = inlineformset_factory(
    Card,
    Phone,
    form=PhoneForm,
    fields=['phone_type', 'phone_number'],
    extra=1,
    min_num=0,
    can_delete=True
)


class EmailForm(forms.ModelForm):
    class Meta:
        model = Email
        fields = ['email_type', 'email_address']
        widgets = {
            'email_address': forms.EmailInput(attrs={'autocomplete': 'email'}),
        }


EmailFormSet = inlineformset_factory(
    Card,
    Email,
    form=EmailForm,
    fields=['email_type', 'email_address'],
    extra=1,
    min_num=0,
    can_delete=True
)

class TitleForm(forms.ModelForm):
    class Meta:
        model = Title
        fields = ('value',)


TitleFormSet = inlineformset_factory(
    Card,
    Title,
    form=TitleForm,
    fields=('value',),
    extra=1,
    min_num=0,
    can_delete=True
)


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ('value',)


RoleFormSet = inlineformset_factory(
    Card,
    Role,
    form=RoleForm,
    fields=('value',),
    extra=1,
    min_num=0,
    can_delete=True
)


class OrgForm(forms.ModelForm):
    class Meta:
        model = Org
        fields = ('value',)


OrgFormSet = inlineformset_factory(
    Card,
    Org,
    form=OrgForm,
    fields=('value',),
    extra=1,
    min_num=0,
    can_delete=True
)


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ('tag',)


TagFormSet = inlineformset_factory(
    Card,
    Tag,
    form=TagForm,
    fields=('tag',),
    extra=1,
    min_num=0,
    can_delete=True
)


class UrlForm(forms.ModelForm):
    class Meta:
        model = Url
        fields = ['url_type', 'url', 'label']


UrlFormSet = inlineformset_factory(
    Card,
    Url,
    form=UrlForm,
    fields=['url_type', 'url', 'label'],
    extra=1,
    min_num=0,
    can_delete=True
)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('headline', 'location', 'description')
