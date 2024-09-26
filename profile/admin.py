from django.contrib import admin

from .models import (
    Address,
    Phone,
    Email,
    Profile,
)


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'date_of_birth', 'photo']


# what's needed in prod?
admin.site.register(Address)
admin.site.register(Phone)
admin.site.register(Email)
admin.site.register(Profile)
