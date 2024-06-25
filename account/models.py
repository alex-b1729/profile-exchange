import uuid
import os.path
import datetime as dt

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField

# todo: add properties that return full vCard contentline


def profile_photo_dir_path(instance, filename):
    return (f'users/{instance.user.id}{dt.datetime.now().strftime("%S%f")}'
            f'{os.path.splitext(filename)[-1]}')


class Profile(models.Model):
    MALE = 'M'
    FEMAIL = 'F'
    OTHER = 'O'
    NONE = 'N'
    UNKNOWN = 'U'
    GENDER_TYPE_CHOICES = {
        MALE: 'Male',
        FEMAIL: 'Female',
        OTHER: 'Other',
        NONE: 'Not Applicable',
        UNKNOWN: 'Unknown'
    }
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    # 6.2.1-3 Identification Properties
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2
    # extend base user model's name
    prefix = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(blank=True)
    suffix = models.CharField(max_length=50, blank=True)
    nick_name = models.CharField(blank=True)

    # 6.2.4 Photo
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.4
    photo = models.ImageField(
        upload_to=profile_photo_dir_path,
        blank=True
    )

    home_page = models.URLField(blank=True)

    # 6.6 Organizational Properties
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.6
    organization = models.CharField(max_length=250, blank=True)
    title = models.CharField(max_length=250, blank=True)
    role = models.CharField(max_length=250, blank=True)
    work_url = models.URLField(blank=True)
    # logo

    # X-HEADLINE
    headline = models.CharField(max_length=50, blank=True)
    # X-LOCATION
    location = models.CharField(max_length=50, blank=True)

    # 6.2.5 BDAY
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.5
    birthday = models.DateField(blank=True, null=True)

    # 6.2.6 Anniversary
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.6
    anniversary = models.DateField(blank=True, null=True)

    # 6.2.7 Gender
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.7
    sex = models.CharField(max_length=20,
                           choices=GENDER_TYPE_CHOICES,
                           default=None,
                           null=True,
                           blank=True)
    gender = models.CharField(max_length=25, blank=True)

    def __str__(self):
        return f'Profile of {self.user.first_name} {self.user.last_name}'

    @property
    def FN(self):
        """
        Required
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.1
        """
        return (f'{self.prefix} {self.user.first_name} {self.middle_name} {self.user.last_name}'
                f'{", " if self.suffix != "" else ""}{self.suffix}')

    @property
    def N(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.2
        """
        return f'{self.user.last_name};{self.user.first_name};{self.middle_name};{self.prefix};{self.suffix}'


class EmailAddress(models.Model):
    WORK = 'WORK'
    HOME = 'HOME'
    OTHER = 'other'
    TYPE_CHOICES = {
        WORK: 'Work',
        HOME: 'Home',
        OTHER: 'Other'
    }
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='email_addresses',
        on_delete=models.CASCADE
    )
    email_type = models.CharField(max_length=20,
                                  choices=TYPE_CHOICES,
                                  default=WORK)
    email_address = models.EmailField()
    confirmed = models.BooleanField(default=False, null=False)
    is_primary = models.BooleanField(null=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Email Addresses'

    def __str__(self):
        return self.email_address


class Phone(models.Model):
    # todo: handle extensions
    CELL = 'CELL'
    WORK = 'WORK VOICE'
    HOME = 'HOME VOICE'
    WORK_FAX = 'WORK FAX'
    HOME_FAX = 'HOME FAX'
    PAGER = 'PAGER'
    OTHER = 'other'
    TYPE_CHOICES = {
        CELL: 'Cell',
        WORK: 'Work',
        HOME: 'Home',
        WORK_FAX: 'Work Fax',
        HOME_FAX: 'Home Fax',
        PAGER: 'Pager',
        OTHER: 'Other'
    }
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='phone_numbers',
        on_delete=models.CASCADE
    )
    phone_number = PhoneNumberField(blank=False)
    phone_type = models.CharField(max_length=20,
                                  choices=TYPE_CHOICES,
                                  default=CELL)

    def __str__(self):
        return str(self.phone_number)

    @property
    def TEL(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
        """
        # todo: gotta format the number correctly
        return self.phone_number


class PostalAddress(models.Model):
    WORK = 'WORK'
    HOME = 'HOME'
    OTHER = 'other'
    TYPE_CHOICES = {
        WORK: 'Work',
        HOME: 'Home',
        OTHER: 'Other'
    }
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='postal_addresses',
        on_delete=models.CASCADE
    )
    address_type = models.CharField(max_length=20,
                                    choices=TYPE_CHOICES,
                                    default=WORK)
    street1 = models.CharField()
    street2 = models.CharField(blank=True)
    city = models.CharField()
    state = models.CharField()
    zip = models.CharField(max_length=10)
    country = models.CharField(blank=True)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        s = (f'{self.street1 + ", " if self.street1 != "" else ""}'
             f'{self.street2 + ", " if self.street2 != "" else ""}'
             f'{self.city + ", " if self.city != "" else ""}'
             f'{self.state + " " if self.state != "" else ""}'
             f'{self.zip if self.zip != "" else ""}')
        return s

    @property
    def ADR(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.3.1
        First 2 components have interoperability issues and SHOULD be empty according to specs
        """
        return (f';;{self.street1}{"," if self.street2 != "" else ""}{self.street2};'
                f'{self.city};{self.state};{self.zip};{self.country}')


class SocialProfile(models.Model):
    # todo: add label
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='social_profiles',
        on_delete=models.CASCADE
    )
    url = models.URLField()

    def __str__(self):
        return str(self.url)


class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rel_from_set',
        on_delete=models.CASCADE,
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rel_to_set',
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse('connection_detail', kwargs={'connection_id': self.id})

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'Connection {self.user_from} -> {self.user_to}'


# Add following field to User dynamically
user_model = get_user_model()
user_model.add_to_class(
    'connections',
    models.ManyToManyField(
        'self',
        through=Connection,
        symmetrical=True,
    ),
)
