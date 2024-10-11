import uuid
import os.path
import vobject
import datetime as dt
from urllib.parse import urlparse

from .fields import OrderField
from .utils import consts, vcard

from django.apps import apps
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Value
from django.http import HttpResponse
from django.utils.text import slugify
from embed_video.fields import EmbedVideoField
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from djangoyearlessdate.models import YearlessDateField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


class Profile(models.Model):
    class Kind(models.TextChoices):
        INDIVIDUAL = 'ID', _('Individual')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    # individual, group, org...
    kind = models.CharField(
        max_length=2,
        choices=Kind,
        default=Kind.INDIVIDUAL,
        blank=False,
        verbose_name='kind',
    )

    # -------- local info for the user --------
    title = models.CharField(max_length=50, blank=False, verbose_name='kind')
    description = models.CharField(blank=True, verbose_name='description')

    # -------- info displayed on profile --------
    # todo: update for non-individual self.kind
    prefix = models.CharField(max_length=50, blank=True, verbose_name='prefix')
    first_name = models.CharField(max_length=50, blank=True, verbose_name='first name')
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='middle name')
    # last name serves as name if kind is not individual
    last_name = models.CharField(max_length=50, blank=True, verbose_name='last name')
    suffix = models.CharField(max_length=50, blank=True, verbose_name='suffix')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='nickname')

    photo = models.ImageField(
        upload_to=consts.PROFILE_PHOTO_DIR,
        blank=True,
        verbose_name='photo',
    )

    headline = models.CharField(max_length=120, blank=True, verbose_name='headline')
    location = models.CharField(max_length=50, blank=True, verbose_name='location')
    about = models.TextField(blank=True, verbose_name='about')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'profile'
        verbose_name_plural = 'profiles'

    def __str__(self):
        return f'{self.user.username}\'s {self.title} Profile'

    def get_absolute_url(self):
        return reverse('profile', kwargs={'profile_pk': self.pk})

    @property
    def fn(self):
        s = (f'{self.prefix + " " if self.prefix else ""}'
             f'{self.first_name + " " if self.first_name else ""}'
             f'{self.middle_name + " " if self.middle_name else ""}'
             f'{self.last_name}'
             f'{", " + self.suffix if self.suffix else ""}')
        return s


class Content(models.Model):
    profile = models.ForeignKey(
        Profile,
        related_name='contents',
        related_query_name='content',
        on_delete=models.CASCADE,
    )

    def item_subclass_choices(self):
        return [m.__name__ for m in apps.get_models() if issubclass(m, ItemBase)]

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': item_subclass_choices()
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['profile'])

    class Meta:
        ordering = ['order']
        verbose_name = 'content'
        verbose_name_plural = 'contents'


class ItemBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_related',
        on_delete=models.CASCADE,
    )
    content_related = GenericRelation(Content)
    label = models.CharField(max_length=50, blank=True, verbose_name='label')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def render(self):
        return render_to_string(
            f'profile/partials/models/{self.__class__.__name__.lower()}_render.html',
            {'object': self}
        )


# todo: validate all Items
class ContactInfoBase(ItemBase):
    class InfoTypes(models.TextChoices):
        WORK = 'W', _('Work')
        HOME = 'H', _('Home')
        OTHER = 'O', _('Other')

    info_type = models.CharField(
        max_length=1,
        choices=InfoTypes,
        blank=True,
        verbose_name='type',
    )

    class Meta(ItemBase.Meta):
        abstract = True


class Email(ContactInfoBase):
    email_address = models.EmailField(
        blank=False,
        verbose_name='email',
    )

    class Meta(ContactInfoBase.Meta):
        verbose_name = 'email'
        verbose_name_plural = 'emails'

    def __str__(self):
        return (f'{self.info_type.label + ": " if self.info_type else ""}'
                f'{self.email_address}'
                f'{", " + self.label if self.label else ""}')


class Phone(ContactInfoBase):
    # todo: international?
    phone_number = PhoneNumberField(
        balnk=False,
        verbose_name='phone number',
    )

    class Meta(ContactInfoBase.Meta):
        verbose_name = 'phone'
        verbose_name_plural = 'phones'

    def __str__(self):
        return (f'{self.info_type.label + ": " if self.info_type else ""}'
                f'{self.phone_number}'
                f'{", " + self.label if self.label else ""}')


class Address(ContactInfoBase):
    # todo: international?
    street1 = models.CharField(blank=False, verbose_name='street')
    street2 = models.CharField(blank=True, verbose_name='street line 2')
    city = models.CharField(blank=False, verbose_name='city')
    state = models.CharField(blank=False, verbose_name='state')
    zip = models.CharField(max_length=10, blank=False, verbose_name='zip code')
    country = models.CharField(blank=True, verbose_name='country')

    class Meta(ContactInfoBase.Meta):
        verbose_name = 'address'
        verbose_name_plural = 'addresses'

    def __str__(self):
        return (f'{self.info_type.label + ": " if self.info_type else ""}'
                f'{self.street1}'
                f'{", " + self.label if self.label else ""}')


class LinkBase(models.Model):
    """holds primary domains and info for external links
    E.g. netloc: https://github.com/"""
    title = models.CharField(
        blank=False,
        default='Website',
        verbose_name='title',
    )
    netloc = models.CharField(
        blank=True,
        verbose_name='netloc',
    )

    class Meta:
        verbose_name = 'linkbase'
        verbose_name_plural = 'linkbases'

    def __str__(self):
        return str(self.title)


class Link(ItemBase):
    linkbase = models.ForeignKey(
        LinkBase,
        default=1,
        on_delete=models.SET_DEFAULT,
        verbose_name='linkbase',
        related_name='links',
        related_query_name='link',
    )
    url = models.CharField(max_length=200, verbose_name='url')
    is_independent_url = models.BooleanField(
        default=True,
        blank=False,
        verbose_name='independent url',
        help_text='Indicates url does not require linkbase.netlock as the prefix',
    )

    class Meta(ItemBase.Meta):
        ordering = ['linkbase']
        verbose_name = 'link'
        verbose_name_plural = 'links'

    def __str__(self):
        if self.is_independent_url:
            return str(self.url)
        else:
            return f'{self.linkbase.domain}{self.url}'

    def save(self, *args, **kwargs):
        if not self.is_independent_url:
            self.is_independent_url = self.linkbase == 1
        super().save(*args, **kwargs)

    @property
    def pretty_url(self):
        if self.is_independent_url:
            url = urlparse(str(self.url))
        else:
            url = urlparse(f'{self.linkbase.domain}{self.url}')
        return f'{url.netloc}{url.path}{url.params}{url.query}{url.fragment}'.rstrip('/')


class Attachment(ItemBase):
    class AttachmentTypes(models.TextChoices):
        DOCUMENT = 'D', _('Document')
        IMAGE = 'I', _('Image')

    attachment_type = models.CharField(
        max_length=1,
        choices=AttachmentTypes,
        blank=False,
        verbose_name='attachment type',
    )
    url = models.URLField(
        blank=True,
        verbose_name='url',
    )
    file = models.FileField(
        upload_to=consts.ATTACHMENT_MODEL_DIR,
        blank=True,
        verbose_name='file',
    )

    def __str__(self):
        return (f'{self.attachment_type.label}: '
                f'{self.url if self.url else self.file.name}')


class PostBase(ItemBase):
    title = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='title',
    )
    description = models.TextField(
        blank=True,
        verbose_name='description',
    )
    date = models.DateField(
        blank=True,
        verbose_name='date',
    )
    external_link = models.URLField(
        blank=True,
        verbose_name='external link',
    )

    class Meta(ItemBase.Meta):
        abstract = True
        ordering = ['-date']

    def __str__(self):
        return f'{self.title}{" - " + str(self.date) if self.date else ""}'


class OrgBase(PostBase):
    organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='organization',
    )

    class Meta(PostBase.Meta):
        abstract = True

    def __str__(self):
        return f'{self.title}{" - " + str(self.organization) if self.organization else ""}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_link.help_text = 'Link to organization'


class Award(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Awarding organization or body'


class Certificate(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Certifying organization or body'


class License(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Licensing organization or body'


class MembershipBase(OrgBase):
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='location'
    )
    # todo: dates should be more generic to allow just month and/or year
    end_date = models.DateField(
        blank=True,
        verbose_name='end date'
    )
    current = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name='current'
    )

    class Meta(OrgBase.Meta):
        abstract = True
        ordering = ['-end_date', '-date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title.help_text = 'Title or position'
        self.date.verbose_name = 'start date'


class Membership(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class WorkExperience(MembershipBase):
    class SettingType(models.TextChoices):
        IN_PERSON = 'i', _('In-Person')
        HYBRID = 'h', _('Hybrid')
        REMOTE = 'r', _('Remote')

    work_setting = models.CharField(
        max_length=1,
        choices=SettingType,
        blank=True,
        verbose_name='work setting',
    )

    class Meta(MembershipBase.Meta):
        verbose_name = 'work experience'
        verbose_name_plural = 'work experiences'

    def __str__(self):
        return f'{self.title} at {self.organization}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.blank = False  # have to work for some org/comp
        self.organization.verbose_name = 'Company or organization'
        self.external_link.help_text = 'Link to company'


class VolunteerWork(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class Education(MembershipBase):
    degree_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='degree type',
        help_text="Associate, bachelor's, master's, etc."
    )
    gpa = models.FloatField(
        blank=True,
        null=True,
        verbose_name='GPA',
        help_text='Grade point average',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.blank = False  # must be educated somewhere
        self.title.verbose_name = 'major'
        self.date.verbose_name = 'start date'
        self.location.help_text = 'School, university, etc.'
        self.end_date.help_text = 'Graduation or expected graduation date'


class ProjectBase(PostBase):
    contributors = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='contributors',
        help_text='Contributors or co-authors',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='project source',
        help_text='Publication, journal, publisher, etc.',
    )

    class Meta(PostBase.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_link.help_text = 'Link to project source'


class Project(ProjectBase):
    pass


class PublishedWork(ProjectBase):
    class Meta(ProjectBase.Meta):
        verbose_name = 'published work'
        verbose_name_plural = 'published works'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source.blank = False  # must be published somewhere
        self.source.verbose_name = 'publication source'
        self.contributors.verbose_name = 'authors'
        self.external_link.help_text = 'Link to publication'


class ResearchProject(ProjectBase):
    affiliated_institutions = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='affiliated institutions',
    )
    funding_source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='funding source',
        help_text='Grant, institution, etc.',
    )

    class Meta(ProjectBase.Meta):
        verbose_name = 'research project'
        verbose_name_plural = 'research projects'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.contributors.blank = False  # someone must have contributed
        self.contributors.verbose_name = 'authors'
        self.date.help_text = 'Publication date or date of latest version'
        self.description.help_text = 'Abstract or project summary'
        self.external_link.help_text = 'Link to publication'
        self.source.verbose_name = 'publication source'
        self.source.help_text = 'Journal or conference name'


class Patent(ProjectBase):
    class StatusType(models.TextChoices):
        PENDING = 'p', _('Pending')
        GRANTED = 'g', _('Granted')
        EXPIRED = 'e', _('Expired')

    number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='patent number',
    )
    status = models.CharField(
        choices=StatusType,
        blank=True,
    )
    filing_date = models.DateField(
        blank=True,
        verbose_name='filing date',
    )
    classifications = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='classifications',
    )
    country = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='country',
        help_text='Country or region',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date.verbose_name = 'issue date'
        self.date.help_text = 'Issue / Grant date'
        self.external_link.help_text = 'Link to patent'
        self.contributors.verbose_name = 'inventors'
        self.source.verbose_name = 'assignee'


# class Profile(models.Model):
#     """
#     Users can have many profiles and each profile links to one of the user's Cards.
#     """
#     share_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
#     connections = models.ManyToManyField(
#         'self',
#         through='Connection',
#         symmetrical=True
#     )
#
#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.title)
#         super(Profile, self).save(*args, **kwargs)
#
#     def get_absolute_url(self):
#         return reverse('profile', kwargs={'slug': self.slug})
#
#     def __str__(self):
#         return f'{self.user.username}\'s {self.title} Profile'
#
#     def get_shareable_url(self):
#         return reverse('shared_profile', kwargs={'share_uuid': self.share_uuid})


# class Connection(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     profile_from = models.ForeignKey(
#         Profile,
#         related_name='rel_from_set',
#         on_delete=models.CASCADE,
#     )
#     profile_to = models.ForeignKey(
#         Profile,
#         related_name='rel_to_set',
#         on_delete=models.CASCADE
#     )
#     card = models.OneToOneField(
#         Card,
#         on_delete=models.SET_NULL,
#         # in forms need to limit to card.user == profile.user
#         blank=True,
#         null=True,
#     )
#     created = models.DateTimeField(auto_now_add=True)
#
#     @property
#     def get_absolute_url(self):
#         return reverse('connection_detail', kwargs={'connection_id': self.id})
#
#     class Meta:
#         indexes = [
#             models.Index(fields=['-created']),
#         ]
#         ordering = ['-created']
#
#     def __str__(self):
#         return f'Connection {self.profile_from} -> {self.profile_to}'
