from django.contrib import admin

from .models import Profile, EmailAddress, Phone, PostalAddress


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'photo']


admin.site.register(EmailAddress)
admin.site.register(Phone)
admin.site.register(PostalAddress)
