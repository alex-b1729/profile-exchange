import datetime as dt
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.views.generic.detail import DetailView
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View

from .models import (
    Vcard,
    Profile,
)
from .forms import (
    UserRegistrationForm,
    UserEditEmailForm,
    VcardEditForm,
    AddressFormSet,
    PhoneFormSet,
    EmailFormSet,
    OrganizationFormSet,
    TagFormSet,
    UrlFormSet,
    ProfileEditForm,
)


@login_required
def profile(request):
    return render(
        request,
        'account/profile.html',
        {'section': 'profile'}
    )

@login_required
def account(request):
    if request.method == 'POST':
        user_form = UserEditEmailForm(
            instance=request.user,
            data=request.POST
        )
        if user_form.is_valid():
            user_form.save()
            # return redirect('account')
    else:
        user_form = UserEditEmailForm(instance=request.user)
    return render(
        request,
        'account/account.html',
        {'user_form': user_form}
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
    """
    Edits both user's Profile and Vcard
    """
    template_name = 'account/edit.html'

    user = None
    user_profile = None
    user_vcard = None
    files = None

    def get_vcard_form(self, data=None, files=None):
        return VcardEditForm(
            instance=self.user_vcard, data=data, files=files
        )

    def get_profile_form(self, data=None):
        return ProfileEditForm(
            instance=self.user_profile, data=data
        )

    def get_address_formset(self, data=None):
        return AddressFormSet(instance=self.user, data=data)

    def get_phone_formset(self, data=None):
        return PhoneFormSet(instance=self.user, data=data)

    def get_email_formset(self, data=None):
        return EmailFormSet(instance=self.user, data=data)

    def get_org_formset(self, data=None, files=None):
        return OrganizationFormSet(instance=self.user, data=data, files=files)

    def get_tag_formset(self, data=None):
        return TagFormSet(instance=self.user, data=data)

    def get_url_formset(self, data=None):
        return UrlFormSet(instance=self.user, data=data)

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        # todo: should create a user profile if fails to find one?
        self.user_profile = get_object_or_404(
            Profile, user=self.user
        )
        self.user_vcard = get_object_or_404(
            Vcard, user=self.user
        )
        # does below work as expected with multiple files?
        self.files = request.FILES
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        vcard_form = self.get_vcard_form()
        profile_form = self.get_profile_form()
        address_formset = self.get_address_formset()
        phone_formset = self.get_phone_formset()
        email_formset = self.get_email_formset()
        org_formset = self.get_org_formset()
        tag_formset = self.get_tag_formset()
        url_formset = self.get_url_formset()
        return self.render_to_response(
            {'vcard_form': vcard_form,
             'profile_form': profile_form,
             'address_formset': address_formset,
             'phone_formset': phone_formset,
             'email_formset': email_formset,
             'org_formset': org_formset,
             'tag_formset': tag_formset,
             'url_formset': url_formset}
        )

    def post(self, request, *args, **kwargs):
        vcard_form = self.get_vcard_form(data=request.POST, files=self.files)
        profile_form = self.get_profile_form(data=request.POST)
        address_formset = self.get_address_formset(data=request.POST)
        phone_formset = self.get_phone_formset(data=request.POST)
        email_formset = self.get_email_formset(data=request.POST)
        org_formset = self.get_org_formset(data=request.POST, files=self.files)
        tag_formset = self.get_tag_formset(data=request.POST)
        url_formset = self.get_url_formset(data=request.POST)
        if (
            vcard_form.is_valid()
            and profile_form.is_valid()
            and address_formset.is_valid()
            and phone_formset.is_valid()
            and email_formset.is_valid()
            and org_formset.is_vaid()
            and tag_formset.is_valid()
            and url_formset.is_valid()
        ):
            vcard_form.save()
            profile_form.save()
            address_formset.save()
            phone_formset.save()
            email_formset.save()
            org_formset.save()
            tag_formset.save()
            url_formset.save()
            return redirect('profile')
        return self.render_to_response(
            {'vcard_form': vcard_form,
             'profile_form': profile_form,
             'address_formset': address_formset,
             'phone_formset': phone_formset,
             'email_formset': email_formset,
             'org_formset': org_formset,
             'tag_formset': tag_formset,
             'url_formset': url_formset}
        )


# class VCard(object):
#     # todo: add photo
#     # todo: remove hardcoded vcard feature names
#     # todo: x-features
#     # todo: sanitize user inputs!
#     # todo: implement labels for social profiles
#     begin_vcard = 'BEGIN:VCARD\n'
#     vcard_version = 'VERSION:3.0\n'
#     charset = ';CHARSET=UTF-8'  # todo: what does this really do? It's included by vcardmaker
#     rev = 'REV:%s\n'
#     end_vcard = 'END:VCARD\n'
#     def __init__(self, user):
#         # self.requesting_user = request.user?
#         self.user = user
#         self.profile = get_object_or_404(Profile,
#                                          user=self.user)
#
#     def yield_profile_features(self):
#         p: Profile = self.profile
#         if p.nick_name != '': yield f'NICKNAME{self.charset}:{p.nick_name}\n'
#
#         if p.birthday is not None: yield f'BDAY:{p.birthday.strftime("%Y%m%d")}\n' # format?
#
#         if p.home_page != '': yield f'URL;type=HOME{self.charset}:{p.home_page}\n'
#
#         # org
#         if p.title != '': yield f'TITLE{self.charset}:{p.title}\n'
#         if p.role != '': yield f'ROLE{self.charset}:{p.role}\n'
#         if p.organization != '': yield f'ORG{self.charset}:{p.organization}\n'
#
#         if p.anniversary is not None: yield f'ANNIVERSARY:{p.anniversary.strftime("%Y%m%d")}\n'
#
#         if p.sex is not None or p.gender != '':
#             g = f'GENDER{self.charset}:'
#             if p.sex is not None: g += f'{p.sex}'
#             if p.gender != '': g += f';{p.gender}'
#             yield g + '\n'
#
#     def yield_email_features(self):
#         email_list = self.user.email_addresses.all()
#         # what is email_list when there're no emails? None?
#         for e in email_list:
#             s = f'EMAIL;TYPE=INTERNET'
#             if e.email_type != 'other': s += f';TYPE={e.email_type}'
#             s += f':{e.email_address}\n'
#             yield s
#
#     def yield_phone_features(self):
#         phone_list = self.user.phone_numbers.all()
#         for p in phone_list:
#             s = 'TEL'
#             if p.phone_type != 'other': s += f';TYPE={p.phone_type.replace(" ", ",")}'
#             s += f':{p.TEL}\n'
#             yield s
#
#     def yield_address_features(self):
#         address_list = self.user.postal_addresses.all()
#         for a in address_list:
#             s = f'ADR{self.charset}'
#             if a.address_type != 'other': s += f';TYPE={a.address_type}'
#             s += f':{a.ADR}\n'
#             yield s
#
#     def yield_social_features(self):
#         social_list = self.user.social_profiles.all()
#         for s in social_list:
#             yield f'X-SOCIALPROFILE:{s.url}\n'
#
#     def generate_vcard(self):
#         yield self.begin_vcard
#         yield self.vcard_version
#         yield f'FN{self.charset}:{self.profile.FN}\n'
#         yield f'N{self.charset}:{self.profile.N}\n'
#         yield from self.yield_profile_features()
#         yield from self.yield_email_features()
#         yield from self.yield_phone_features()
#         yield from self.yield_address_features()
#         yield from self.yield_social_features()
#         yield self.rev % dt.datetime.now()  # todo: update formatting
#         yield self.end_vcard
#
#     def vcard_text(self):
#         s = ''
#         for line in self.generate_vcard():
#             s += line
#         return s


# @login_required
# def download_vcard(request, username=None):
#     if username is None:
#         user = request.user
#     else:
#         user = get_object_or_404(get_user_model(),
#                                  username=username,
#                                  is_active=True)
#     content = ContentFile(VCard(user).vcard_text())
#     return HttpResponse(
#         content,
#         headers={
#             'Content-Type': 'text/plain',
#             'Content-Disposition': f'attachment; filename="{user.first_name}{user.last_name}.vcf'
#         }
#     )


# @login_required
# def connection_list(request):
#     connections = Connection.objects.filter(user_from=request.user)
#     return render(
#         request,
#         'account/user/connections.html',
#         {'section': 'connections',
#          'connections': connections}
#     )
#
#
# @login_required
# def connection_detail(request, connection_id):
#     connection = get_object_or_404(Connection,
#                                    id=connection_id,
#                                    # below so you can't try to query connections you're not part of
#                                    user_from=request.user)
#     return render(
#         request,
#         'account/user/contact.html',
#         {'section': 'connections',
#          'connection': connection}
#     )
