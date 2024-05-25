from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    company = models.CharField(max_length=250, blank=True)
    job_title = models.CharField(max_length=250, blank=True)

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
