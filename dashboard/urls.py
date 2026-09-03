from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard),
    path("stock-price/", views.stock_price),
    path("buy/", views.buy),
    path("sell/", views.sell),
]