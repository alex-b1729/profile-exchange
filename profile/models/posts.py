from django.db import models
from django.utils.translation import gettext_lazy as _

from . import profile as profile_models


class PostBase(profile_models.ItemBase):
    label = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='title',
    )
    description = models.TextField(
        blank=True,
        verbose_name='description',
    )
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name='date',
    )
    external_link = models.URLField(
        blank=True,
        verbose_name='external link',
    )

    class Meta(profile_models.ItemBase.Meta):
        abstract = True
        ordering = ['-date']

    def __str__(self):
        return f'{self.title}{" - " + str(self.date) if self.date else ""}'


class OrgBase(PostBase):
    organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='organization',
    )

    class Meta(PostBase.Meta):
        abstract = True

    def __str__(self):
        return f'{self.title}{" - " + str(self.organization) if self.organization else ""}'


class Award(OrgBase):
    pass


class Certificate(OrgBase):
    pass


class License(OrgBase):
    pass


class MembershipBase(OrgBase):
    organization = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='organization',
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='location'
    )
    # todo: dates should be more generic to allow just month and/or year
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name='start date',
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='end date'
    )
    current = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name='current'
    )

    class Meta(OrgBase.Meta):
        abstract = True
        ordering = ['-end_date', '-date']


class Membership(MembershipBase):
    pass


class WorkExperience(MembershipBase):
    class SettingType(models.TextChoices):
        IN_PERSON = 'i', _('In-Person')
        HYBRID = 'h', _('Hybrid')
        REMOTE = 'r', _('Remote')

    organization = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='company',
    )
    date = models.DateField(
        blank=False,
        verbose_name='start date',
    )
    work_setting = models.CharField(
        max_length=1,
        choices=SettingType,
        blank=True,
        verbose_name='work setting',
    )

    class Meta(MembershipBase.Meta):
        verbose_name = 'work experience'
        verbose_name_plural = 'work experiences'

    def __str__(self):
        return f'{self.title} at {self.organization}'


class VolunteerWork(MembershipBase):
    organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='organization',
    )


class Education(MembershipBase):
    label = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='major',
    )
    organization = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='school',
        help_text='School, university, etc.',
    )
    degree_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='degree type',
        help_text="Associate, bachelor's, master's, etc.",
    )
    gpa = models.FloatField(
        blank=True,
        null=True,
        verbose_name='GPA',
        help_text='Grade point average',
    )


class ProjectBase(PostBase):
    contributors = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='contributors',
        help_text='Contributors or co-authors',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='project source',
        help_text='Publication, journal, publisher, etc.',
    )

    class Meta(PostBase.Meta):
        abstract = True


class Project(ProjectBase):
    pass


class PublishedWork(ProjectBase):
    contributors = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='authors',
    )
    source = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='publication source',
    )

    class Meta(ProjectBase.Meta):
        verbose_name = 'published work'
        verbose_name_plural = 'published works'


class ResearchProject(ProjectBase):
    contributors = models.CharField(
        max_length=200,
        blank=False,
        verbose_name='authors',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='project source',
        help_text='Publication, journal, publisher, etc.',
    )
    affiliated_institutions = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='affiliated institutions',
    )
    funding_source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='funding source',
        help_text='Grant, institution, etc.',
    )

    class Meta(ProjectBase.Meta):
        verbose_name = 'research project'
        verbose_name_plural = 'research projects'


class Patent(ProjectBase):
    class StatusType(models.TextChoices):
        PENDING = 'p', _('Pending')
        GRANTED = 'g', _('Granted')
        EXPIRED = 'e', _('Expired')

    number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='patent number',
    )
    status = models.CharField(
        choices=StatusType,
        blank=True,
    )
    date = models.DateField(
        blank=True,
        null=True,
        verbose_name='issue date',
        help_text='Issue / Grant date',
    )
    filing_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='filing date',
    )
    contributors = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='inventors',
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='assignee',
    )
    classifications = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='classifications',
    )
    country = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='country',
        help_text='Country or region',
    )
