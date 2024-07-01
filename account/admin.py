from django.contrib import admin

from .models import (
    Vcard,
    Address,
    Phone,
    Email,
    Organization,
    Tag,
    Url,
    Profile,
    Connection,
    ContactNote
)


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'date_of_birth', 'photo']


# what's needed in prod?
admin.site.register(Vcard)
admin.site.register(Address)
admin.site.register(Phone)
admin.site.register(Email)
admin.site.register(Organization)
admin.site.register(Tag)
admin.site.register(Url)
admin.site.register(Profile)
admin.site.register(Connection)
admin.site.register(ContactNote)
