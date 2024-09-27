from django.contrib import admin

from profile import models


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'date_of_birth', 'photo']


# what's needed in prod?
admin.site.register(models.Address)
admin.site.register(models.Phone)
admin.site.register(models.Email)
admin.site.register(models.Profile)
admin.site.register(models.LinkBase)
admin.site.register(models.Link)
