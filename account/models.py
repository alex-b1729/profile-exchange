import uuid
import os.path
import datetime as dt

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models import Value
from django.http import HttpResponse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djangoyearlessdate.models import YearlessDateField
from phonenumber_field.modelfields import PhoneNumberField

# todo: worth understanding how popular systems parse vcards
# https://alessandrorossini.org/the-sad-story-of-the-vcard-format-and-its-lack-of-interoperability/


WORK = 'WORK'
HOME = 'HOME'
OTHER = 'other'
TYPE_WH_CHOICES = {
    WORK: 'Work',
    HOME: 'Home',
    OTHER: 'Other'
}


def vcard_img_dir_path(instance, filename):
    # todo: a uuid file name would be better
    return (f'users/{filename}')


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
    PRODID = ''

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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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
                f'{self.middle_name + " " if self.middle_name!="" else ""}'
                f'{self.last_name}'
                f'{", " + self.suffix if self.suffix!="" else ""}')

    @property
    def N(self):
        """
        6.2.2
        cardinality: *1
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.2
        """
        return f'{self.last_name};{self.first_name};{self.middle_name};{self.prefix};{self.suffix}'

    @property
    def REV(self):
        # todo: should this be time of vCard export or last time a user updated a value of the model?
        return dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    @property
    def vcf(self):
        """
        return formatted vcard
        I'm choosing to add newline chars at end of each property.
        """
        # todo: implement line folding over 75 chars as outlined in
        # https://datatracker.ietf.org/doc/html/rfc6350#section-3.2
        s = f'BEGIN:{self.BEGIN}\n'
        s += f'VERSION:{self.VERSION}\n'
        s += f'KIND:{self.kind}\n'
        s += f'FN:{self.FN}\n'
        s += f'N:{self.N}\n'
        if self.nickname!='':
            s += f"{'NICKNAME:' + self.nickname if self.nickname!='' else ''}\n"

        # todo: photo encoding

        # TODO: date w/o year won't be interpreted by Apple contacts
        if self.birthday is not None:
            year = str(self.birthday_year) if self.birthday_year is not None else '--'
            bday = f'{self.birthday.month:02}{self.birthday.day:02}'
            s += f'BDAY:{year}{bday}\n'

        if self.anniversary is not None:
            year = str(self.anniversary_year) if self.anniversary_year is not None else '--'
            anniv = f'{self.anniversary.month:02}{self.anniversary.day:02}'
            s += f'BDAY:{year}{anniv}\n'

        if self.sex is not None or self.gender!='':
            s += (f'GENDER:{self.sex if self.sex is not None else ""}'
                  f'{";" + self.gender if self.gender!="" else ""}\n')

        s += ''.join([f'ADR{adr.ADR}\n' for adr in self.address_set.all()])
        s += ''.join([f'TEL{tel.TEL}\n' for tel in self.phone_set.all()])
        s += ''.join([f'EMAIL{email.EMAIL}\n' for email in self.email_set.all()])
        s += ''.join([org.formatted_organizational_properties for org in self.organization_set.all()])
        s += ''.join([f'URL{url.URL}\n' for url in self.url_set.all()])

        s += f'NOTE:{self.note}\n' if self.note!='' else ''

        categories = [cat.CATEGORIES for cat in self.tag_set.all()]
        if categories != []:
            s += f'CATEGORIES:{",".join(categories)}\n'

        s += f'REV:{self.REV}\n'
        s += f'END:{self.END}'

        return s

    def vcf_http_reponse(self, request):
        # todo: downloading will involve the linked vcard as well
        return HttpResponse(
            ContentFile(self.vcf),
            headers={
                'Content-Type': 'text/plain',
                'Content-Disposition': f'attachment; filename="{self.FN}.vcf"'
            }
        )


class Address(models.Model):
    """
    6.3.1
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.3.1
    """
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    address_type = models.CharField(max_length=5,
                                    choices=TYPE_WH_CHOICES,
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
        s = (f'{self.street1}')
        return s

    @property
    def ADR(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.3.1
        First 2 components have interoperability issues and SHOULD be empty according to specs
        """
        return (f'{";TYPE=" + self.address_type if self.address_type not in ["", "other"] else ""}:'
                f';;{self.street1}{"," + self.street2 if self.street2 is not None else ""};'
                f'{self.city};{self.state};{self.zip};{self.country if self.country is not None else ""}')


class Phone(models.Model):
    """
    6.4.1
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
    """
    # todo: handle extensions
    EXT = ''

    CELL = 'CELL'
    WORK = 'WORK'
    HOME = 'HOME'
    VOICE = 'VOICE'
    TEXT = 'TEXT'
    FAX = 'FAX'
    PAGER = 'PAGER'
    OTHER = 'other'
    TYPE_CHOICES = {
        CELL: 'Cell',
        WORK: 'Work',
        HOME: 'Home',
        VOICE: 'Voice',
        TEXT: 'Text',
        FAX: 'Fax',
        PAGER: 'Pager',
        OTHER: 'Other'
    }
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    phone_number = PhoneNumberField(blank=False)
    phone_type = models.CharField(
        max_length=5,
        choices=TYPE_CHOICES,
        default=CELL,
        null=True,
        blank=True
    )

    def __str__(self):
        return str(self.phone_number)

    @property
    def TEL(self):
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
        """
        # todo: gotta format the number correctly
        return (f'{";TYPE=" + self.phone_type if self.phone_type not in ["", "other"] else ""}:'
                f'{self.phone_number}{";ext=" + self.EXT if self.EXT != "" else ""}')


class Email(models.Model):
    """
    6.4.2
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.2
    """
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    email_type = models.CharField(max_length=5,
                                  choices=TYPE_WH_CHOICES,
                                  default=None,
                                  null=True,
                                  blank=True)
    email_address = models.EmailField(blank=False)

    def __str__(self):
        return self.email_address

    @property
    def EMAIL(self):
        return (f'{";TYPE=" + self.email_type if self.email_type not in [None, "", "other"] else ""}:'
                f'{self.email_address}')


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
    role = models.CharField(max_length=250, blank=True, null=True)
    logo = models.ImageField(
        upload_to=vcard_img_dir_path,
        blank=True,
        null=True
    )
    organization = models.CharField(max_length=250, blank=True, null=True)
    # todo: handle member and related
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.6.5
    # todo: add meta so this displays as something like "work" or "job" to users

    @property
    def formatted_organizational_properties(self):
        # todo: add encoded logo
        s = f'TITLE:{self.title}\n' if self.title!='' else ''
        s += f'ROLL:{self.role}\n' if self.role!='' else ''
        s += f'ORG:{self.organization}\n' if self.organization!='' else ''
        return s


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

    @property
    def CATEGORIES(self):
        return str(self.tag)


class Url(models.Model):
    """
    6.7.8
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.8
    """
    vcard = models.ForeignKey(
        Vcard,
        on_delete=models.CASCADE
    )
    url = models.URLField(blank=False)
    url_type = models.CharField(
        max_length=5,
        choices=TYPE_WH_CHOICES,
        default=None,
        null=True,
        blank=True
    )
    label = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return str(self.url)

    @property
    def URL(self):
        # todo: when to export as X-SOCIALPROFILE vs URL?
        return (f'{";TYPE=" + self.url_type if self.url_type not in [None, "", "other"] else ""}:'
                f'{self.url}')


# todo: implement security properties 6.8, KEY
# todo: implement Calendar Properties 6.9


class Profile(models.Model):
    """
    Users can have many profiles and each profile links to one of the user's vcards.
    """
    # todo: add attachments and CV/resume related fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    vcard = models.OneToOneField(
        Vcard,
        on_delete=models.CASCADE,
    )

    # eventually use this to differentiate different profiles for same user
    # e.g. personal, professional, business, etc.
    title = models.CharField(max_length=50, default='Personal')

    # X-HEADLINE
    headline = models.CharField(max_length=120, blank=True, null=True)
    # X-LOCATION
    location = models.CharField(max_length=80, blank=True, null=True)
    # X-DESCRIPTION
    description = models.CharField(blank=True, null=True)

    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=True
    )

    def __str__(self):
        return f'{self.user.username}\'s {self.title} Profile'


class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    vcard = models.OneToOneField(
        Vcard,
        on_delete=models.SET_NULL,
        # in forms need to limit to vcard.user == profile.user
        blank=True,
        null=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    @property
    def get_absolute_url(self):
        return reverse('connection_detail', kwargs={'connection_id': self.id})

    class Meta:
        indexes = [
            models.Index(fields=['-created']),
        ]
        ordering = ['-created']

    def __str__(self):
        return f'Connection {self.profile_from} -> {self.profile_to}'
