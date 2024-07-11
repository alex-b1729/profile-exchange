import qrcode
import datetime as dt
import qrcode.image.svg
from account.utils import vcard
from django.db.models import Value
from django.contrib import messages
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.views.generic.detail import DetailView
from formtools.wizard.views import SessionWizardView
from django.views.decorators.http import require_POST
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateResponseMixin, View

from .models import (
    Card,
    Profile,
    Connection,
    Address,
    Phone,
    Email,
    Title,
    Role,
    Org,
    Tag,
    Url,
)
from .forms import (
    UserRegistrationForm,
    CardNameForm,
    UserEditEmailForm,
    CardEditForm,
    AddressFormSet,
    PhoneFormSet,
    EmailFormSet,
    TitleFormSet,
    RoleFormSet,
    OrgFormSet,
    TagFormSet,
    UrlFormSet,
    ProfileEditForm,
    ImportCardForm,
)


@login_required
def profile(request):
    profile = get_object_or_404(Profile, user=request.user, title='Personal')
    # query all the vcard data here for easier display
    vc = profile.card.to_vobject()
    # below bugs when user is admin
    # profile = request.user.profile_set.select_related('card').get(title='Personal')
    return render(
        request,
        'account/card.html',
        {
            'section': 'profile',
            'entity': 'self',
            'profile': profile,
            'vc': vc,
        }
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
    """depreciated for registration wizard"""
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


class RegisterWizard(SessionWizardView):
    template_name = 'account/register.html'

    def done(self, form_list, **kwargs):
        new_user = form_list[0].save(commit=False)
        name_form_data = form_list[1].cleaned_data
        fn = name_form_data['first_name']
        ln = name_form_data['last_name']

        new_card = Card(user=new_user, first_name=fn, last_name=ln)
        new_profile = Profile(user=new_user, card=new_card)

        new_user.save()
        new_card.save()
        new_profile.save()
        return render(
            self.request,
            'account/register_done.html',
            {'first_name': fn},
        )


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
#         'account/edit.html',  # todo: this or something else?
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


class EditCardView(TemplateResponseMixin, View):
    """
    Edits Card and optionally Profile
    """
    template_name = 'account/edit.html'

    user = None
    user_profile = None
    user_card = None
    files = None

    def get_card_form(self, data=None, files=None):
        return CardEditForm(
            instance=self.user_card, data=data, files=files
        )

    def get_profile_form(self, data=None):
        return ProfileEditForm(
            instance=self.user_profile, data=data
        )

    def get_address_formset(self, data=None):
        return AddressFormSet(instance=self.user_card, data=data)

    def get_phone_formset(self, data=None):
        return PhoneFormSet(instance=self.user_card, data=data)

    def get_email_formset(self, data=None):
        return EmailFormSet(instance=self.user_card, data=data)

    def get_title_formset(self, data=None):
        return TitleFormSet(instance=self.user_card, data=data)

    def get_role_formset(self, data=None):
        return RoleFormSet(instance=self.user_card, data=data)

    def get_org_formset(self, data=None):
        return OrgFormSet(instance=self.user_card, data=data)

    def get_tag_formset(self, data=None):
        return TagFormSet(instance=self.user_card, data=data)

    def get_url_formset(self, data=None):
        return UrlFormSet(instance=self.user_card, data=data)

    def dispatch(self, request, *args, **kwargs):
        self.user = request.user
        # todo: should create a user profile if fails to find one?
        self.user_profile = get_object_or_404(
            Profile, user=self.user,
            title='Personal'  # Note: hard coded profile title for this version!
        )
        self.user_card = self.user_profile.card
        # appears to work fine for multiple forms with files
        self.files = request.FILES
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        card_form = self.get_card_form()
        profile_form = self.get_profile_form()
        address_formset = self.get_address_formset()
        phone_formset = self.get_phone_formset()
        email_formset = self.get_email_formset()
        title_formset = self.get_title_formset()
        role_formset = self.get_role_formset()
        org_formset = self.get_org_formset()
        tag_formset = self.get_tag_formset()
        url_formset = self.get_url_formset()
        return self.render_to_response(
            {'mode': 'self',
             'card_form': card_form,
             'profile_form': profile_form,
             'address_formset': address_formset,
             'phone_formset': phone_formset,
             'email_formset': email_formset,
             'title_formset': title_formset,
             'role_formset': role_formset,
             'org_formset': org_formset,
             'tag_formset': tag_formset,
             'url_formset': url_formset}
        )

    def post(self, request, *args, **kwargs):
        card_form = self.get_card_form(data=request.POST, files=self.files)
        profile_form = self.get_profile_form(data=request.POST)
        address_formset = self.get_address_formset(data=request.POST)
        phone_formset = self.get_phone_formset(data=request.POST)
        email_formset = self.get_email_formset(data=request.POST)
        title_formset = self.get_title_formset(data=request.POST)
        role_formset = self.get_role_formset(data=request.POST)
        org_formset = self.get_org_formset(data=request.POST)
        tag_formset = self.get_tag_formset(data=request.POST)
        url_formset = self.get_url_formset(data=request.POST)
        if (
            card_form.is_valid()
            and profile_form.is_valid()
            and address_formset.is_valid()
            and phone_formset.is_valid()
            and email_formset.is_valid()
            and title_formset.is_valid()
            and role_formset.is_valid()
            and org_formset.is_valid()
            and tag_formset.is_valid()
            and url_formset.is_valid()
        ):
            card_form.save()
            profile_form.save()
            address_formset.save()
            phone_formset.save()
            email_formset.save()
            title_formset.save()
            role_formset.save()
            org_formset.save()
            tag_formset.save()
            url_formset.save()
            return redirect('profile')
        return self.render_to_response(
            {'mode': 'self',
             'card_form': card_form,
             'profile_form': profile_form,
             'address_formset': address_formset,
             'phone_formset': phone_formset,
             'email_formset': email_formset,
             'title_formset': title_formset,
             'role_formset': role_formset,
             'org_formset': org_formset,
             'tag_formset': tag_formset,
             'url_formset': url_formset}
        )


# @login_required
# def card_list(request):
#     # connections not linked to personal card
#     connections = request.user.rel_from_set.filter(card=None)
#     # all user cards includes those linked to a connection
#     cards = request.user.card_set.all()
#     return render(
#         request,
#         'account/user/connections.html',
#         {'section': 'connections',
#          'connections': connections}
#     )


@login_required
def connection_list(request):
    # gotta use .rel_from_set instead of .connections or will only get the profiles
    connections = (request.user.profile_set.get(title='Personal')
                   .rel_from_set.all())  #.select_related() could improve performance
    return render(
        request,
        'account/user/connections.html',
        {'section': 'connections',
         'connections': connections}
    )


@login_required
def connection_detail(request, connection_id):
    connection = get_object_or_404(Connection,
                                   id=connection_id,
                                   # below so you can't try to query connections you're not part of
                                   profile_from=request.user.profile_set.get(title='Personal'))
    return render(
        request,
        'account/card.html',
        {
            'section': 'connections',
            'entity': 'connection',
            'profile': connection.profile_to
        }
    )

@login_required
def download_card(request, connection_id=None):
    if connection_id:
        # connection = get_object_or_404(
        #     Connection,
        #     id=connection_id,
        #     user=request.user
        # )
        # card = connection.card
        return None
    else:
        card = request.user.profile_set.get(title='Personal').card
    return card.vcf_http_reponse(request)


@login_required
# @require_POST  # post if i'm changing the server state
def share_card(request, share_uuid):
    p = get_object_or_404(
        Profile,
        user=request.user,
        share_uuid=share_uuid
    )
    link = 'https://www.contacts.con/ashareablelink' #p.get_absolute_url()
    vcard = p.card.vcf
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        image_factory=qrcode.image.svg.SvgPathImage
    )
    qr.add_data(vcard)
    qr_svg = qr.make_image()
    # qr_svg = qrcode.make(vcard, image_factory=qrcode.image.svg.SvgPathImage)
    return render(
        request,
        'account/partials/share_profile.html',
        {'link': link,
         'svg': qr_svg.to_string(encoding='unicode')}
    )


@login_required
def import_cards(request):
    if request.method == 'POST':
        form = ImportCardForm(request.POST, request.FILES)
        if form.is_valid():
            # todo: this ain't memory safe
            vmods = vcard.vcf_to_model_dicts(request.FILES['file'].read().decode("utf-8") )
            vcard.save_model_dict_to_db(request.user, vmods)
            return render(
                request,
                'account/user/contactbook.html',
                {'section': 'contactbook'}
            )
    else:
        form = ImportCardForm()
    return render(
        request,
        'account/user/import_cards.html',
        {'section': 'contactbook',
         'form': form}
    )

@login_required
def contact_book(request):
    return render(
        request,
        'account/user/contactbook.html',
        {'section': 'contactbook'}
    )


# @login_required
# def connection_detail(request, connection_id):
#     connection = get_object_or_404(Connection,
#                                    id=connection_id,
#                                    # below so you can't try to query connections you're not part of
#                                    user=request.user)
#     local_card = connection.card
#     card_list = [local_card]
#     if connection.profile:
#         linked_card = connection.profile.user.card
#         card_list.append(linked_card)
#
#     addresses = Address.objects.filter(card__in=card_list)
#
#     # Or
#     address_qs = connection.card.address_set.all().annotate(linked=Value(False))
#     if connection.profile:
#         linked_qs = connection.profile.user.card.address_set.all().annotate(linked=Value(True))
#         address_qs = address_qs.union(linked_qs)
#
#     # usage
#     # for a in address_qs:
#     #     print(f'{a}{" - linked" if a.linked else ""}')
#
#     return render(
#         request,
#         'account/card.html',
#         {
#             'section': 'connections',
#             'entity': 'connection',
#             'connection': connection,
#             # 'addresses': address_qs # or addresses
#             'card': connection.card,
#             'profile': connection.profile
#         }
#     )
