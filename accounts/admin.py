from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

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



admin.site.register(Account,AccountAdmin)