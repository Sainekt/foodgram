from django.contrib import admin

from .models import User, Subscriber


@admin.register(User)
class User(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_display_links = ('username', 'last_name', 'first_name')


@admin.register(Subscriber)
class Subscriber(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscriber')
    search_fields = ('user', 'subscriber')
    list_editable = ('user', 'subscriber')
