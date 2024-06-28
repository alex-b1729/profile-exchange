import uuid
import os.path
import datetime as dt

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from djangoyearlessdate.models import YearlessDateField
from phonenumber_field.modelfields import PhoneNumberField

# todo: add properties that return full vCard contentline


def vcard_img_dir_path(instance, filename):
    # todo: a uuid file name would be better
    return (f'users/{instance.user.id}{dt.datetime.now().strftime("%S%f")}'
            f'{os.path.splitext(filename)[-1]}')


class Vcard(models.Model):
    """
    Generally Vcard fields include vCard properties where cardinality is 1 or *1.
    E.g. where exactly on instance MUST / MAY be present.
    Fields with 1* or * are their own classes related to a vcard
    through a foreign key.
    But if my implementation allows only 1 instance per vcard then I include it here.
    """
    # todo: am I able to query other models linked to an instance of this model? To build the ADR etc.
    # todo: implement: SOUND 6.7.5, UUID .6, CLIENTPIDMAP .7
    BEGIN = 'VCARD'
    VERSION = '4.0'
    END = 'VCARD'
    SOURCE = ''  # uri
    XML = ''
    # todo: PRODID *1 should specify that this app made the vCard
    PRODID = 'ALEX\'S AWESOME APP!'

    INDIVIDUAL = 'individual'
    GROUP = 'group'
    ORG = 'org'
    LOCATION = 'location'
    KIND_CHOICES = {
        INDIVIDUAL: 'Individual',
        GROUP: 'Group',
        ORG: 'Organization',
        LOCATION: 'Location'
    }

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
    # note: cascading delete means that linked contact info disappears if other side leaves
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # 6.1.4
    # cardinality *1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.1.4
    kind = models.CharField(
        max_length=15,
        choices=KIND_CHOICES,
        default=INDIVIDUAL
    )

    # 6.2.1-3 Identification Properties
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2
    # use this instead of base user model first and last name
    prefix = models.CharField(max_length=50, blank=True)
    first_name = models.CharField(max_length=50, blank=True)
    middle_name = models.CharField(max_length=50, blank=True)
    # last name serves as name if kind is not individual
    last_name = models.CharField(max_length=50, blank=False)
    suffix = models.CharField(max_length=50, blank=True)

    # 6.2.3
    # cardinality: * - I coerce to *1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.3
    nickname = models.CharField(max_length=50, blank=True)

    # 6.2.4 Photo
    # cardinality: * - I coerce to *1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.4
    photo = models.ImageField(
        upload_to=vcard_img_dir_path,
        blank=True
    )

    # 6.2.5 BDAY
    # cardinality: *1
    # text allowed in specs but I coerce to datetime
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.5
    birthday = YearlessDateField(blank=True, null=True)
    birthday_year = models.PositiveSmallIntegerField(blank=True, null=True)

    # 6.2.6 Anniversary
    # cardinality: *1
    # text allowed in specs but I coerce to datetime
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.6
    anniversary = YearlessDateField(blank=True, null=True)
    anniversary_year = models.PositiveSmallIntegerField(blank=True, null=True)

    # 6.2.7 Gender
    # cardinality: *1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.7
    sex = models.CharField(max_length=1,
                           choices=GENDER_TYPE_CHOICES,
                           default=None,
                           null=True,
                           blank=True)
    gender = models.CharField(max_length=50, blank=True)

    # 6.7.2 Note
    # cardinality * - but I'm coercing to 1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.2
    note = models.CharField(blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        # todo: return vcard str here?
        return (f'vCard:{" (" + self.user.username + ")" if self.user is not None else ""} '
                f'{self.first_name} {self.last_name}')

    @property
    def FN(self):
        """
        6.2.1
        cardinality: 1* - I coerce to 1 for now
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.1
        """
        return (f'{self.prefix + " " if self.prefix!="" else ""}'
                f'{self.first_name + " " if self.first_name!="" else ""}'
                f'{self.middle_name + "" if self.middle_name!="" else ""}'
                f'{self.last_name}'
                f'{", " + self.suffix if self.suffix!="" else ""}')

    @property
    def N(self):
        """
        6.2.2
        cardinality: *1
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.2
        """
        return f'{self.user.last_name};{self.user.first_name};{self.middle_name};{self.prefix};{self.suffix}'

    @property
    def REV(self):
        # todo: should this be time of vCard export or last time a user updated a value of the model?
        return dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


class Address(models.Model):
    """
    6.3.1
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.3.1
    """
    # todo: type should accept user input / label
    WORK = 'WORK'
    HOME = 'HOME'
    OTHER = 'other'
    TYPE_CHOICES = {
        WORK: 'Work',
        HOME: 'Home',
        OTHER: 'Other'
    }
    vcard = models.ForeignKey(
        Vcard,
        related_name='addresses',
        on_delete=models.CASCADE
    )
    address_type = models.CharField(max_length=5,
                                    choices=TYPE_CHOICES,
                                    default=WORK,
                                    blank=True,
                                    null=True)
    # todo: idk about blank/null here. How will people want to hack these fields?
    street1 = models.CharField(blank=False)
    street2 = models.CharField(blank=True, null=True)
    city = models.CharField(blank=False)
    state = models.CharField(blank=False)
    zip = models.CharField(max_length=10, blank=False)  # todo: validate
    country = models.CharField(blank=True, null=True)

    class Meta:
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


class Phone(models.Model):
    """
    6.4.1
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
    """
    # todo: handle extensions
    EXT = ''
    # todo: type should accept user input / label
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
    vcard = models.ForeignKey(
        Vcard,
        related_name='phones',
        on_delete=models.CASCADE
    )
    phone_number = PhoneNumberField(blank=False)
    phone_type = models.CharField(max_length=10,
                                  choices=TYPE_CHOICES,
                                  default=CELL,
                                  null=True,
                                  blank=True)

    def __str__(self):
        return str(self.phone_number)

    @property
    def TEL(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
        """
        # todo: gotta format the number correctly
        return f'tel:{self.phone_number}{";" + self.EXT if self.EXT != "" else ""}'


class Email(models.Model):
    """
    6.4.2
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.2
    """
    WORK = 'WORK'
    HOME = 'HOME'
    OTHER = 'other'
    TYPE_CHOICES = {
        WORK: 'Work',
        HOME: 'Home',
        OTHER: 'Other'
    }
    vcard = models.ForeignKey(
        Vcard,
        related_name='emails',
        on_delete=models.CASCADE
    )
    email_type = models.CharField(max_length=5,
                                  choices=TYPE_CHOICES,
                                  default=None,
                                  null=True,
                                  blank=True)
    email_address = models.EmailField(blank=False)

    def __str__(self):
        return self.email_address


# todo: add IMPP, LAN, and geographical property class
# 6.4.3 - 6.5.2
# https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.3


class Organization(models.Model):
    """
    6.6
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.6
    """
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250, blank=True, null=True)
    role = models.CharField(max_length=250, blank=False)
    logo = models.ImageField(
        upload_to=vcard_img_dir_path,
        blank=True,
        null=True
    )
    organization = models.CharField(max_length=250, blank=True, null=True)
    work_url = models.URLField(blank=True, null=True)
    # todo: handle member and related
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.6.5
    # todo: add meta so this displays as something like "work" or "job" to users


class Tag(models.Model):
    """
    6.7.1 Categories
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.1
    Also known as "tags" so I'll use that here
    """
    # does it make most sense to have these associated with vcard or contact model?
    # vcard you can tag yourself but CATEGORIES isn't interpreted by Apple contacts
    # todo: user's will expect to easily query all the tags they've used
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    tag = models.CharField(max_length=30, blank=False)

    def __str__(self):
        return self.tag


class Url(models.Model):
    """
    6.7.8
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.8
    """
    # todo: really need a vcard LABEL associated with this
    # todo: when to export as X-SOCIALPROFILE vs URL?
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    url = models.URLField(blank=False)
    label = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.url)


# todo: implement security properties 6.8, KEY
# todo: implement Calendar Properties 6.9


class Profile(models.Model):
    """
    Contains information about a user that does not fit in the Vcard model.
    Users specify this info about themselves.
    """
    # todo: add attachments and CV/resume related fields
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    # X-HEADLINE
    headline = models.CharField(max_length=120, blank=True, null=True)
    # X-LOCATION
    location = models.CharField(max_length=80, blank=True, null=True)
    # X-DESCRIPTION
    description = models.CharField(blank=True, null=True)

    def __str__(self):
        return f'Profile: {self.user.username}'


class Contact(models.Model):
    """
    Every contact links to one vCard which is self.user's personal vcard of the Contact
    If self.profile is not None then it indicates the contact is linked to a connection

    Notes:
        - The same profile will be linked to multiple user's
        - Each Contact links to one, unique Vcard
        - The same Profile will link to multiple Vcards
        - BUT, a user can only link a Profile to one Contact.
          E.g. Contacts are unique on (user, profile) as enforced
          by the unique_user_connection constraint.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    vcard = models.OneToOneField(
        Vcard,
        on_delete=models.CASCADE
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'profile'],
                name='unique_user_connection',
                nulls_distinct=True
            )
        ]

    def __str__(self):
        return f'Contact: {self.user.username} -> {self.vcard.FN}'


class ContactNote(models.Model):
    # todo: naming? This'll will get confusing with Vcard.note
    # todo: would be fun to have tags associated with these
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
    )
    note = models.CharField(blank=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'{self.note[:50]}{"..." + len(self.note-50) if len(self.note>51) else ""}'


"""
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
"""
