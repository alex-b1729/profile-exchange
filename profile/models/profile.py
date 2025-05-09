import uuid
import inspect

from django.apps import apps
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.sites.models import Site
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

    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=True,
    )

    requests_made = models.ManyToManyField(
        'self',
        through='ConnectionRequest',
        related_name='requests_of',
        symmetrical=False,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'profile'
        verbose_name_plural = 'profiles'

    def save(self, *args, **kwargs):
        # create a default link when saving new profile
        if not self.pk:
            new_profile = super().save()
            share_link = ProfileLink(
                label='Default',
                profile=self,
            )
            share_link.save()
        else:
            super().save()

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

    # could also get model__in dynamically using this SO answer
    # although I haven't tested that it works here
    # https://stackoverflow.com/a/38896959
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': consts.CONTENT_TYPES,
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['profile'])

    class Meta:
        ordering = ['order']
        verbose_name = 'content'
        verbose_name_plural = 'contents'

    def __str__(self):
        return str(self.item)


class ContentContent(models.Model):
    """Relationship from a profile content item to a sub-item"""
    content = models.ForeignKey(
        Content,
        related_name='subcontents',
        related_query_name='contentcontent',
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': consts.CONTENT_TYPES,
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['content'])

    class Meta:
        ordering = ['order']

    def __str__(self):
        return str(self.item)


class ItemBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_related',
        on_delete=models.CASCADE,
    )
    content_related = GenericRelation(Content)
    subcontent_related = GenericRelation(ContentContent)
    label = models.CharField(max_length=50, blank=True, verbose_name='label')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def render(self):
        cls_name = self.__class__.__name__
        parent_cls_name = inspect.getmro(self.__class__)[1].__name__
        grandparent_cls_name = inspect.getmro(self.__class__)[2].__name__
        return render_to_string(
            [
                f'profile/partials/models/{cls_name.lower()}_render.html',
                f'profile/partials/models/{parent_cls_name.lower()}_render.html',
                f'profile/partials/models/{grandparent_cls_name.lower()}_render.html',
                f'profile/partials/models/model_render.html',
            ],
            {'object': self}
        )

    @property
    def model_name(self):
        return self.__class__.__name__


class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_expired=False)


class ProfileLink(models.Model):
    label = models.CharField(
        blank=False,
        max_length=200,
        verbose_name='label',
    )
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='links',
        related_query_name='link',
    )
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(
        blank=True,
        null=True,
        default=None,
    )
    last_viewed = models.DateTimeField(auto_now=True)

    max_views = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='maximum number of views'
    )
    views = models.IntegerField(default=0, null=False)

    is_expired = models.BooleanField(
        editable=False,
        null=False,
    )

    objects = models.Manager()
    active = ActiveManager()

    class Meta:
        ordering = ['-created']
        verbose_name = 'profile link'
        verbose_name_plural = 'profile links'

    def save(self, *args, **kwargs):
        self.is_expired = self.calculate_expired
        super().save(*args, **kwargs)

    def get_shareable_url(self):
        return f"{Site.objects.get_current()}{reverse('shared_profile', kwargs={'uid': self.uid})}"

    def record_view(self):
        self.views += 1
        self.save()

    @property
    def views_expired(self):
        return self.max_views is not None and self.views >= self.max_views

    @property
    def time_expired(self):
        return self.expires is not None and timezone.now() >= self.expires

    @property
    def calculate_expired(self):
        return self.views_expired or self.time_expired


class Connection(models.Model):
    profile_from = models.ForeignKey(
        Profile,
        related_name='rel_from_set',
        on_delete=models.CASCADE,
    )
    profile_to = models.ForeignKey(
        Profile,
        related_name='rel_to_set',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'{self.profile_from} -> {self.profile_to}'

    def get_absolute_url(self):
        return reverse('connection', kwargs={'connection_pk': self.pk})


class RequestStatus(models.TextChoices):
    OUTSTANDING = 'o', _('Outstanding')
    ACCEPTED = 'a', _('Accepted')
    DECLINED = 'd', _('Declined')


class OutstandingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.OUTSTANDING)


class AcceptedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.ACCEPTED)


class DeclinedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=RequestStatus.DECLINED)


class ConnectionRequest(models.Model):
    profile_from = models.ForeignKey(
        Profile,
        related_name='request_from_set',
        on_delete=models.CASCADE,
    )
    profile_to = models.ForeignKey(
        Profile,
        related_name='request_to_set',
        on_delete=models.CASCADE,
    )
    message = models.CharField(
        max_length=200,
        blank=True,
    )
    requested = models.DateTimeField(
        auto_now_add=True,
    )
    status = models.CharField(
        max_length=1,
        choices=RequestStatus,
        default=RequestStatus.OUTSTANDING,
    )
    updated = models.DateTimeField(
        auto_now=True,
    )

    objects = models.Manager()
    outstanding = OutstandingManager()
    accepted = AcceptedManager()
    declined = DeclinedManager()

    class Meta:
        ordering = ('-requested',)

    def __str__(self):
        return f'{self.profile_from} requested to follow {self.profile_to}'

    def accept(self):
        self.status = RequestStatus.ACCEPTED
        self.save()
        self.profile_from.connections.add(self.profile_to)

    def decline(self):
        self.status = RequestStatus.DECLINED
        self.save()
