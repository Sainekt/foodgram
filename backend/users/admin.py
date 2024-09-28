from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscriber, User

admin.site.register(User, UserAdmin)


@admin.register(Subscriber)
class Subscriber(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscriber')
    search_fields = ('user', 'subscriber')
    list_editable = ('user', 'subscriber')
