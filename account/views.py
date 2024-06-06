from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth import get_user_model
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View

from .models import (
    Profile,
    EmailAddress,
    Phone,
    PostalAddress,
    SocialProfile,
)
from .forms import (
    UserRegistrationForm,
    UserEditForm,
    ProfileEditForm,
    EmailAddressFormSet,
    PhoneFormSet,
    PostalAddressFormSet,
    SocialProfileFormset,
)


@login_required
def dashboard(request):
    emails = EmailAddress.objects.filter(user=request.user)
    phones = Phone.objects.filter(user=request.user)
    addresses = PostalAddress.objects.filter(user=request.user)
    socials = SocialProfile.objects.filter(user=request.user)
    return render(request,
                  'account/dashboard.html',
                  {'section': 'dashboard',
                   'emails': emails,
                   'phones': phones,
                   'addresses': addresses,
                   'socials': socials})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            # Create the user profile
            Profile.objects.create(user=new_user)
            return render(
                request,
                'account/register_done.html',
                {'new_user': new_user},
            )
    else:
        user_form = UserRegistrationForm()
    return render(
        request,
        'account/register.html',
        {'user_form': user_form}
    )


class EditDashboardView(TemplateResponseMixin, View):
    template_name = 'account/edit.html'

    user = None
    user_profile = None
    files = None

    def get_user_form(self, data=None):
        return UserEditForm(instance=self.user, data=data)

    def get_profile_form(self, data=None, files=None):
        return ProfileEditForm(
            instance=self.user_profile, data=data, files=files
        )

    def get_email_formset(self, data=None):
        return EmailAddressFormSet(instance=self.user, data=data)

    def get_phone_formset(self, data=None):
        return PhoneFormSet(instance=self.user, data=data)

    def get_address_formset(self, data=None):
        return PostalAddressFormSet(instance=self.user, data=data)

    def get_socials_formset(self, data=None):
        return SocialProfileFormset(instance=self.user, data=data)

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        # todo: should create a user profile if fails to find one
        self.user_profile = get_object_or_404(
            Profile, user=self.user
        )
        self.files = request.FILES
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        user_form = self.get_user_form()
        profile_form = self.get_profile_form()
        email_formset = self.get_email_formset()
        phone_formset = self.get_phone_formset()
        address_formset = self.get_address_formset()
        socials_formset = self.get_socials_formset()
        return self.render_to_response(
            {'user_form': user_form,
             'profile_form': profile_form,
             'email_formset': email_formset,
             'phone_formset': phone_formset,
             'address_formset': address_formset,
             'socials_formset': socials_formset}
        )

    def post(self, request, *args, **kwargs):
        user_form = self.get_user_form(data=request.POST)
        profile_form = self.get_profile_form(data=request.POST, files=self.files)
        email_formset = self.get_email_formset(data=request.POST)
        phone_formset = self.get_phone_formset(data=request.POST)
        address_formset = self.get_address_formset(data=request.POST)
        socials_formset = self.get_socials_formset(data=request.POST)
        if (
            user_form.is_valid()
            and profile_form.is_valid()
            and email_formset.is_valid()
            and phone_formset.is_valid()
            and address_formset.is_valid()
            and socials_formset.is_valid()
        ):
            user_form.save()
            profile_form.save()
            email_formset.save()
            phone_formset.save()
            address_formset.save()
            socials_formset.save()
            return redirect('dashboard')
        return self.render_to_response(
            {'user_form': user_form,
             'profile_form': profile_form,
             'email_formset': email_formset,
             'phone_formset': phone_formset,
             'address_formset': address_formset,
             'socials_formset': socials_formset}
        )


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(
            instance=request.user,
            data=request.POST
        )
        profile_form = ProfileEditForm(
            instance=request.user.profile,
            data=request.POST,
            files=request.FILES,
        )
        email_formset = EmailAddressFormSet(
            queryset=EmailAddress.objects.filter(user=request.user),
            instance=request.user.email_addresses,
            data=request.POST
        )
        phone_formset = PhoneFormSet(
            queryset=Phone.objects.filter(user=request.user),
            data=request.POST
        )
        address_formset = PhoneFormSet(
            queryset=PostalAddress.objects.filter(user=request.user),
            data=request.POST
        )
        if (
            user_form.is_valid()
            and profile_form.is_valid()
            and email_formset.is_valid()
            and phone_formset.is_valid()
            and address_formset.is_valid()
        ):
            user_form.save()
            profile_form.save()
            email_formset.save()
            phone_formset.save()
            address_formset.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        email_formset = EmailAddressFormSet(
            # queryset=EmailAddress.objects.filter(user=request.user)
            instance=request.user.email_addresses
        )
        phone_formset = PhoneFormSet(queryset=Phone.objects.filter(user=request.user))
        address_formset = PostalAddressFormSet(queryset=PostalAddress.objects.filter(user=request.user))
    return render(
        request,
        'account/edit.html',
        {'user_form': user_form,
         'profile_form': profile_form,
         'email_formset': email_formset,
         'phone_formset': phone_formset,
         'address_formset': address_formset}
    )


@login_required
def user_list(request):
    users = get_user_model().objects.filter(is_active=True)
    return render(
        request,
        'account/user/list.html',
        {'section': 'people',
         'users': users}
    )


@login_required
def user_detail(request, username):
    user = get_object_or_404(get_user_model(),
                             username=username,
                             is_active=True)
    return render(
        request,
        'account/user/detail.html',
        {'section': 'people',
         'user': user}
    )
