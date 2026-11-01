from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("stock-price/", views.stock_price, name="stock_price"),
    path("buy/", views.buy, name="buy"),
    path("sell/", views.sell, name="sell"),
]