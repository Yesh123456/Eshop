from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse
# Create your views here.
from cart.models import CartItem
from store.models import Product
from .forms import OrderForm
import datetime
from .models import Order,Payment,OrderProduct
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
import json
import razorpay
from django.conf import settings

razorpay_client = razorpay.Client(auth=(settings.RAZOR_KEY_ID,settings.RAZOR_KEY_SECRET))

def payments(request):
	body = json.loads(request.body)
	# print(body)
	#print(body['transactionId'])
	order = Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderId'])
	print(order)
	payment = Payment(
		user = request.user,
		payment_id = body['transactionId'],
		payment_method = body['payment_method'],
		amount_paid = order.order_total,
		status = body['status'],
		)
	# print(payment.user)
	# print(payment.payment_id)
	# print(payment.payment_method)
	# print(payment.amount_paid)
	print(payment.status)
	payment.save()
	order.payment=payment
	#print(order)
	order.is_ordered=True
	order.save()
	#move cart items to orderproduct,reduce the quantity of sold products,clear cart,send email as order recieved,send order number and transaction id back to method to redirct to thanku page.
	cart_items = CartItem.objects.filter(user=request.user)
	print("111")
	for i in cart_items:
		order_product=OrderProduct()
		order_product.order_id=order.id
		order_product.payment=payment
		order_product.user_id=request.user.id
		order_product.product_id=i.product.id
		order_product.quantity=i.quantity
		order_product.product_price=i.product.product_price
		order_product.ordered=True
		order_product.save()
		cart_item = CartItem.objects.get(id=i.id)
		product_variation=cart_item.variations.all()
		order_product = OrderProduct.objects.get(id=order_product.id)
		order_product.variations.set(product_variation)
		order_product.save()
	# print("222")
		product = Product.objects.get(id=i.product_id)
		product.stock-=i.quantity
		product.save()
	CartItem.objects.filter(user=request.user).delete()

	mail_subject='Your Order is confirmed!'
	message=render_to_string('orders/order_recieved_mail.html',{
		'user':request.user,
		'order':order,
		'product':product,
	})
	to_email=request.user.email
	send_email=EmailMessage(mail_subject,message,to=[to_email])
	send_email.send()

	data={
	'order_number':order.order_number,
	'transactionId':payment.payment_id,
	}
	return JsonResponse(data)

def place_order(request,total=0,quantity=0):
	current_user=request.user

	cart_items=CartItem.objects.filter(user=current_user)
	cart_count=cart_items.count()#if cart count is less or equal to 0 redirect to store
	if cart_count<=0:
		return redirect('store')
		
	grand_total=0
	tax=0
	for cart_item in cart_items:
		total+=(cart_item.product.product_price*cart_item.quantity)
		quantity+=cart_item.quantity
	tax = (18*total)/100
	grand_total = total+tax
	if request.method == 'POST':
		#print("222")
		form = OrderForm(request.POST)
		#print("333")
		#print(form)
		if form.is_valid():#store all billing info inside order table
			#print("444")
			data = Order()
			data.user = current_user
			data.first_name=form.cleaned_data['first_name']
			data.last_name=form.cleaned_data['last_name']
			data.phone_number=form.cleaned_data['phone_number']
			data.email=form.cleaned_data['email']
			data.address_line1=form.cleaned_data['address_line1']
			data.address_line2=form.cleaned_data['address_line2']
			data.city=form.cleaned_data['city']
			data.state=form.cleaned_data['state']
			data.order_note=form.cleaned_data['order_note']
			data.order_total=grand_total
			data.tax=tax
			data.ip=request.META.get('REMOTE_ADDR')
			data.save()
			#genrating order number
			yr=int(datetime.date.today().strftime('%Y'))
			dat=int(datetime.date.today().strftime('%d'))
			mon=int(datetime.date.today().strftime('%m'))
			dd=datetime.date(yr,mon,dat)
			current_date=dd.strftime("%Y%m%d")
			order_number=current_date+str(data.id)
			data.order_number = order_number
			data.save()
			order = Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
			grand_total = round(grand_total)
			# print(round(amount))
			currency="INR"
			inr_amount = grand_total*100
			razorpay_order = razorpay_client.order.create(dict(amount=inr_amount,currency=currency,payment_capture=1))
			razorpay_order_id = razorpay_order['id']
			context = {
				'razorpay_order_id': razorpay_order_id,
				'razorpay_merchant_key': settings.RAZOR_KEY_ID,
				'inr_amount':inr_amount,
				'currency':currency,				
				'order':order,
				'cart_items':cart_items,
				'total':total,
				'tax':tax,
				'grand_total':grand_total
			}
			return render(request,'orders/payments.html',context)
		else:
			#print("555")
			return HttpResponse('fail')

def order_complete(request):
	order_number = request.GET.get('order_number')
	transactionId= request.GET.get('payment_id')
	try:
		order = Order.objects.get(order_number=order_number,is_ordered=True)
		order_products = OrderProduct.objects.filter(order_id=order.id)
		
		subtotal =0
		for i in order_products:
			subtotal+=i.product_price*i.quantity
		order_total = round(order.order_total)
		payment = Payment.objects.get(payment_id=transactionId)
		context={
		'order':order,
		'order_products':order_products,
		'order_number':order.order_number,
		'transactionId':payment.payment_id,
		'payment':payment,
		'subtotal':subtotal,
		'order_total':order_total,
		}
		return render(request,'orders/order_complete_template.html',context)
	except(Payment.DoesNotExist,Order.DoesNotExist):
		return redirect('home')