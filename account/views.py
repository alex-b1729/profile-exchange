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
def profile(request):
    return render(
        request,
        'account/profile.html',
        {'section': 'profile'}
    )


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
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


class EditProfileView(TemplateResponseMixin, View):
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
            return redirect('profile')
        return self.render_to_response(
            {'user_form': user_form,
             'profile_form': profile_form,
             'email_formset': email_formset,
             'phone_formset': phone_formset,
             'address_formset': address_formset,
             'socials_formset': socials_formset}
        )


@login_required
def connection_list(request):
    connections = request.user.connections.all()
    return render(
        request,
        'account/user/connections.html',
        {'section': 'connections',
         'connections': connections}
    )


@login_required
def contact_detail(request, username):
    contact = get_object_or_404(get_user_model(),
                                username=username,
                                is_active=True)
    return render(
        request,
        'account/user/contact.html',
        {'section': 'connections',
         'contact': contact}
    )
