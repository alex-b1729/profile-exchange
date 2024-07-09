import uuid
import os.path
import vobject
import datetime as dt

from .utils import consts, vcard

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


class Card(models.Model):
    """
    Generally Card fields include vCard properties where cardinality is 1 or *1.
    E.g. where exactly on instance MUST / MAY be present.
    Fields with 1* or * are their own classes related to a Card through a foreign key.
    But if my implementation allows only 1 instance per Card then I include it here.
    """
    # todo: implement: SOUND 6.7.5, UUID .6, CLIENTPIDMAP .7
    # map vcard property names to Card attribute names
    # _repr for single object, _yield for an iterator of objects
    PROPERTY_TO_ATTR = {
        'KIND': 'KIND_repr',
        'FN': 'FN_repr',
        'N': 'N_repr',
        'NICKNAME': 'NICKNAME_repr',
        # 'PHOTO': 'photo',  # todo: implement imgs
        'BDAY': 'BDAY_repr',
        'ANNIVERSARY': 'ANNIVERSARY_repr',
        'GENDER': 'GENDER_repr',
        'ADR': 'ADR_repr',
        'TEL': 'TEL_repr',
        'EMAIL': 'EMAIL_repr',
        'TITLE': 'TITLE_repr',
        'ROLE': 'ROLE_repr',
        # 'LOGO': 'LOGO_yield',
        'ORG': 'ORG_repr',
        # 'MEMBER': 'MEMBER_yield',
        # 'RELATED': 'RELATED_yield',
        'NOTE': 'NOTE_repr',
        'CATEGORY': 'TAG_repr',
        'URL': 'URL_repr',
        'REV': 'REV_repr'
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
        max_length=1,
        choices=vcard.KIND_CHOICES,
        default=vcard.INDIVIDUAL_KIND
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
        upload_to=consts.PROFILE_PHOTO_DIR,
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
                           choices=vcard.GENDER_TYPE_CHOICES,
                           default='',
                           blank=True)
    gender = models.CharField(max_length=50, blank=True)

    # 6.7.2 Note
    # cardinality * - but I'm coercing to 1
    # https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.2
    note = models.CharField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        u_str = '__UNDEFINED__'
        if hasattr(self, 'user'):
            u_str = self.user.username
        return (f'({u_str}) {self.first_name} {self.last_name}')


    @property
    def KIND_repr(self) -> list[dict[str]]:
        return [{'value': vcard.KIND_CHOICES[self.kind]}]

    @property
    def FN(self) -> str:
        val = (f'{self.prefix + " " if self.prefix != "" else ""}'
               f'{self.first_name + " " if self.first_name != "" else ""}'
               f'{self.middle_name + " " if self.middle_name != "" else ""}'
               f'{self.last_name}'
               f'{", " + self.suffix if self.suffix != "" else ""}')
        return val

    @property
    def FN_repr(self) -> list[dict[str]]:
        """
        6.2.1
        cardinality: 1* - I coerce to 1 for now
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.1
        """
        return [{'value': self.FN}]

    @property
    def N_repr(self) -> list[dict[str]]:
        """
        6.2.2
        cardinality: *1
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.2.2
        """
        n = vobject.vcard.Name(prefix=self.prefix,
                               given=self.first_name,
                               additional=self.middle_name,
                               family=self.last_name,
                               suffix=self.suffix)
        return [{'value': n}]

    @property
    def NICKNAME_repr(self) -> list[dict[str]]:
        n = []
        if self.nickname != '':
            n = [{'value': self.nickname}]
        return n

    @property
    def BDAY_repr(self) -> list[dict[str]]:
        ret_l = []
        if self.birthday is not None:
            d = {}
            d['value'] = vcard.generate_vcard_date(self.birthday, self.birthday_year)
            if self.birthday_year is None:
                d['X-APPLE-OMIT-YEAR'] = '1604'
            ret_l.append(d)
        return ret_l

    @property
    def ANNIVERSARY_repr(self) -> list[dict[str]]:
        ret_l = []
        if self.anniversary is not None:
            d = {}
            d['value'] = vcard.generate_vcard_date(self.anniversary, self.anniversary_year)
            if self.anniversary_year is None:
                d['X-APPLE-OMIT-YEAR'] = vcard.X_APPLE_OMIT_YEAR
            ret_l.append(d)
        return ret_l

    @property
    def GENDER_repr(self) -> list[dict[str]]:
        ret_l = []
        if self.sex != '' or self.gender != '':
            ret_l.append({'value': vcard.generate_gender(self.sex, self.gender)})
        return ret_l

    @property
    def ADR_repr(self) -> iter:
        adrs = self.address_set.all()
        return [adr.ADR_repr for adr in adrs]

    @property
    def TEL_repr(self) -> iter:
        tels = self.phone_set.all()
        return [tel.TEL_repr for tel in tels]

    @property
    def EMAIL_repr(self) -> iter:
        emails = self.email_set.all()
        return [email.EMAIL_repr for email in emails]

    @property
    def TITLE_repr(self) -> iter:
        ts = self.title_set.all()
        return [t.TITLE_repr for t in ts]

    @property
    def ROLE_repr(self) -> iter:
        rs = self.role_set.all()
        return [r.ROLE_repr for r in rs]

    @property
    def ORG_repr(self) -> iter:
        orgs = self.org_set.all()
        return [{'value': [str(org) for org in orgs]}]

    @property
    def NOTE_repr(self) -> dict[str]:
        ret_l = []
        if self.note != '':
           ret_l.append({'value': self.note})
        return ret_l

    @property
    def TAG_repr(self) -> list:
        ts = self.tag_set.all()
        if ts:
            return [{'value': [t.tag for t in ts]}]
        else:
            return []

    @property
    def URL_repr(self):
        us = self.url_set.all()
        return [u.URL_repr for u in us]

    @property
    def REV_repr(self):
        # todo: should this be time of vCard export or last time a user updated a value of the model?
        yield {'value': dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}

    def to_vcard(self) -> str:
        """
        returns str in vCard format from Card
        """
        # todo: caching this data when a vcard view is loaded?
        v = vobject.vCard()
        for prop_name, attr in self.PROPERTY_TO_ATTR.items():
            prop_list = getattr(self, attr)
            if prop_list:
                prop = v.add(prop_name)
                if prop_name == 'ORG':
                    print(prop)
                    print(prop_list)
                for prop_kv in prop_list:
                    for k, val in prop_kv.items():
                        setattr(prop, k, val)
                        if prop_name == 'ORG':
                            print(prop)
        return v.serialize()

    def vcf_http_reponse(self, request):
        # todo: downloading will involve the linked vcard as well
        return HttpResponse(
            ContentFile(self.to_vcard()),
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
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    address_type = models.CharField(max_length=1,
                                    choices=vcard.WH_TYPE_CHOICES,
                                    default=vcard.WORK,
                                    blank=True)
    # todo: idk about blank/null here. How will people want to hack these fields?
    street1 = models.CharField(blank=False)
    street2 = models.CharField(blank=True)
    city = models.CharField(blank=False)
    state = models.CharField(blank=False)
    zip = models.CharField(max_length=10, blank=False)  # todo: validate
    country = models.CharField(blank=True)

    class Meta:
        verbose_name_plural = 'Addresses'

    def __str__(self):
        s = (f'{self.street1}')
        return s

    @property
    def ADR_repr(self) -> dict[str]:
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.3.1
        First 2 components have interoperability issues and SHOULD be empty according to specs
        """
        d = {}
        adr = vobject.vcard.Address(street=f'{self.street1}{", " + self.street2 if self.street2!="" else ""}',
                                    city=self.city,
                                    region=self.state,
                                    code=str(self.zip),
                                    country=self.country)
        d['value'] = adr
        if self.address_type not in ['', 'other']:
            d['type_param'] = vcard.WH_TYPE_CHOICES[self.address_type]
        return d


class Phone(models.Model):
    """
    6.4.1
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
    """
    # todo: handle extensions
    EXT = ''

    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    phone_number = PhoneNumberField(blank=False)
    phone_type = models.CharField(
        max_length=1,
        choices=vcard.PHONE_TYPE_CHOICES,
        default=vcard.CELL,
        blank=True
    )

    def __str__(self):
        return str(self.phone_number)

    @property
    def TEL_repr(self) -> dict[str]:
        """
        https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.1
        """
        # todo: gotta format the number correctly
        d = {}
        d['value'] = str(self.phone_number)
        if self.phone_type not in ['', 'other']:
            d['type_param'] = vcard.PHONE_TYPE_CHOICES[self.phone_type]
        return d


class Email(models.Model):
    """
    6.4.2
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.2
    """
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    email_type = models.CharField(max_length=1,
                                  choices=vcard.WH_TYPE_CHOICES,
                                  default=None,
                                  blank=True)
    email_address = models.EmailField(blank=False)

    def __str__(self):
        return self.email_address

    @property
    def EMAIL_repr(self):
        d = {}
        d['value'] = self.email_address
        d['type_param'] = ['INTERNET']
        if self.email_type not in ['', 'other']:
            d['type_param'].append(vcard.WH_TYPE_CHOICES[self.email_type])
        return d


# todo: add IMPP, LAN, and geographical property class
# 6.4.3 - 6.5.2
# https://datatracker.ietf.org/doc/html/rfc6350#section-6.4.3


class Title(models.Model):
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    # group = models.CharField(max_length=20, blank=True)  # for compatibility with group prefix
    title = models.CharField(max_length=100)

    def __str__(self):
        return str(self.title)

    @property
    def TITLE_repr(self):
        return {'value': self.title}


class Role(models.Model):
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    # group = models.CharField(max_length=20, blank=True)  # for compatibility with group prefix
    role = models.CharField(max_length=100)

    def __str__(self):
        return str(self.role)
    @property
    def ROLE_repr(self):
        return {'value': self.role}


class Org(models.Model):
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    # group = models.CharField(max_length=20, blank=True)  # for compatibility with group prefix
    organization = models.CharField(max_length=100)

    def __str__(self):
        return str(self.organization)
    @property
    def ORG_repr(self):
        return {'value': self.organization}


class Tag(models.Model):
    """
    6.7.1 Categories
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.1
    Also known as "tags" so I'll use that here
    """
    # does it make most sense to have these associated with Card or contact model?
    # vCard you can tag yourself but CATEGORIES isn't interpreted by Apple contacts
    # todo: user's will expect to easily query all the tags they've used
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    tag = models.CharField(max_length=30, blank=False)

    def __str__(self):
        return self.tag

    @property
    def CATEGORY_repr(self):
        return {'value': self.tag}


class Url(models.Model):
    """
    6.7.8
    cardinality: *
    https://datatracker.ietf.org/doc/html/rfc6350#section-6.7.8
    """
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    url = models.URLField(blank=False)
    url_type = models.CharField(
        max_length=1,
        choices=vcard.WH_TYPE_CHOICES,
        default=None,
        blank=True
    )
    label = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return str(self.url)

    @property
    def URL_repr(self):
        # todo: when to export as X-SOCIALPROFILE vs URL?
        d = {}
        d['value'] = self.url
        type_list = [str(s) for s in [vcard.WH_TYPE_CHOICES[self.url_type], self.label] if s not in ['', 'none']]
        if len(type_list) != 0:
            d['type_param'] = type_list
        yield d


# todo: implement security properties 6.8, KEY
# todo: implement Calendar Properties 6.9


class BaseContentLine(models.Model):
    """
    generic content line model for unresolved properties
    """
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE
    )
    param_type = models.CharField(max_length=100, blank=True)
    group = models.CharField(max_length=100, blank=True)  # for compatibility with group prefix
    name = models.CharField(max_length=50, blank=False)
    pref = models.BooleanField(default=False)
    other_params = models.CharField(max_length=50, blank=True)
    value = models.CharField()


class Profile(models.Model):
    """
    Users can have many profiles and each profile links to one of the user's Cards.
    """
    # todo: add attachments and CV/resume related fields
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    card = models.OneToOneField(
        Card,
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
    card = models.OneToOneField(
        Card,
        on_delete=models.SET_NULL,
        # in forms need to limit to card.user == profile.user
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
