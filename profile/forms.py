import re
from django import forms
from urllib.parse import urljoin
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from phonenumber_field.formfields import PhoneNumberField
from djangoyearlessdate.forms import YearlessDateField, YearlessDateSelect

from profile import models


class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    password2 = forms.CharField(
        label='Repeat password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
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


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = (models.Profile)
        fields = ['title', 'kind', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Profile title',
                'class': 'form-control mb-3'
            }),
            'kind': forms.Select(attrs={
                'class': 'form-select mb-3'
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Profile description',
                'rows': 2,
                'class': 'form-control'
            }),
        }


class ProfileDetailEditForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = [
            'prefix',
            'first_name',
            'middle_name',
            'last_name',
            'suffix',
            'nickname',
            'headline',
            'location',
            'about',
        ]
        widgets = {
            'prefix': forms.TextInput(attrs={
                'autocomplete': 'honorific-prefix',
                'size': 6,
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'autocomplete': 'given-name',
                'size': 12,
                'class': 'form-control'
            }),
            'middle_name': forms.TextInput(attrs={
                'autocomplete': 'additional-name',
                'size': 12,
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'autocomplete': 'family-name',
                'size': 12,
                'class': 'form-control'
            }),
            'suffix': forms.TextInput(attrs={
                'autocomplete': 'honorific-suffix',
                'size': 6,
                'class': 'form-control'
            }),
            'nickname': forms.TextInput(attrs={
                'size': 15,
                'class': 'form-control'
            }),
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'You in a sentence',
            }),
            'location': forms.TextInput(attrs={
                'size': 30,
                'class': 'form-control'
            }),
            'about': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'You in a paragraph',
            }),
        }


class ProfileSelectContentForm(forms.Form):
    model_choice = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'asdf'}),
        required=False,
    )

    def __init__(self, qs, label=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['model_choice'].queryset = qs
        if label:
            self.fields['model_choice'].label = label


class ProfileImgEditForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ('photo',)


class BootstrapModelFormMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            if issubclass(self.fields[field].__class__, forms.SelectMultiple):
                pass
            elif issubclass(self.fields[field].__class__, forms.Select):
                self.fields[field].widget.attrs.update({'class': 'form-select'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class UserEditEmailForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('email',)
        widgets = {
            'email': forms.EmailInput(attrs={
                'autocomplete': 'email',
                'size': 30,
                'class': 'form-control'
            }),
        }


class EmailCreateUpdateForm(BootstrapModelFormMixin):
    class Meta:
        model = models.Email
        fields = ('email_address', 'label', 'type')
        widgets = {
            'email_address': forms.EmailInput(attrs={
                'autocomplete': 'email',
                'size': 30,
            }),
            'label': forms.TextInput(),
            'type': forms.Select(),
        }


class PhoneCreateUpdateForm(BootstrapModelFormMixin):
    class Meta:
        model = models.Phone
        fields = ('phone_number', 'label', 'type')
        widgets = {
            # todo: fix phone input
            # 'phone_number': PhoneNumberField(
            # #     attrs={
            # #     'autocomplete': 'tel',
            # # }
            # ),
            'label': forms.TextInput(),
            'type': forms.Select(),
        }


class AddressCreateUpdateForm(BootstrapModelFormMixin):
    class Meta:
        model = models.Address
        fields = (
            'street1',
            'street2',
            'city',
            'state',
            'zip',
            'country',
            'label',
            'type',
        )
        widgets = {
            'street1': forms.TextInput(attrs={
                'autocomplete': 'address-line1',
            }),
            'street2': forms.TextInput(attrs={
                'autocomplete': 'address-line2',
            }),
            'city': forms.TextInput(attrs={
                'autocomplete': 'address-level2',
            }),
            'state': forms.TextInput(attrs={
                'autocomplete': 'address-level1',
            }),
            'zip': forms.TextInput(attrs={
                'autocomplete': 'postal-code',
            }),
            'country': forms.TextInput(attrs={
                'autocomplete': 'country',
            }),
            'label': forms.TextInput(),
            'type': forms.Select(),
        }


class LinkCreateUpdateForm(BootstrapModelFormMixin):
    class Meta:
        model = models.Link
        fields = ('linkbase', 'label', 'url',)
        widgets = {
            'url': forms.TextInput(attrs={
                'aria-describedby': 'basic-addon3 basic-addon4', 
            }),
            'linkbase': forms.HiddenInput,
        }

    def clean(self):
        cleaned_data = super().clean()
        # todo: separate logic for generic web link
        cleaned_url = cleaned_data['url'].lstrip('/')
        if cleaned_data['linkbase'].pk == 1:
            if re.search('\w+://', cleaned_url):
                full_url = cleaned_url
            else:
                full_url = 'https://' + cleaned_url
        else:
            # todo: will still accept stuff like https://github.com/https://asdf.com/
            full_url = cleaned_data['linkbase'].domain + cleaned_url
        validator = URLValidator()
        try:
            validator(full_url)
        except ValidationError as e:
            msg = f'{full_url} is not a valid url.'
            self.add_error('url', msg)
        cleaned_data['url'] = cleaned_url
        return cleaned_data


class MediaCreateUpdateForm(BootstrapModelFormMixin):
    class Meta:
        model = models.Media
        fields = ('label', 'media_type', 'url', 'file',)
        widgets = {
            'media_type': forms.HiddenInput,
        }

    # todo: def save where only allow one of url or file


# class CardEditForm(forms.ModelForm):
#     class Meta:
#         model = Card
#         fields = (
#             'kind',
#             'prefix', 'first_name', 'middle_name', 'last_name', 'suffix', 'nickname',
#             'birthday', 'birthday_year', 'anniversary', 'anniversary_year',
#             'note'
#         )
#         widgets = {
#             'prefix': forms.TextInput(attrs={
#                 'autocomplete': 'honorific-prefix',
#                 'size': 6,
#                 'class': 'form-control'
#             }),
#             'first_name': forms.TextInput(attrs={
#                 'autocomplete': 'given-name',
#                 'size': 12,
#                 'class': 'form-control'
#             }),
#             'middle_name': forms.TextInput(attrs={
#                 'autocomplete': 'additional-name',
#                 'size': 12,
#                 'class': 'form-control'
#             }),
#             'last_name': forms.TextInput(attrs={
#                 'autocomplete': 'family-name',
#                 'size': 12,
#                 'class': 'form-control'
#             }),
#             'suffix': forms.TextInput(attrs={
#                 'autocomplete': 'honorific-suffix',
#                 'size': 6,
#                 'class': 'form-control'
#             }),
#             'nickname': forms.TextInput(attrs={
#                 'size': 15,
#                 'class': 'form-control'
#             }),
#             'note': forms.Textarea(attrs={'class': 'form-control'}),
#         }
#
#
# class AddressForm(forms.ModelForm):
#     class Meta:
#         model = Address
#         fields = ['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country']
#         widgets = {
#             'street1': forms.TextInput(attrs={'autocomplete': 'address-line1'}),
#             'street2': forms.TextInput(attrs={'autocomplete': 'address-line2'}),
#             'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
#             'state': forms.TextInput(attrs={'autocomplete': 'address-level1'}),
#             'zip': forms.TextInput(attrs={'autocomplete': 'postal-code'}),
#             'country': forms.TextInput(attrs={'autocomplete': 'country'}),
#         }
#
#
# AddressFormSet = inlineformset_factory(
#     Card,
#     Address,
#     form=AddressForm,
#     fields=['address_type', 'street1', 'street2', 'city', 'state', 'zip', 'country'],
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class PhoneForm(forms.ModelForm):
#     class Meta:
#         model = Phone
#         fields = ['phone_type', 'phone_number']
#         widgets = {
#             'phone_number': forms.TextInput(attrs={'autocomplete': 'tel'}),
#         }
#
#
# PhoneFormSet = inlineformset_factory(
#     Card,
#     Phone,
#     form=PhoneForm,
#     fields=['phone_type', 'phone_number'],
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class EmailForm(forms.ModelForm):
#     class Meta:
#         model = Email
#         fields = ['email_type', 'email_address']
#         widgets = {
#             'email_address': forms.EmailInput(attrs={'autocomplete': 'email'}),
#         }
#
#
# EmailFormSet = inlineformset_factory(
#     Card,
#     Email,
#     form=EmailForm,
#     fields=['email_type', 'email_address'],
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class TitleForm(forms.ModelForm):
#     class Meta:
#         model = Title
#         fields = ('title',)
#
#
# TitleFormSet = inlineformset_factory(
#     Card,
#     Title,
#     form=TitleForm,
#     fields=('title',),
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class RoleForm(forms.ModelForm):
#     class Meta:
#         model = Role
#         fields = ('role',)
#
#
# RoleFormSet = inlineformset_factory(
#     Card,
#     Role,
#     form=RoleForm,
#     fields=('role',),
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class OrgForm(forms.ModelForm):
#     class Meta:
#         model = Org
#         fields = ('organization',)
#
#
# OrgFormSet = inlineformset_factory(
#     Card,
#     Org,
#     form=OrgForm,
#     fields=('organization',),
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class TagForm(forms.ModelForm):
#     class Meta:
#         model = Tag
#         fields = ('tag',)
#
#
# TagFormSet = inlineformset_factory(
#     Card,
#     Tag,
#     form=TagForm,
#     fields=('tag',),
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
# class UrlForm(forms.ModelForm):
#     class Meta:
#         model = Url
#         fields = ['url_type', 'url', 'label']
#
#
# UrlFormSet = inlineformset_factory(
#     Card,
#     Url,
#     form=UrlForm,
#     fields=['url_type', 'url', 'label'],
#     extra=1,
#     min_num=0,
#     can_delete=True
# )
#
#
#
#
# class ProfileEditForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ['title', 'description']
#         widgets = {
#             'title': forms.TextInput(attrs={
#                 'class': 'form-control',
#             }),
#             'description': forms.TextInput(attrs={
#                 'placeholder': 'Description',
#                 'class': 'form-control',
#             }),
#         }
#
#
# class ImportCardForm(forms.Form):
#     file = forms.FileField()
