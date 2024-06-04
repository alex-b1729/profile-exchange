from django.contrib import messages
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import (
    Profile,
    EmailAddress,
    Phone,
    PostalAddress,
)
from .forms import (
    UserRegistrationForm,
    UserEditForm,
    ProfileEditForm,
    EmailAddressFormSet,
    PhoneFormSet,
    PostalAddressFormSet,
)


@login_required
def dashboard(request):
    emails = EmailAddress.objects.filter(user=request.user)
    phones = Phone.objects.filter(user=request.user)
    addresses = PostalAddress.objects.filter(user=request.user)
    return render(request,
                  'account/dashboard.html',
                  {'section': 'dashboard',
                   'emails': emails,
                   'phones': phones,
                   'addresses': addresses})


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
        if (user_form.is_valid()
                and profile_form.is_valid()
                and email_formset.is_valid()):
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
        email_formset = EmailAddressFormSet(queryset=EmailAddress.objects.filter(user=request.user))
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
