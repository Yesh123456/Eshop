from django.shortcuts import render,redirect,get_object_or_404
from store.models import Product,Variation
from .models import Cart,CartItem
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def _cart_id(request):
	cart = request.session.session_key
	if not cart:
		cart = request.session.create()
	return cart

def add_cart(request,product_id):
	current_user = request.user
	product = Product.objects.get(id=product_id)# to get product
	if current_user.is_authenticated:
		product_variation = []
		if request.method == 'POST':
			for i in request.POST:
				key = i
				value = request.POST[key]

				try:
					variation = Variation.objects.get(product = product,variation_category__iexact=key,variation_value__iexact=value)
					product_variation.append(variation)
				except:
					pass

		is_cart_item_exsist = CartItem.objects.filter(product=product,user=current_user)
		if is_cart_item_exsist:
			cart_item = CartItem.objects.filter(product=product,user=current_user)
			exsisting_variation=[]
			id=[]
			for item in cart_item:
				ex_variation = item.variations.all()
				exsisting_variation.append(list(ex_variation))
				id.append(item.id)
			print(exsisting_variation)

			if product_variation in exsisting_variation:
				# return HttpResponse('True')
				temp = exsisting_variation.index(product_variation)
				item_id=id[temp]
				item = CartItem.objects.get(product=product,id=item_id)
				item.quantity+=1
				item.save()
			else:
				# return HttpResponse('false')
				item = CartItem.objects.create(product=product,quantity=1,user=current_user)
				if len(product_variation)>0:
					item.variations.clear()
					item.variations.add(*product_variation)
			# cart_item.quantity+=1
				item.save()
		else:
			cart_item = CartItem.objects.create(product=product,quantity=1,user=current_user)
			if len(product_variation)>0:
				cart_item.variations.clear()
				cart_item.variations.add(*product_variation)
			cart_item.save()
		# return HttpResponse(cart_item.product)
		# exit()
		return redirect('cart')
	else:
		product_variation = []
		if request.method == 'POST':
			for i in request.POST:
				key = i
				value = request.POST[key]

				try:
					variation = Variation.objects.get(product = product,variation_category__iexact=key,variation_value__iexact=value)
					product_variation.append(variation)
				except:
					pass
		try:
			cart = Cart.objects.get(cart_id=_cart_id(request))#to get cart_id present in session
		except Cart.DoesNotExist:
			cart = Cart.objects.create(cart_id=_cart_id(request))
		cart.save()

		is_cart_item_exsist = CartItem.objects.filter(product=product,cart=cart)
		if is_cart_item_exsist:
			cart_item = CartItem.objects.filter(product=product,cart=cart)
			exsisting_variation=[]
			id=[]
			for item in cart_item:
				ex_variation = item.variations.all()
				exsisting_variation.append(list(ex_variation))
				id.append(item.id)
			print(exsisting_variation)

			if product_variation in exsisting_variation:
				# return HttpResponse('True')
				temp = exsisting_variation.index(product_variation)
				item_id=id[temp]
				item = CartItem.objects.get(product=product,id=item_id)
				item.quantity+=1
				item.save()
			else:
				# return HttpResponse('false')
				item = CartItem.objects.create(product=product,quantity=1,cart=cart)
				if len(product_variation)>0:
					item.variations.clear()
					item.variations.add(*product_variation)
			# cart_item.quantity+=1
				item.save()
		else:
			cart_item = CartItem.objects.create(product=product,quantity=1,cart=cart)
			if len(product_variation)>0:
				cart_item.variations.clear()
				cart_item.variations.add(*product_variation)
			cart_item.save()
		# return HttpResponse(cart_item.product)
		# exit()
		return redirect('cart')


def remove_cart(request,product_id,cart_item_id):
	product = get_object_or_404(Product,id=product_id)
	try:
		if request.user.is_authenticated:
			cart_item = CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
		else:
			cart = Cart.objects.get(cart_id=_cart_id(request))
			cart_item = CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
		if cart_item.quantity>1:
			cart_item.quantity-=1
			cart_item.save()
		else:
			cart.item.delete()
	except:
		pass
	return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
	product=get_object_or_404(Product,id=product_id)
	try:
		if request.user.is_authenticated:
			cart_item = CartItem.objects.get(product=product,user=request.user,id=cart_item_id)
		else:
			cart=Cart.objects.get(cart_id=_cart_id(request))
			cart_item = CartItem.objects.get(product=product,cart=cart,id=cart_item_id)
		cart_item.delete()
	except:
		pass
	return redirect('cart')


def cart(request,total=0,quantity=0,cart_items=None):
	try:
		tax=0
		grand_total=0
		if request.user.is_authenticated:
			cart_items  = CartItem.objects.filter(user=request.user,is_active=True)
		else:
			cart = Cart.objects.get(cart_id=_cart_id(request))
			cart_items = CartItem.objects.filter(cart=cart,is_active=True)
		for cart_item in cart_items:
			total = (cart_item.product.product_price*cart_item.quantity)
			quantity += cart_item.quantity
		tax = (18*total)/100
		grand_total = total+tax
	except ObjectDoesNotExist:
		pass
	context = {'total':total,'quantity':quantity,'cart_items':cart_items,'tax':tax,'grand_total':grand_total}
	return render(request,'store/cart.html',context)

@login_required(login_url='login')
def checkout(request,total=0,quantity=0,cart_items=None):
	try:
		tax=0
		grand_total=0
		if request.user.is_authenticated:
			cart_items  = CartItem.objects.filter(user=request.user,is_active=True)
		else:
			cart = Cart.objects.get(cart_id=_cart_id(request))
			cart_items = CartItem.objects.filter(cart=cart,is_active=True)
		for cart_item in cart_items:
			total = (cart_item.product.product_price*cart_item.quantity)
			quantity += cart_item.quantity
		tax = (18*total)/100
		grand_total = total+tax
	except ObjectDoesNotExist:
		pass
	context = {'total':total,'quantity':quantity,'cart_items':cart_items,'tax':tax,'grand_total':grand_total}
	return render(request,'store/checkout.html',context)