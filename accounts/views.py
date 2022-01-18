from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile
import random
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required
# Create your views here.
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail.message import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.http.response import HttpResponse
from cart.views import _cart_id
from cart.models import CartItem,Cart
from orders.models import Order
import requests


def register(request):
	if request.method == "POST":
		form = RegistrationForm(request.POST)
		# print(form.errors)
		if form.is_valid():
			# print(form)
			first_name = form.cleaned_data['first_name']
			last_name = form.cleaned_data['last_name']
			phone_number = form.cleaned_data['phone_number']
			email = form.cleaned_data['email']
			password = form.cleaned_data['password']
			#username = email.split("@")[0]
			username = first_name + str(random.randint(100,1000000))
			user = Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,password=password)
			user.save()
			
			#user activation
			current_site=get_current_site(request)
			mail_subject='Please Activate your account'
			message=render_to_string('accounts/account_verification.html',{
				'user':user,
				'domain':current_site,
				'uid':urlsafe_base64_encode(force_bytes(user.pk)),
				'token':default_token_generator.make_token(user),
			})
			to_email=email
			send_email=EmailMessage(mail_subject,message,to=[to_email])
			send_email.send()
			#messages.success(request,'Email sent for verification ')
			return redirect('/accounts/login/?command=verification&email='+email)
	else:
		form = RegistrationForm()
	context = {'form':form,}
	return render(request,'accounts/register.html',context)


def login(request):
	if request.method == 'POST':
		email=request.POST['email']
		password=request.POST['password']

		user = auth.authenticate(email=email,password=password)
		if user is not None:
			try:
				cart = Cart.objects.get(cart_id=_cart_id(request))
				is_cart_item_exsist = CartItem.objects.filter(cart=cart).exists()
				if is_cart_item_exsist:
					cart_item = CartItem.objects.filter(cart=cart)
					product_variation=[]

					for item in cart_item:
						variation = item.variations.all()
						product_variation.append(list(variation))

					cart_item = CartItem.objects.filter(user=user)
					exsisting_variation=[]
					id=[]
					for item in cart_item:
						ex_variation = item.variations.all()
						exsisting_variation.append(list(ex_variation))
						id.append(item.id)

					for i in product_variation:
						if i in exsisting_variation:
							index=exsisting_variation.index(i)
							item_id=id[index]
							item = CartItem.objects.get(id=item_id)
							item.quantity+=1
							item.user=user
							item.save()
						else:
							cart_item = CartItem.objects.filter(cart=cart)
							for item in cart_item:
								item.user=user
								item.save()
			except:
				pass
			auth.login(request,user)
			url=request.META.get('HTTP_REFERER')
			try:
				query = requests.utils.urlparse(url).query
				print(query)
				params = dict(x.split('=') for x in query.split('&'))
				if 'next' in params:
					nextPage = params['next']
					return redirect(nextPage)
			except:
				return redirect('dashboard')
		else:
			messages.error(request,'Invalid credentials')
			return redirect('login')
	return render(request,'accounts/login.html')

@login_required(login_url='login')
def logout(request):
	auth.logout(request)
	messages.success(request,'You are logged out!')
	return redirect('login')


def activate(request,uidb64,token):
	try:
		uid=urlsafe_base64_decode(uidb64).decode()
		user=Account._default_manager.get(pk=uid)
	except(TypeError,Account.DoesNotExist,ValueError,OverflowError):
		user=None
	if user is not None and default_token_generator.check_token(user,token):
		user.is_active=True
		user.save()
		messages.success(request,'Awesome! your account is activated~')
		return redirect('login')
	else:
		messages.error(request,'Invalid acctivation link')
		return redirect('register')

@login_required(login_url='login')
def dashboard(request):
	orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
	order_counts = orders.count()
	context={
	'order_counts':order_counts,
	}
	return render(request,'accounts/dashboard.html',context)

def forgetpassword(request):
	if request.method =='POST':
		email = request.POST['email']
		if Account.objects.filter(email=email).exists():
			user=Account.objects.get(email__exact=email)

			#reset password email
			current_site=get_current_site(request)
			mail_subject='Reset Your Password'
			message=render_to_string('accounts/account_reset_password.html',{
				'user':user,
				'domain':current_site,
				'uid':urlsafe_base64_encode(force_bytes(user.pk)),
				'token':default_token_generator.make_token(user),
			})
			to_email=email
			send_email=EmailMessage(mail_subject,message,to=[to_email])
			send_email.send()
			messages.success(request,'Password Reset Mail Sent')
			return redirect('login')
		else:
			messages.error(request,'Account not found!!')
			return redirect('forgetpassword')
	return render(request,'accounts/forgetpassword.html')

def resetpassword_validate(request,uidb64,token):
	try:
		uid=urlsafe_base64_decode(uidb64).decode()
		user=Account._default_manager.get(pk=uid)
	except(TypeError,Account.DoesNotExist,ValueError,OverflowError):
		user=None
	if user is not None and default_token_generator.check_token(user,token):
		request.session['uid']=uid
		messages.success(request,'Please reset your Password')
		return redirect('resetPassword')
	else:
		messages.error(request,'This link has expired!')
		return redirect('login')

def resetPassword(request):
	if request.method == 'POST':
		password = request.POST['password']
		confirm_password = request.POST['confirm_password']

		if password == confirm_password:
			uid = request.session.get('uid')
			user = Account.objects.get(pk=uid)
			user.set_password(password)
			user.save()
			messages.success(request,'Password Reset Successfull')
			return redirect('login')
		else:
			messages.error(request,'Password Dont match!!')
			return redirect('resetPassword')
	else:
		return render(request,'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
	orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
	context = {
		'orders':orders,
	}
	return render(request,'accounts/my_orders.html',context)
		
@login_required(login_url='login')
def edit_profile(request):
	userprofile = get_object_or_404(UserProfile,user=request.user)
	if request.method == 'POST':
		user_form = UserForm(request.POST,instance=request.user)
		profile_form = UserProfileForm(request.POST,request.FILES,instance=userprofile)
		if user_form.is_valid() and profile_form.is_valid():
			user_form.save()
			profile_form.save()
			messages.success(request,'Your Profile has been Updated')
			return redirect('edit_profile')
	else:
		user_form = UserForm(instance=request.user)
		profile_form = UserProfileForm(instance=userprofile)
	context = {
		'user_form':user_form,
		'profile_form':profile_form,
		'userprofile':userprofile,
	}
	return render(request,'accounts/edit_profile.html',context)

@login_required(login_url='login')
def change_password(request):
	if request.method == 'POST':
		current_pass = request.POST['current_pass']
		new_pass = request.POST['new_pass']
		confirm_new_pass = request.POST['confirm_new_pass'] 

		user = Account.objects.get(username__exact=request.user.username)

		if new_pass == confirm_new_pass:
			success = user.check_password(current_pass)
			if success:
				user.set_password(new_pass)
				user.save()
				messages.success(request,'Password Change Successfull')
				return redirect('change_password')
			else:
				messages.error(request,'Please Enter Current Correct Password')
				return redirect('change_password')
		else:
			messages.error(request,'Confirm Password Does Not Match')
			return redirect('change_password')
	return render(request,'accounts/change_password.html')