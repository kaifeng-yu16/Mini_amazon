from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from amazon.models import Category, Product, Order, Item
from .forms import OrderInfoForm, ItemAmountForm 
from django.core.mail import send_mail

import socket

# send a signal to backend when received a order
def send_signal(o_id):
  HOST = "server" #"127.0.0.1"  # The server's hostname or IP address
  PORT = 2104
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(str(o_id).encode())
    s.close()

# Create your views here.
@login_required
def home(request):
  products=Product.objects.all()
  orders=Order.objects.all().filter(customer=request.user.customer, status='closed').order_by('-date_time')
  if orders.count() > 0:
    order = orders[0]
    return render(request, 'amazon/home.html', {'products': products, 'order': order})
  else:
    return render(request, 'amazon/home.html', {'products': products})

@login_required
def search_by_cat(request):
  cats = Category.objects.all() 
  return render(request, 'amazon/search_by_cat.html', {'cats': cats})

@login_required
def view_cat(request, c_id):
  try:
    cat = Category.objects.get(c_id=c_id)
  except Category.DoesNotExist:
    return HttpResponse('This category does not exist!')
  products=Product.objects.filter(category=cat)
  return render(request, 'amazon/view_cat.html', {'cat': cat, 'products': products})

@login_required
def goto_cart(request):
  try:
    order = Order.objects.get(customer=request.user.customer, status='open')
  except Order.DoesNotExist:
    order = Order.objects.create(customer=request.user.customer, loc_x=request.user.customer.loc_x,\
        loc_y=request.user.customer.loc_y, card_number=request.user.customer.card_number,\
        ups_account=request.user.customer.ups_account)
  return redirect('amazon:checkout', o_id=order.o_id)
   
@login_required
def view_order(request):
  orders=Order.objects.filter(customer=request.user.customer, status='closed').order_by('-date_time')
  return render(request, 'amazon/view_order.html', {'orders': orders, 'date': True})

@login_required
def view_order_price_hl(request):
  orders=Order.objects.filter(customer=request.user.customer, status='closed').order_by('-total')
  return render(request, 'amazon/view_order.html', {'orders': orders, 'hl': True})
  
@login_required
def view_order_price_lh(request):
  orders=Order.objects.filter(customer=request.user.customer, status='closed').order_by('total')
  return render(request, 'amazon/view_order.html', {'orders': orders, 'lh': True})

@login_required
def search_order(request):
  if request.method == "GET":
    return render(request, 'amazon/search_order.html')
  else:
    p_name = request.POST['p_name']
    products = Product.objects.filter(name__contains=p_name).values('p_id')
    orders = Order.objects.filter(customer=request.user.customer, status='closed')\
        .filter(items__product_id__in=products).order_by('-date_time')
    return render(request, 'amazon/search_order.html', {'orders': orders})

@login_required
def view_product(request, p_id):
  try:
    product=Product.objects.get(p_id=p_id)
  except Product.DoesNotExist:
    return HttpResponse('This product does not exist!')
  favorite = product.favorite
  if request.method == "POST":
    if 'liked' in request.POST:
      favorite = request.POST['liked']
      product.favorite = favorite
      product.save()
      return render(request, 'amazon/view_product.html', {'product': product, 'favorite': favorite})
    if 'add_to_cart' in request.POST:
      try:
        order = Order.objects.get(customer=request.user.customer, status='open')
      except Order.DoesNotExist:
        order = Order.objects.create(customer=request.user.customer, loc_x=request.user.customer.loc_x,\
            loc_y=request.user.customer.loc_y, card_number=request.user.customer.card_number,
            ups_account=request.user.customer.ups_account)
      try:
        item = Item.objects.get(order=order, product=product, status='new')
      except Item.DoesNotExist:
        item = Item.objects.create(order=order, product=product, count=0)
      if item.count + int(request.POST['count']) > 100:
        item.count = 100
      else:
        item.count += int(request.POST['count']) 
      item.save()
      return HttpResponseRedirect(reverse('amazon:home'))
    if 'buy_now' in request.POST:
      order = Order.objects.create(customer=request.user.customer, loc_x=request.user.customer.loc_x, \
          loc_y=request.user.customer.loc_y, card_number=request.user.customer.card_number,\
          ups_account=request.user.customer.ups_account, status='one_time')
      count = int(request.POST['count'])
      if count > 100:
        count = 100
      Item.objects.create(order=order, product=product, count=count)
      return redirect('amazon:checkout', o_id=order.o_id)
    return HttpResponseRedirect(reverse('amazon:home'))
  else:
    return render(request, 'amazon/view_product.html', {'product': product, 'favorite': str(favorite)})

@login_required
def checkout(request, o_id):
  try:
    order=Order.objects.get(o_id=o_id, customer=request.user.customer)
  except Order.DoesNotExist:
    return HttpResponse('This order does not exist!')
  items=order.items.all();
  total = 0
  for i in items:
    total += i.product.price * i.count
  if request.method == "POST":
    if items.count() == False:
      return render(request, 'amazon/failure_no_item.html')
    form = OrderInfoForm(request.POST, instance=order)
    if form.is_valid():
      form.save()
      order.total=total
      order.status='closed'
      order.save()
      send_signal(order.o_id)
      send_mail(
        'Order Received',
        'Your order has been received. Thank you 🧡',
        'amazingMiniAmz@outlook.com',
        [request.user.email],
        fail_silently=True
      )
      return render(request, 'amazon/success.html')
    else:
      return render(request, 'amazon/checkout.html', {'invalid': True, 'order': order, 'items': items, 'form': form, 'total': tatal})
  else:
    form = OrderInfoForm(instance=order)
    return render(request, 'amazon/checkout.html', {'order': order, 'items': items, 'form': form, 'total': total})

@login_required
def change_item(request, i_id):
  try:
    orders = Order.objects.filter(customer=request.user.customer).exclude(status='closed')
    item=Item.objects.get(i_id=i_id, order__in=orders)
  except (Order.DoesNotExist, Item.DoesNotExist):
    return HttpResponse('This order does not exist!')
  if request.method == "POST":
    form = ItemAmountForm(request.POST, instance=item)
    if 'del' in request.POST:
      item.delete()
      return redirect('amazon:checkout', o_id=item.order.o_id)
    else:
      if form.is_valid():
        form.save()
        return redirect('amazon:checkout', o_id=item.order.o_id)
      else:
        return render(request, 'amazon/change_item.html', {'form': form, 'item': item, 'error_msg': 'Invalid quantity of this product, please enter again.'})
  else:
    form = ItemAmountForm(instance=item)
    return render(request, 'amazon/change_item.html', {'form': form, 'item': item})
  

@login_required
def view_order_detail(request, o_id):
  try:
    order=Order.objects.get(o_id=o_id, customer=request.user.customer)
  except Order.DoesNotExist:
    return HttpResponse('This order does not exist!')
  items=order.items.all();
  total = 0
  for i in items:
    total += i.product.price * i.count
  return render(request, 'amazon/view_order_detail.html', {'order': order, 'items': items, 'total': total})
 
@login_required
def search_product(request):
  if request.method == "GET":
    return render(request, 'amazon/search_product.html')
  else:
    p_name = request.POST['p_name']
    products_p = Product.objects.filter(name__contains=p_name)
    categories = Category.objects.filter(name__contains=p_name).values('c_id')
    products_c = Product.objects.filter(category_id__in=categories)
    products = products_p.union(products_c)
    return render(request, 'amazon/search_product.html', {'products': products})

@login_required
def buy_again(request, o_id):
  try:
    old_order=Order.objects.get(o_id=o_id, customer=request.user.customer)
  except Order.DoesNotExist:
    return HttpResponse('This order does not exist!')
  items=old_order.items.all();
  order = Order.objects.create(customer=request.user.customer, loc_x=request.user.customer.loc_x,\
      loc_y=request.user.customer.loc_y, card_number=request.user.customer.card_number,
      ups_account=request.user.customer.ups_account, status='one_time')
  for i in items:
    Item.objects.create(order=order, product=i.product, count=i.count)
  return redirect('amazon:checkout', o_id=order.o_id)

@login_required
def view_favorite(request):
  products = Product.objects.filter(favorite=True)
  return render(request, 'amazon/view_favorite.html', {'products': products})
