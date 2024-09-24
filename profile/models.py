import uuid
import os.path
import vobject
import datetime as dt

from .fields import OrderField
from .utils import consts, vcard

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Value
from django.http import HttpResponse
from django.utils.text import slugify
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
        return reverse('profile', kwargs={'pk': self.pk})

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
            'model__in': consts.PROFILE_CONTENTS
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
        return str(self.email_address)


class Phone(ItemBase):
    type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        blank=True
    )
    phone_number = PhoneNumberField()


class Link(ItemBase):
    type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        blank=True
    )
    url = models.URLField()


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

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f'{self.street1}'


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
