import random
from django.http import JsonResponse
from django.shortcuts import render

price = 100.00
cash = 1000.00
shares = 0

def dashboard(request):
    return render(request, "dashboard.html")

def stock_price(request):
    global price

    price += random.uniform(-2, 2)
    price = max(price, 1)

    return JsonResponse({
        "price": round(price, 2),
        "cash": round(cash, 2),
        "shares": shares,
        "value": round(cash + shares * price, 2)
    })


def buy(request):
    global cash, shares

    amount = int(request.GET.get("amount", 0))
    cost = amount * price

    if amount > 0 and cost <= cash:
        cash -= cost
        shares += amount

    return JsonResponse({
        "cash": round(cash, 2),
        "shares": shares
    })


def sell(request):
    global cash, shares

    amount = int(request.GET.get("amount", 0))

    if amount > 0 and amount <= shares:
        cash += amount * price
        shares -= amount

    return JsonResponse({
        "cash": round(cash, 2),
        "shares": shares
    })