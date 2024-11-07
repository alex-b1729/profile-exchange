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
    model_type = models.ForeignKey(
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
        help_text='Indicates url does not require model_type.netlock as the prefix',
    )

    class Meta(profile_models.ItemBase.Meta):
        ordering = ['model_type']
        verbose_name = 'link'
        verbose_name_plural = 'links'

    def __str__(self):
        if self.is_independent_url:
            return str(self.url)
        else:
            return f'{self.model_type.netloc}{self.url}'

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                model_type_title = getattr(self, 'model_type_title')
            except AttributeError:
                pass
            else:
                try:
                    self.model_type = LinkBase.objects.get(title=model_type_title)
                except LinkBase.DoesNotExist:
                    pass

        # always recheck and set is_indepenedent_url
        self.is_independent_url = self.model_type.pk == 1

        super().save(*args, **kwargs)

    @property
    def pretty_url(self):
        if self.is_independent_url:
            url = urlparse(str(self.url))
        else:
            url = urlparse(f'{self.model_type.netloc}{self.url}')
        return f'{url.netloc}{url.path}{url.params}{url.query}{url.fragment}'.rstrip('/')

    @staticmethod
    def model_type_initial(mode_type_name):
        try:
            return LinkBase.objects.get(title=mode_type_name)
        except LinkBase.DoesNotExist:
            pass
        return None

    @property
    def model_name(self):
        return self.model_type.title


def create_link_proxy_model(linkbase_title: str, verbose_name=None, verbose_name_plural=None):
    class CustomManager(models.Manager):
        def get_queryset(self, *args, **kwargs):
            return super().get_queryset(*args, **kwargs).filter(
                model_type__title=linkbase_title
            )

        # create isn't called on proxy model initiation so
        # LinkBase.objects.get() doesn't raise any warnings
        # when used within `ProxyModel = type(...)` I get this warning
        # RuntimeWarning: Accessing the database during app initialization is discouraged
        # see https://django.readthedocs.io/en/latest/ref/applications.html
        def create(self, *args, **kwargs):
            kwargs.update({'model_type': LinkBase.objects.get(title=linkbase_title)})
            return super().create(*args, **kwargs)

    meta_attribs = {'proxy': True}
    if verbose_name:
        meta_attribs['verbose_name'] = verbose_name
    if verbose_name_plural:
        meta_attribs['verbose_name_plural'] = verbose_name_plural

    # dynamic proxy model
    ProxyModel = type(
        f'{linkbase_title}',  # name of proxy model
        (Link,),              # base class
        {
            'objects': CustomManager(),
            '__module__': __name__,

            # gotta create this strange intermediate attribute which the
            # Link model then accesses and uses to set the Link.model_type
            # within Link.save()
            # This is the only way I was able to get the model_type saved
            # when calling ProxyModel.save()
            'model_type_title': linkbase_title,

            'Meta': type('Meta', (), meta_attribs),
        }
    )

    return ProxyModel


class Attachment(profile_models.ItemBase):
    class AttachmentTypes(models.TextChoices):
        DOCUMENT = 'd', _('Document')
        IMAGE = 'i', _('Image')

    model_type = models.CharField(
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
        return f'{"url: " + str(self.url) if self.url else self.file.name}'

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                self.model_type = getattr(self, 'model_type_title')
            except AttributeError:
                pass
        super().save(*args, **kwargs)

    @staticmethod
    def model_type_initial(model_type_name):
        return model_type_name

    @property
    def model_name(self):
        return self.AttachmentTypes(self.model_type).label

    @property
    def filename(self):
        return self.file.name.split('/')[-1]


def create_attachment_proxy_model(attachment_type):
    class CustomManager(models.Manager):
        def get_queryset(self, *args, **kwargs):
            return super().get_queryset(*args, **kwargs).filter(model_type=attachment_type)

        def create(self, *args, **kwargs):
            kwargs.update({'model_type': attachment_type})
            return super().create(*args, **kwargs)

    # dynamic proxy model
    ProxyModel = type(
        f'{Attachment.AttachmentTypes(attachment_type).label}',
        (Attachment,),
        {
            'objects': CustomManager(),
            '__module__': __name__,
            'model_type_title': attachment_type,
            'Meta': type('Meta', (), {'proxy': True}),
        }
    )

    return ProxyModel


# ---------------------------------------------------------------------
# Proxy models all go below this --------------------------------------
# ---------------------------------------------------------------------

# Links
Website = create_link_proxy_model('Website')
GitHub = create_link_proxy_model('GitHub', verbose_name='GitHub', verbose_name_plural='GitHubs')

# Attachments
Document = create_attachment_proxy_model(Attachment.AttachmentTypes.DOCUMENT)
Image = create_attachment_proxy_model(Attachment.AttachmentTypes.IMAGE)
