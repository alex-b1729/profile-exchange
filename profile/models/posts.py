from django.db import models
from django.utils.translation import gettext_lazy as _

from . import profile as profile_models


class PostBase(profile_models.ItemBase):
    title = models.CharField(
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_link.help_text = 'Link to organization'


class Award(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Awarding organization or body'


class Certificate(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Certifying organization or body'


class License(OrgBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Licensing organization or body'


class MembershipBase(OrgBase):
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='location'
    )
    # todo: dates should be more generic to allow just month and/or year
    end_date = models.DateField(
        blank=True,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title.help_text = 'Title or position'
        self.date.verbose_name = 'start date'


class Membership(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class WorkExperience(MembershipBase):
    class SettingType(models.TextChoices):
        IN_PERSON = 'i', _('In-Person')
        HYBRID = 'h', _('Hybrid')
        REMOTE = 'r', _('Remote')

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.blank = False  # have to work for some org/comp
        self.organization.verbose_name = 'Company or organization'
        self.external_link.help_text = 'Link to company'


class VolunteerWork(MembershipBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.help_text = 'Group, organization, club, etc.'


class Education(MembershipBase):
    degree_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='degree type',
        help_text="Associate, bachelor's, master's, etc."
    )
    gpa = models.FloatField(
        blank=True,
        null=True,
        verbose_name='GPA',
        help_text='Grade point average',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization.blank = False  # must be educated somewhere
        self.title.verbose_name = 'major'
        self.date.verbose_name = 'start date'
        self.location.help_text = 'School, university, etc.'
        self.end_date.help_text = 'Graduation or expected graduation date'


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_link.help_text = 'Link to project source'


class Project(ProjectBase):
    pass


class PublishedWork(ProjectBase):
    class Meta(ProjectBase.Meta):
        verbose_name = 'published work'
        verbose_name_plural = 'published works'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source.blank = False  # must be published somewhere
        self.source.verbose_name = 'publication source'
        self.contributors.verbose_name = 'authors'
        self.external_link.help_text = 'Link to publication'


class ResearchProject(ProjectBase):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.contributors.blank = False  # someone must have contributed
        self.contributors.verbose_name = 'authors'
        self.date.help_text = 'Publication date or date of latest version'
        self.description.help_text = 'Abstract or project summary'
        self.external_link.help_text = 'Link to publication'
        self.source.verbose_name = 'publication source'
        self.source.help_text = 'Journal or conference name'


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
    filing_date = models.DateField(
        blank=True,
        verbose_name='filing date',
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date.verbose_name = 'issue date'
        self.date.help_text = 'Issue / Grant date'
        self.external_link.help_text = 'Link to patent'
        self.contributors.verbose_name = 'inventors'
        self.source.verbose_name = 'assignee'
