from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    company = models.CharField(max_length=250, blank=True)
    job_title = models.CharField(max_length=250, blank=True)
    location = models.CharField(max_length=30, blank=True)

    photo = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True
    )
    headline = models.CharField(max_length=50, blank=True)

    date_of_birth = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'Profile of {self.user.first_name} {self.user.last_name}'


class EmailAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='email_addresses',
        on_delete=models.CASCADE
    )
    email_address = models.EmailField()
    confirmed = models.BooleanField(default=False, null=False)
    is_primary = models.BooleanField(null=False)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email_address


class Phone(models.Model):
    # todo: handle extensions
    MOBILE = 'mobile'
    HOME = 'home'
    WORK = 'work'
    SCHOOL = 'school'
    MAIN = 'main'
    HOME_FAX = 'home_fax'
    WORK_FAX = 'work_fax'
    PAGER = 'pager'
    OTHER = 'other'
    TYPE_CHOICES = {
        MOBILE: 'Mobile',
        HOME: 'Home',
        WORK: 'Work',
        SCHOOL: 'School',
        MAIN: 'Main',
        HOME_FAX: 'Home Fax',
        WORK_FAX: 'Work Fax',
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
                                  default=MOBILE)

    def __str__(self):
        return str(self.phone_number)


class PostalAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='postal_addresses',
        on_delete=models.CASCADE
    )
    street1 = models.CharField()
    street2 = models.CharField(blank=True)
    city = models.CharField()
    state = models.CharField()
    zip = models.CharField(max_length=10)
    country = models.CharField(blank=True)

    class Meta:
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'
