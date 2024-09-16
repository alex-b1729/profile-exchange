from django.contrib import admin

from .models import (
    Card,
    Address,
    Phone,
    Email,
    Title,
    Org,
    Role,
    Tag,
    Url,
    Profile,
    Connection,
)


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'date_of_birth', 'photo']


# what's needed in prod?
admin.site.register(Card)
admin.site.register(Address)
admin.site.register(Phone)
admin.site.register(Email)
admin.site.register(Title)
admin.site.register(Org)
admin.site.register(Role)
admin.site.register(Tag)
admin.site.register(Url)
admin.site.register(Profile)
admin.site.register(Connection)
# admin.site.register(ContactNote)
