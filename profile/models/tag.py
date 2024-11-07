from django.db import models
from django.utils.translation import gettext_lazy as _

from . import profile as profile_models


class TagBase(profile_models.ItemBase):
    class Meta(profile_models.ItemBase.Meta):
        abstract = True

    def __str__(self):
        return str(self.label)


class Skill(TagBase):
    label = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='skill',
    )


class Interest(TagBase):
    label = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='interest',
    )


class Cause(TagBase):
    label = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='cause',
    )
    external_link = models.URLField(
        blank=True,
        verbose_name='external link',
    )
