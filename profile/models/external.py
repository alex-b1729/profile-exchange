from urllib.parse import urlparse

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..utils import consts
from . import profile as profile_models


class LinkBase(models.Model):
    """holds primary domains and info for external links
    E.g. netloc: https://github.com/"""
    title = models.CharField(
        blank=False,
        unique=True,
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


class Link(profile_models.ItemBase):
    linkbase = models.ForeignKey(
        LinkBase,
        default=1,
        blank=False,
        on_delete=models.SET_DEFAULT,
        verbose_name='linkbase',
        related_name='links',
        related_query_name='link',
    )
    url = models.CharField(
        blank=False,
        max_length=200,
        verbose_name='url',
    )
    is_independent_url = models.BooleanField(
        default=True,
        blank=False,
        verbose_name='independent url',
        help_text='Indicates url does not require linkbase.netlock as the prefix',
    )

    class Meta(profile_models.ItemBase.Meta):
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


# proxy models as outlined in this SO answer
# https://stackoverflow.com/a/60853449
class WebsiteManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            linkbase=LinkBase.objects.get(title='Website').pk
        )

    def create(self, *args, **kwargs):
        kwargs.update({'linkbase': LinkBase.objects.get(title='Website').pk})
        return super().create(*args, **kwargs)


class Website(Link):
    objects = WebsiteManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.linkbase = LinkBase.objects.get(title='Website').pk
        return super().save(*args, **kwargs)


class GithubManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(
            linkbase=LinkBase.objects.get(title='GitHub').pk
        )

    def create(self, *args, **kwargs):
        kwargs.update({'linkbase': LinkBase.objects.get(title='GitHub').pk})
        return super().create(*args, **kwargs)


class Github(Link):
    objects = GithubManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.linkbase = LinkBase.objects.get(title='GitHub').pk
        return super().save(*args, **kwargs)


class Attachment(profile_models.ItemBase):
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
