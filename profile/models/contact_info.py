from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from . import profile as profile_models


# todo: validate all Items
class ContactInfoBase(profile_models.ItemBase):
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

    class Meta(profile_models.ItemBase.Meta):
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
        blank=False,
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
