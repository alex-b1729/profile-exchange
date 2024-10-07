import qrcode
import datetime as dt
import qrcode.image.svg
from profile.utils import vcard, consts
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin

from django.apps import apps
from django.db.models import Value
from django.urls import reverse_lazy
from django.core.files.base import ContentFile
from django.forms.models import modelform_factory
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

import profile.models as models
from .models import (
    Profile,
    Content,
    ItemBase,
    Email,
    LinkBase,
    Link,
)

from profile import forms
from .forms import (
    UserRegistrationForm,
    ProfileEditForm,
    UserEditEmailForm,
    ProfileDetailEditForm,
    ProfileImgEditForm,
    ProfileSelectContentForm,
)


def home(request):
    return render(
        request,
        'index.html',
        {'section': ''},
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


class UserEditMixin(object):
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


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


class ProfileCreateUpdateView(
    LoginRequiredMixin,
    UserMixin,
    TemplateResponseMixin,
    View,
):
    template_name = 'profile/manage/profile_edit.html'
    user = None
    profile = None

    def get_form(self, data=None, files=None):
        return ProfileEditForm(
            instance=self.profile,
            data=data,
        )

    def dispatch(self, request, profile_pk=None, *args, **kwargs):
        self.user = request.user
        if profile_pk:
            self.profile = get_object_or_404(
                Profile,
                pk=profile_pk,
                user=self.user,
            )
        return super().dispatch(
            request, *args, **kwargs
        )

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({
            'section': 'profiles',
            'form': form,
            'profile': self.profile,
        })

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
        return self.render_to_response({
            'section': 'profiles',
            'form': form,
            'profile': self.profile,
        })


@login_required
@require_POST
def profile_delete(request, profile_pk):
    p = get_object_or_404(
        Profile,
        user=request.user,
        pk=profile_pk,
    )
    p.delete()
    return redirect('profile_list')


@login_required
def profile(request, profile_pk):
    p = get_object_or_404(
        Profile,
        user=request.user,
        pk=profile_pk,
    )
    return render(
        request,
        'profile/detail.html',
        {
            'section': 'profiles',
            'entity': 'self',
            'profile': p,
        }
    )


class ProfileDetailEditView(
    LoginRequiredMixin,
    UserMixin,
    TemplateResponseMixin,
    View,
):
    template_name = 'profile/manage/edit_detail.html'
    user = None
    profile = None
    profile_pic = None

    def get_form(self, data=None):
        return forms.ProfileDetailEditForm(
            instance=self.profile,
            data=data,
        )

    def dispatch(self, request, profile_pk, *args, **kwargs):
        self.user = request.user
        self.profile = get_object_or_404(
            Profile,
            pk=profile_pk,
            user=self.user,
        )
        if self.profile.photo:
            self.profile_pic = self.profile.photo
        return super().dispatch(request, profile_pk, *args, **kwargs)

    def get(self, request, profile_pk, *args, **kwargs):
        form = self.get_form()
        return self.render_to_response({
            'section': 'profiles',
            'form': form,
            'profile_pic': self.profile_pic,
            'profile_pk': self.profile.pk,
        })

    def post(self, request, profile_pk, *args, **kwargs):
        form = self.get_form(data=request.POST)
        if form.is_valid():
            p = form.save(commit=True)
            return redirect('profile', p.pk)
        return self.render_to_response({
            'section': 'profiles',
            'form': form,
            'profile_pic': self.profile_pic,
            'profile_pk': self.profile.pk,
        })


@login_required
def update_profile_img(request, profile_pk):
    user = request.user
    user_profile = get_object_or_404(
        Profile,
        user=user,
        pk=profile_pk,
    )
    if request.method == 'POST':
        form = ProfileImgEditForm(
            instance=user_profile,
            data=request.POST,
            files=request.FILES
        )
        if form.is_valid():
            form.save()
            return redirect('profile', profile_pk)
    else:
        form = ProfileImgEditForm(instance=user_profile)
    return render(
        request,
        'profile/partials/update_profile_img.html',
        {
            'form': form,
            'pk': profile_pk,
        }
    )


@login_required
@require_POST
def profile_img_delete(request, profile_pk):
    p = get_object_or_404(
        Profile,
        user=request.user,
        pk=profile_pk
    )
    p.photo.delete(save=True)
    return redirect('profile', profile_pk)


@login_required
def user_content_view(request):
    c = dict()
    for content_type in consts.CONTENT_TYPES:
        mod = apps.get_model(app_label='profile', model_name=content_type)
        objs = mod.objects.filter(user=request.user)
        if objs:
            c[content_type] = objs
    return render(
        request,
        'user_content.html',
        {
            'section': 'content',
            'content_dict': c,
        }
    )


@login_required
def add_item(request):
    return render(
        request,
        'manage/add_item.html',
        {
            'section': 'content',
            'content_categories': consts.CONTENT_CATEGORIES,
        }
    )


class ContentCreateUpdateView(
    LoginRequiredMixin,
    UserEditMixin,
    TemplateResponseMixin,
    View
):
    profile = None
    model = None
    obj = None
    template_name = None
    initial = dict()
    context = dict()

    def set_template(self):
        self.template_name = f'manage/item/{self.model.__name__.lower()}_edit.html'

    def get_model(self, model_name):
        try:
            mod = apps.get_model(app_label='profile', model_name=model_name)
            if issubclass(mod, ItemBase):
                return mod
        except LookupError:
            if model_name.capitalize() in consts.CONTENT_CATEGORIES['Link']:
                # check if model_name is a LinkBase item
                try:
                    linkbase = LinkBase.objects.get(svg_id=model_name)
                    self.initial.update({'linkbase': linkbase})
                    self.context.update({'linkbase': linkbase})
                    return apps.get_model(app_label='profile', model_name='link')
                except LinkBase.DoesNotExist:
                    pass
            elif model_name.capitalize() in consts.CONTENT_CATEGORIES['Media']:
                try:
                    media_init = getattr(models.Media, model_name.upper())
                except AttributeError:
                    pass
                else:
                    self.initial.update({'media_type': media_init})
                    return apps.get_model(app_label='profile', model_name='media')
        return None

    def get_form(self, instance=None, data=None, files=None, *args, **kwargs):
        try:
            form = getattr(forms, f'{self.model.__name__.capitalize()}CreateUpdateForm')
            return form(
                instance=instance,
                initial=self.initial,
                data=data,
                files=files
            )
        except AttributeError:
            pass
        return None

    def set_context(self, **kwargs):
        for k, v in kwargs.items():
            self.context[k] = v

    def dispatch(self, request, model_name, profile_pk=None, content_pk=None, *args, **kwargs):
        self.model = self.get_model(model_name)
        self.set_template()
        if profile_pk:
            self.profile = get_object_or_404(
                Profile,
                pk=profile_pk,
                user=request.user,
            )
        if content_pk:
            self.obj = get_object_or_404(
                self.model,
                pk=content_pk,
                user=request.user,
            )
        self.set_context(
            section='profiles' if profile_pk else 'content',
            model_name=model_name,
            profile_pk=profile_pk,
            content_pk=content_pk,
            card_width=28,
        )
        return super(ContentCreateUpdateView, self).dispatch(
            request, model_name, profile_pk, content_pk, *args, **kwargs
        )

    def get(self, request, model_name, profile_pk=None, content_pk=None):
        form = self.get_form(instance=self.obj)
        self.context.update({'form': form})
        return self.render_to_response(self.context)

    def post(self, request, model_name, profile_pk=None, content_pk=None):
        form = self.get_form(
            instance=self.obj,
            data=request.POST,
            files=request.FILES,
        )
        self.context.update({'form': form})
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            if profile_pk:
                if not content_pk:
                    # if profile and no associated content then create new content
                    c = Content(
                        profile=self.profile,
                        item=item,
                    )
                    c.save()
                return redirect('profile_content_select', self.profile.pk)
            return redirect('content')
        return self.render_to_response(self.context)


@login_required
@require_POST
def content_delete(request, model_name, content_pk, profile_pk=None):
    if profile_pk:
        # delete the content but not the item
        content = get_object_or_404(
            Content,
            pk=content_pk,
            profile__pk=profile_pk,
            profile__user=request.user,
        )
        content.delete()
        return redirect('profile', profile_pk)
    else:
        # delete the actual item
        # here content_pk represents the item's pk
        try:
            model = apps.get_model(app_label='profile', model_name=model_name)
            if not issubclass(model, ItemBase):
                # page not found or just none? Like no response
                return page_not_found
        except LookupError:
            # check if model_name is a LinkBase item
            try:
                # todo: sanitize model_name! ??
                LinkBase.objects.get(svg_id=model_name)
                model = apps.get_model(app_label='profile', model_name='link')
            except LinkBase.DoesNotExist:
                return page_not_found
        item = get_object_or_404(
            model,
            pk=content_pk,
            user=request.user,
        )
        item.delete()
        return redirect('content')


class ProfileSelectContentView(
    LoginRequiredMixin,
    UserMixin,
    TemplateResponseMixin,
    View,
):
    template_name = 'profile/manage/select_content.html'
    user = None
    profile = None
    qs_dict = dict()
    initial_dict = dict()
    form_dict = dict()

    def set_forms(self, data=None):
        for content_type in self.qs_dict:
            self.form_dict[content_type] = ProfileSelectContentForm(
                qs=self.qs_dict[content_type],
                label=content_type.capitalize(),
                prefix=f'{content_type}form',
                initial={'model_choice': self.initial_dict[content_type]},
                data=data,
            )

    def set_qs_and_initial(self):
        """gets all items associated with user for all item models"""
        for content_type in consts.CONTENT_TYPES:
            mod = apps.get_model(app_label='profile', model_name=content_type)
            user_objs = mod.objects.filter(user=self.user)
            if user_objs.exists():
                self.qs_dict[content_type] = user_objs
                self.initial_dict[content_type] = user_objs.filter(content_related__profile=self.profile)

    def dispatch(self, request, profile_pk, *args, **kwargs):
        self.user = request.user
        self.profile = get_object_or_404(
            Profile,
            user=self.user,
            pk=profile_pk,
        )
        self.set_qs_and_initial()
        return super(ProfileSelectContentView, self).dispatch(
            request, profile_pk, *args, **kwargs
        )

    def get(self, request, profile_pk, *args, **kwargs):
        self.set_forms()
        return self.render_to_response({
            'section': 'profiles',
            'forms': self.form_dict.values(),
            'profile': self.profile,
            'content_categories': consts.CONTENT_CATEGORIES,
        })

    def post(self, request, profile_pk, *args, **kwargs):
        self.set_forms(data=request.POST)
        if all(form.is_valid() for form in self.form_dict.values()):
            for content_type, form in self.form_dict.items():
                models_in_form = form.cleaned_data['model_choice']
                initial_models = self.initial_dict[content_type]
                for mod in self.qs_dict[content_type]:
                    if models_in_form.contains(mod) and not initial_models.contains(mod):
                        # add new content
                        c = Content(
                            profile=self.profile,
                            item=mod,
                        )
                        c.save()
                    elif not models_in_form.contains(mod) and initial_models.contains(mod):
                        # remove previous content
                        content_to_remove = mod.content_related.get(profile=self.profile)
                        content_to_remove.delete()
                    else:
                        pass
            return redirect('profile', profile_pk)
        return self.render_to_response({
            'section': 'profiles',
            'forms': self.form_dict.values(),
            'profile': self.profile,
            'content_categories': consts.CONTENT_CATEGORIES,
        })


class ContentOrderView(
    CsrfExemptMixin,
    JsonRequestResponseMixin,
    View,
):
    def post(self, request):
        for content_pk, order in self.request_json.items():
            Content.objects.filter(pk=content_pk, profile__user=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


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
