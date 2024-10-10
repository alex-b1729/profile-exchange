import uuid
import os.path
import vobject
import datetime as dt
from urllib.parse import urlparse

from .fields import OrderField
from .utils import consts, vcard

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
from djangoyearlessdate.models import YearlessDateField
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


class Profile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    # individual, group, org...
    kind = models.CharField(
        max_length=1,
        choices=vcard.KIND_CHOICES,
        default=vcard.INDIVIDUAL_KIND
    )

    # -------- local info for the user --------
    title = models.CharField(max_length=50, blank=False)
    description = models.CharField(blank=True, null=True)

    # -------- info displayed on profile --------
    # todo: update for non-individual self.kind
    prefix = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=50, blank=True)
    # last name serves as name if kind is not individual
    last_name = models.CharField(max_length=50, blank=True)
    suffix = models.CharField(max_length=50, blank=True)
    nickname = models.CharField(max_length=50, blank=True)

    photo = models.ImageField(
        upload_to=consts.PROFILE_PHOTO_DIR,
        blank=True
    )

    headline = models.CharField(max_length=120, blank=True, null=True)
    location = models.CharField(max_length=50, blank=True, null=True)
    about = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('profile', kwargs={'profile_pk': self.pk})

    def __str__(self):
        return f'{self.user.username}\'s {self.title} Profile'

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
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': consts.CONTENT_TYPES
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['profile'])

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_related',
        on_delete=models.CASCADE,
    )
    content_related = GenericRelation(Content)
    label = models.CharField(max_length=50, blank=True)

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
class Email(ItemBase):
    type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        blank=True
    )
    email_address = models.EmailField()

    def __str__(self):
        return (f'{vcard.WH_TYPE_CHOICES[self.type] + ": " if self.type else ""}'
                f'{self.email_address}'
                f'{", " + self.label if self.label else ""}')


class Phone(ItemBase):
    type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        blank=True
    )
    phone_number = PhoneNumberField()

    def __str__(self):
        return (f'{vcard.WH_TYPE_CHOICES[self.type] + ": " if self.type else ""}'
                f'{self.phone_number}'
                f'{", " + self.label if self.label else ""}')


class Address(ItemBase):
    type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        blank=True
    )
    street1 = models.CharField(blank=False)
    street2 = models.CharField(blank=True)
    city = models.CharField(blank=False)
    state = models.CharField(blank=False)
    zip = models.CharField(max_length=10, blank=False)
    country = models.CharField(blank=True)

    class Meta(ItemBase.Meta):
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return (f'{vcard.WH_TYPE_CHOICES[self.type] + ": " if self.type else ""}'
                f'{self.street1}'
                f'{", " + self.label if self.label else ""}')


class LinkBase(models.Model):
    """holds primary domains and info for external links
    E.g. domain: https://github.com/"""
    title = models.CharField(blank=False, default='Website')
    domain = models.CharField(blank=True)
    svg_id = models.CharField(blank=False, default='web')

    def __str__(self):
        return str(self.title)


class Link(ItemBase):
    linkbase = models.ForeignKey(
        LinkBase,
        default=1,
        on_delete=models.SET_DEFAULT,
    )
    url = models.CharField(max_length=200)
    is_independent_url = models.BooleanField(
        help_text='Indicates url does not require linkbase.domain as the prefix'
    )

    class Meta(ItemBase.Meta):
        ordering = ['linkbase']

    def save(self, commit=True, *args, **kwargs):
        if self.is_independent_url is None:
            self.is_independent_url = self.linkbase == 1
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_independent_url:
            return str(self.url)
        else:
            return f'{self.linkbase.domain}{self.url}'

    @property
    def pretty_url(self):
        if self.is_independent_url:
            url = urlparse(str(self.url))
        else:
            url = urlparse(f'{self.linkbase.domain}{self.url}/')
        return f'{url.netloc}{url.path}{url.params}{url.query}{url.fragment}'.rstrip('/')


class Attachment(ItemBase):
    DOCUMENT = 'DOC'
    IMAGE = 'IMG'
    ATTACHMENT_TYPE_CHOICES = {
        DOCUMENT: 'Document',
        IMAGE: 'Image',
    }
    attachment_type = models.CharField(
        max_length=3,
        choices=ATTACHMENT_TYPE_CHOICES,
    )
    url = models.URLField(blank=True, null=True)
    file = models.FileField(
        upload_to=consts.ATTACHMENT_MODEL_DIR,
        blank=True,
    )

    def __str__(self):
        return (f'{self.ATTACHMENT_TYPE_CHOICES[self.attachment_type]}: '
                f'{self.url if self.url else self.file.name}')


class PostBase(ItemBase):
    title = models.CharField(
        max_length=200,
        blank=False, null=False,
        help_text='Title',
    )
    description = models.TextField(
        blank=True, null=True,
        help_text='Description',
    )
    date = models.DateField(
        blank=True, null=True,
        help_text='Date',
    )
    external_link = models.URLField(
        blank=True, null=True,
        help_text='External link',
    )

    class Meta(ItemBase.Meta):
        abstract = True
        ordering = ['-date']

    def __str__(self):
        return f'{self.title}{" - " + str(self.date) if self.date else ""}'


class OrgBase(PostBase):
    organization = models.CharField(
        max_length=200,
        blank=True, null=True,
    )

    class Meta(PostBase.Meta):
        abstract = True

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
    location = models.CharField(max_length=200, blank=True, null=True)
    # todo: dates should be more generic to allow just month and/or year
    end_date = models.DateField(blank=True, null=True)
    current = models.BooleanField(
        default=False,
        blank=True, null=True,
    )

    class Meta(OrgBase.Meta):
        abstract = True
        ordering = ['-end_date', '-date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title.help_text = 'Title or position'
        self.date.help_text = 'Start date'


class Membership(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class WorkExperience(MembershipBase):
    IN_PERSON = 'i'
    HYBRID = 'h'
    REMOTE = 'r'
    SETTING_TYPE_CHOICES = {
        IN_PERSON: 'In-person',
        HYBRID: 'Hybrid',
        REMOTE: 'Remote',
    }
    work_setting = models.CharField(
        max_length=1,
        choices=SETTING_TYPE_CHOICES,
        blank=True, null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Company or organization'
        self.external_link.help_text = 'Link to company'


class VolunteerWork(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class Education(MembershipBase):
    degree_type = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text="Associate, bachelor's, master's, etc."
    )
    gpa = models.FloatField(
        blank=True, null=True,
        help_text='GPA',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title.help_text = 'Major'
        self.date.help_text = 'Start date'
        self.location.help_text = 'School, university, location, etc.'
        self.end_date.help_text = 'Graduation or expected graduation date'


class ProjectBase(PostBase):
    contributors = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Contributors or co-authors',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Publication, journal, publisher, etc.',
    )

    class Meta(PostBase.Meta):
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_link.help_text = 'Link to source'


class Project(ProjectBase):
    pass


class PublishedWork(ProjectBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contributors.help_text = 'Authors'


class Patent(ProjectBase):
    PENDING = 'p'
    GRANTED = 'g'
    EXPIRED = 'e'
    STATUS_CHOICES = {
        PENDING: 'Pending',
        GRANTED: 'Granted',
        EXPIRED: 'Expired',
    }
    number = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text='Patent No.',
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        blank=True,
    )
    filing_date = models.DateField(
        blank=True, null=True,
        help_text='Filing date',
    )
    classification = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text='Classifications',
    )
    country = models.CharField(
        max_length=200,
        blank=True, null=True,
        help_text='Country or region',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date.help_text = 'Issue / Grant date'
        self.external_link.help_text = 'Link to patent'
        self.contributors.help_text = 'Inventor(s)'
        self.source.help_text = 'Assignee'


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
