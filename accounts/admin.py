from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account,UserProfile
from django.utils.html import format_html

# Register your models here.

class AccountAdmin(UserAdmin):
	list_display=('email','first_name','last_name','username','date_joined','last_login','is_active')
	list_display_links=('email','first_name','last_name')#display full view on this links too
	readonly_fields = ('last_login','date_joined')# can view only
	ordering = ('-date_joined',)#ascending order
	#column row view
	filter_horizontal =()
	list_filter = ()
	fieldsets = ()#password readonly

class UserProfileAdmin(admin.ModelAdmin):
	def thumbnail(self,object):
		return format_html('<img src="{}" width=30 style="border-radius:50%;">'.format(object.profile_picture.url))

	thumbnail.short_description = 'Profile Picture'
	list_display = ('user','city','state','thumbnail')

admin.site.register(Account,AccountAdmin)
admin.site.register(UserProfile,UserProfileAdmin)
