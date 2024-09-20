import qrcode
import datetime as dt
import qrcode.image.svg
from profile.utils import vcard
from django.db.models import Value
from django.urls import reverse_lazy
from django.core.files.base import ContentFile
from formtools.wizard.views import SessionWizardView
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.views.generic.list import ListView
from django.views.defaults import page_not_found
from django.views.generic.detail import DetailView
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import ModelFormMixin

from .models import Profile
from .forms import (
    UserRegistrationForm,
    ProfileEditForm,
    UserEditEmailForm,
    ProfileDetailEditForm,
    ProfileImgEditForm,
)


def register(request):
    """depreciated for registration wizard"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            # Profile.objects.create(user=new_user)
            return render(
                request,
                'profile/register_done.html',
                {'new_user': new_user},
            )
    else:
        form = UserRegistrationForm()
    return render(
        request,
        'profile/register.html',
        {'form': form}
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
            # return redirect('profile')
    else:
        user_form = UserEditEmailForm(instance=request.user)
    return render(
        request,
        'profile/account.html',
        {'user_form': user_form}
    )


class UserMixin(object):
    def get_queryset(self):
        qs = super(UserMixin, self).get_queryset()
        return qs.filter(user=self.request.user)


@login_required
def profile_list(request):
    profiles = request.user.profile_set.all()
    return render(
        request,
        'profile/list.html',
        {
            'section': 'profiles',
            'profiles': profiles,
         }
    )


class ProfileEditCreateView(
    TemplateResponseMixin,
    View,
    UserMixin,
):
    template_name = 'profile/partials/profile_edit.html'
    user = None
    profile = None
    pk = None

    def get_form(self, data=None, files=None):
        return ProfileEditForm(
            instance=self.profile,
            data=data,
        )

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        if 'pk' in kwargs:
            self.pk = kwargs['pk']
            self.profile = get_object_or_404(
                Profile,
                pk=self.pk,
                user=self.user,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({'form': form, 'pk': self.pk})

    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            if p.pk:
                # editing existing
                p.save()
                return redirect('profile_list')
            else:
                # new profile
                p.user = self.user
                p.save()
                return redirect('profile_detail_edit', p.pk)
        return self.render_to_response({'form': form, 'pk': self.pk})


class ProfileDetailEditView(
    TemplateResponseMixin,
    View,
    UserMixin,
):
    template_name = 'profile/manage/profile/edit_detail.html'
    user = None
    profile = None
    pk = None

    def get_form(self, data=None, files=None):
        return ProfileDetailEditForm(
            instance=self.profile,
            data=data,
        )

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        if 'pk' in kwargs:
            self.pk = kwargs['pk']
            self.profile = get_object_or_404(
                Profile,
                pk=self.pk,
                user=self.user,
            )
        else:
            return page_not_found
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST)
        if form.is_valid():
            p = form.save(commit=True)
            return redirect('profile', pk=p.pk)
        return self.render_to_response({'form': form})


@login_required
@require_POST
def profile_delete(request, pk):
    p = get_object_or_404(
        Profile,
        user=request.user,
        pk=pk
    )
    p.delete()
    return redirect('profile_list')


@login_required
def profile(request, pk):
    profile = get_object_or_404(Profile, user=request.user, pk=pk)
    return render(
        request,
        'profile/detail.html',
        {
            'entity': 'self',
            'profile': profile,
        }
    )


def update_profile_img(request, pk):
    user = request.user
    user_profile = get_object_or_404(
        Profile,
        user=user,
        pk=pk,
    )
    if request.method == 'POST':
        form = ProfileImgEditForm(
            instance=user_profile,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            form.save()
            return redirect('profile', pk=pk)
    else:
        form = ProfileImgEditForm(instance=user_profile)
    return render(
        request,
        'profile/partials/update_profile_img.html',
        {
            'form': form,
            'pk': pk,
        }
    )


@login_required
@require_POST
def profile_img_delete(request, pk):
    p = get_object_or_404(
        Profile,
        user=request.user,
        pk=pk
    )
    p.photo.delete(save=True)
    return redirect('profile', pk)


# class RegisterWizard(SessionWizardView):
#     template_name = 'profile/register.html'
#
#     def done(self, form_list, **kwargs):
#         new_user = form_list[0].save(commit=False)
#         name_form_data = form_list[1].cleaned_data
#         fn = name_form_data['first_name']
#         ln = name_form_data['last_name']
#
#         new_card = Card(user=new_user, first_name=fn, last_name=ln)
#         new_profile = Profile(
#             user=new_user,
#             card=new_card,
#             title='Personal',
#             slug='personal',
#         )
#
#         new_user.save()
#         new_card.save()
#         new_profile.save()
#         return render(
#             self.request,
#             'profile/register_done.html',
#             {'first_name': fn},
#         )


# def edit_connection(request, connection_id=None):
#     # todo: contact edit form?
#     connection = None
#     card = None
#     mode = None  # context for whether card is new or existing
#     if connection_id:
#         connection = get_object_or_404(Connection,
#                                        id=connection_id,
#                                        # below so you can't try to query connections you're not part of
#                                        user=request.user)
#         card = get_object_or_404(Card, id=connection.card.pk)
#         mode = 'edit'
#     else:
#         # connection = Connection()
#         card = Card()
#         mode = 'new'
#     if request.method == 'POST':
#         card_form = CardEditForm(instance=card, data=request.POST, files=request.FILES)
#         address_formset = AddressFormSet(instance=card, data=request.POST)
#         phone_formset = PhoneFormSet(instance=card, data=request.POST)
#         email_formset = EmailFormSet(instance=card, data=request.POST)
#         org_formset = OrganizationFormSet(instance=card, data=request.POST, files=request.FILES)
#         tag_formset = TagFormSet(instance=card, data=request.POST)
#         url_formset = UrlFormSet(instance=card, data=request.POST)
#         if (
#             card_form.is_valid()
#             and address_formset.is_valid()
#             and phone_formset.is_valid()
#             and email_formset.is_valid()
#             and org_formset.is_valid()
#             and tag_formset.is_valid()
#             and url_formset.is_valid()
#         ):
#             new_card = Card.save()
#             address_formset.save()
#             phone_formset.save()
#             email_formset.save()
#             org_formset.save()
#             tag_formset.save()
#             url_formset.save()
#             if not connection:
#                 connection = Connection(user=request.user, card=new_card)
#                 connection.save()
#             # todo: return view of saved card
#             # return HttpResponse('success!')
#             return redirect(connection)
#     else:
#         card_form = CardEditForm(instance=card)
#         address_formset = AddressFormSet(instance=card)
#         phone_formset = PhoneFormSet(instance=card)
#         email_formset = EmailFormSet(instance=card)
#         org_formset = OrganizationFormSet(instance=card)
#         tag_formset = TagFormSet(instance=card)
#         url_formset = UrlFormSet(instance=card)
#     return render(
#         request,
#         'profile/edit.html',  # todo: this or something else?
#         {
#             'mode': mode,
#             'card_form': card_form,
#             'address_formset': address_formset,
#             'phone_formset': phone_formset,
#             'email_formset': email_formset,
#             'org_formset': org_formset,
#             'tag_formset': tag_formset,
#             'url_formset': url_formset
#          }
#     )


# class EditCardView(TemplateResponseMixin, View):
#     """
#     Edits Card and optionally Profile
#     """
#     template_name = 'profile/edit.html'
#
#     user = None
#     slug = None
#     user_profile = None
#     user_card = None
#     files = None
#
#     def get_card_form(self, data=None, files=None):
#         return CardEditForm(
#             instance=self.user_card, data=data
#         )
#
#     def get_profile_form(self, data=None):
#         return ProfileDetailEditForm(
#             instance=self.user_profile, data=data
#         )
#
#     def get_address_formset(self, data=None):
#         return AddressFormSet(instance=self.user_card, data=data)
#
#     def get_phone_formset(self, data=None):
#         return PhoneFormSet(instance=self.user_card, data=data)
#
#     def get_email_formset(self, data=None):
#         return EmailFormSet(instance=self.user_card, data=data)
#
#     def get_title_formset(self, data=None):
#         return TitleFormSet(instance=self.user_card, data=data)
#
#     def get_role_formset(self, data=None):
#         return RoleFormSet(instance=self.user_card, data=data)
#
#     def get_org_formset(self, data=None):
#         return OrgFormSet(instance=self.user_card, data=data)
#
#     def get_tag_formset(self, data=None):
#         return TagFormSet(instance=self.user_card, data=data)
#
#     def get_url_formset(self, data=None):
#         return UrlFormSet(instance=self.user_card, data=data)
#
#     def dispatch(self, request, *args, **kwargs):
#         if 'slug' in kwargs:
#             self.slug = kwargs['slug']
#         else:
#             page_not_found()
#         self.user = request.user
#         self.user_profile = get_object_or_404(
#             Profile,
#             user=self.user,
#             slug=kwargs['slug'],
#         )
#         self.user_card = self.user_profile.card
#         # appears to work fine for multiple forms with files
#         self.files = request.FILES
#         return super().dispatch(request, *args, **kwargs)
#
#     def get(self, request, *args, **kwargs):
#         card_form = self.get_card_form()
#         profile_form = self.get_profile_form()
#         address_formset = self.get_address_formset()
#         phone_formset = self.get_phone_formset()
#         email_formset = self.get_email_formset()
#         title_formset = self.get_title_formset()
#         role_formset = self.get_role_formset()
#         org_formset = self.get_org_formset()
#         tag_formset = self.get_tag_formset()
#         url_formset = self.get_url_formset()
#         return self.render_to_response(
#             {'mode': 'edit',
#              'profile_pic': self.user_card.photo,
#              'card_form': card_form,
#              'profile_form': profile_form,
#              'address_formset': address_formset,
#              'phone_formset': phone_formset,
#              'email_formset': email_formset,
#              'title_formset': title_formset,
#              'role_formset': role_formset,
#              'org_formset': org_formset,
#              'tag_formset': tag_formset,
#              'url_formset': url_formset}
#         )
#
#     def post(self, request, *args, **kwargs):
#         card_form = self.get_card_form(data=request.POST, files=self.files)
#         profile_form = self.get_profile_form(data=request.POST)
#         address_formset = self.get_address_formset(data=request.POST)
#         phone_formset = self.get_phone_formset(data=request.POST)
#         email_formset = self.get_email_formset(data=request.POST)
#         title_formset = self.get_title_formset(data=request.POST)
#         role_formset = self.get_role_formset(data=request.POST)
#         org_formset = self.get_org_formset(data=request.POST)
#         tag_formset = self.get_tag_formset(data=request.POST)
#         url_formset = self.get_url_formset(data=request.POST)
#         if (
#             card_form.is_valid()
#             and profile_form.is_valid()
#             and address_formset.is_valid()
#             and phone_formset.is_valid()
#             and email_formset.is_valid()
#             and title_formset.is_valid()
#             and role_formset.is_valid()
#             and org_formset.is_valid()
#             and tag_formset.is_valid()
#             and url_formset.is_valid()
#         ):
#             card_form.save()
#             profile_form.save()
#             address_formset.save()
#             phone_formset.save()
#             email_formset.save()
#             title_formset.save()
#             role_formset.save()
#             org_formset.save()
#             tag_formset.save()
#             url_formset.save()
#             return redirect('profile', slug=self.slug)
#         return self.render_to_response(
#             {'mode': 'edit',
#              'profile_pic': self.user_card.photo,
#              'card_form': card_form,
#              'profile_form': profile_form,
#              'address_formset': address_formset,
#              'phone_formset': phone_formset,
#              'email_formset': email_formset,
#              'title_formset': title_formset,
#              'role_formset': role_formset,
#              'org_formset': org_formset,
#              'tag_formset': tag_formset,
#              'url_formset': url_formset}
#         )
#
#
#
#
# @login_required
# def connection_list(request):
#     # gotta use .rel_from_set instead of .connections or will only get the profiles
#     connections = (request.user.profile_set.get(title='Personal')
#                    .rel_from_set.all())  #.select_related() could improve performance
#     return render(
#         request,
#         'profile/user/connections.html',
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
#                                    profile_from=request.user.profile_set.get(title='Personal'))
#
# @login_required
# def download_card(request, connection_id=None):
#     if connection_id:
#         return None
#     else:
#         card = request.user.profile_set.get(title='Personal').card
#     return card.vcf_http_reponse(request)
#
#
# @login_required
# def share_card(request):
#     p = get_object_or_404(
#         Profile,
#         user=request.user,
#         title='Personal'
#     )
#     rel_link = p.get_shareable_url()
#     abs_link = f'https://{Site.objects.get_current().domain}{rel_link}'
#     vcf = p.card.vcf
#     qr = qrcode.QRCode(
#         error_correction=qrcode.constants.ERROR_CORRECT_L,
#         image_factory=qrcode.image.svg.SvgPathImage
#     )
#     qr.add_data(vcf)
#     qr_svg = qr.make_image()
#     # qr_svg = qrcode.make(vcard, image_factory=qrcode.image.svg.SvgPathImage)
#     return render(
#         request,
#         'profile/partials/share_profile.html',
#         {'link': abs_link,
#          'svg': qr_svg.to_string(encoding='unicode')}
#     )
#
#
# def view_shared_profile(request, share_uuid):
#     p = get_object_or_404(
#         Profile,
#         share_uuid=share_uuid
#     )
#     # redirect to connection if they're already connections
#     if request.user.is_authenticated:
#         try:
#             p_from = request.user.profile_set.get(title='Personal')
#             p_to = p_from.connections.get(share_uuid=share_uuid)
#             conn = Connection.objects.filter(profile_from=p_from, profile_to=p_to)[0]
#             if conn:
#                 return redirect('connection_detail', connection_id=conn.id)
#         except Profile.DoesNotExist or Connection.DoesNotExist:
#             # todo: display message?
#             pass
#     return render(
#         request,
#         'profile/card.html',
#         {
#             'section': '',
#             'entity': 'shared',
#             'profile': p,
#             'vc': p.card.to_vobject()
#         }
#     )
#
#
# @login_required
# @require_POST
# def connect(request, share_uuid): #, share_title_from='Personal'):
#     try:
#         p_from = get_object_or_404(
#             Profile,
#             user=request.user,
#             title='Personal'
#         )
#         p_to = get_object_or_404(
#             Profile,
#             share_uuid=share_uuid
#         )
#         p_from.connections.add(p_to)
#         new_connection = Connection.objects.get(
#             profile_from=p_from,
#             profile_to=p_to
#         )
#         return redirect('connection_detail', connection_id=new_connection.id)
#     except Exception as e:
#         raise e
#         # return JsonResponse({'status': 'ko'})
#
#
# @login_required
# def import_cards(request):
#     if request.method == 'POST':
#         form = ImportCardForm(request.POST, request.FILES)
#         if form.is_valid():
#             # todo: this ain't memory safe
#             vmods = vcard.vcf_to_model_dicts(request.FILES['file'].read().decode("utf-8") )
#             vcard.save_model_dict_to_db(request.user, vmods)
#             return render(
#                 request,
#                 'profile/user/contactbook.html',
#                 {'section': 'contactbook'}
#             )
#     else:
#         form = ImportCardForm()
#     return render(
#         request,
#         'profile/user/import_cards.html',
#         {'section': 'contactbook',
#          'form': form}
#     )
#
#
# @login_required
# def contact_book(request):
#     obj_list = Card.objects.filter(user=request.user)
#     paginator = Paginator(obj_list, 3)
#     page = request.GET.get('page')
#     try:
#         cards = paginator.page(page)
#     except PageNotAnInteger:
#         cards = paginator.page(1)
#     except EmptyPage:
#         cards = paginator.page(paginator.num_pages)
#     return render(
#         request,
#         'profile/user/contactbook.html',
#         {
#             'section': 'contactbook',
#             'cards': cards,
#         }
#     )
#
#
# @login_required
# def connection_detail(request, connection_id):
#     connection = get_object_or_404(Connection,
#                                    id=connection_id,
#                                    # below so you can't try to query connections you're not part of
#                                    profile_from=request.user.profile_set.get(title='Personal'))
#     p_to = connection.profile_to
#     return render(
#         request,
#         'profile/card.html',
#         {
#             'section': 'connections',
#             'entity': 'connection',
#             'profile': p_to,
#             'vc': p_to.card.to_vobject()
#         }
#     )
#
#
# @login_required
# def card_detail(request, card_id):
#     card = get_object_or_404(
#         Card,
#         id=card_id,
#         user=request.user
#     )
#     return  render(
#         request,
#         'profile/card.html',
#         {
#             'section': 'contactbook',
#             'entity': 'connection',
#             'profile': None,
#             'vc': card.to_vobject()
#         }
#     )
