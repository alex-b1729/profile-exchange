from django.contrib import admin

from .models import (
    Profile,
    EmailAddress,
    Phone,
    PostalAddress,
    SocialProfile,
    Connection,
    ConnectionNote,
)


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'date_of_birth', 'photo']


# what's needed in prod?
admin.site.register(Profile)
admin.site.register(EmailAddress)
admin.site.register(Phone)
admin.site.register(PostalAddress)
admin.site.register(SocialProfile)
admin.site.register(Connection)
admin.site.register(ConnectionNote)
