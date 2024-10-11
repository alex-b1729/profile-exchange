from django.apps import apps
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

from ..utils import consts
from ..fields import OrderField


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
