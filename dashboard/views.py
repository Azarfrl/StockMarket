import os
import re
import time
import requests

from django.http import JsonResponse
from django.shortcuts import render

API_KEY = os.environ.get("ALPHA_VANTAGE_KEY")
API_URL = "https://www.alphavantage.co/query"

cash = 1000.00
holdings = {}
stock_cache = {}

CACHE_SECONDS = 6 * 60 * 60


def get_stock_data(symbol):
    if not re.fullmatch(r"[A-Z0-9.-]{1,10}", symbol):
        raise ValueError("Enter a valid stock ticker.")

    if symbol in stock_cache:
        cached_data, cached_time = stock_cache[symbol]

        if time.monotonic() - cached_time < CACHE_SECONDS:
            return cached_data

    if not API_KEY:
        raise ValueError("Alpha Vantage API key is missing.")

    response = requests.get(
        API_URL,
        params={
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": API_KEY
        },
        timeout=15
    )

    response.raise_for_status()
    data = response.json()

    time_series = data.get("Time Series (Daily)")

    if not time_series:
        message = (
            data.get("Error Message")
            or data.get("Note")
            or data.get("Information")
            or "No stock data found."
        )
        raise ValueError(message)

    dates = sorted(time_series.keys())[-30:]

    prices = []
    candles = []

    for date in dates:
        daily_data = time_series[date]

        open_price = float(daily_data["1. open"])
        high_price = float(daily_data["2. high"])
        low_price = float(daily_data["3. low"])
        close_price = float(daily_data["4. close"])

        prices.append(close_price)

        candles.append({
            "date": date,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price
        })

    stock_data = {
        "labels": dates,
        "prices": prices,
        "candles": candles
    }

    stock_cache[symbol] = (stock_data, time.monotonic())

    return stock_data


def get_portfolio_value():
    total = cash

    for symbol, amount in holdings.items():
        if amount > 0:
            data = get_stock_data(symbol)
            latest_price = data["prices"][-1]
            total += amount * latest_price

    return total


def dashboard(request):
    return render(request, "dashboard.html")


def stock_price(request):
    symbol = request.GET.get("symbol", "AAPL").strip().upper()

    try:
        data = get_stock_data(symbol)
        price = data["prices"][-1]

        return JsonResponse({
            **data,
            "symbol": symbol,
            "price": price,
            "cash": round(cash, 2),
            "shares": holdings.get(symbol, 0),
            "value": round(get_portfolio_value(), 2)
        })

    except requests.RequestException as error:
        return JsonResponse({"error": str(error)}, status=503)

    except (ValueError, KeyError) as error:
        return JsonResponse({"error": str(error)}, status=400)


def buy(request):
    global cash

    symbol = request.GET.get("symbol", "AAPL").strip().upper()

    try:
        data = get_stock_data(symbol)
        price = data["prices"][-1]
        amount = int(request.GET.get("amount", 0))

        if amount <= 0:
            raise ValueError("Enter a positive number of shares.")

        cost = amount * price

        if cost > cash:
            raise ValueError("You do not have enough cash.")

        cash -= cost
        holdings[symbol] = holdings.get(symbol, 0) + amount

        return JsonResponse({
            "cash": round(cash, 2),
            "shares": holdings[symbol],
            "value": round(get_portfolio_value(), 2)
        })

    except requests.RequestException as error:
        return JsonResponse({"error": str(error)}, status=503)

    except (ValueError, KeyError) as error:
        return JsonResponse({"error": str(error)}, status=400)


def sell(request):
    global cash

    symbol = request.GET.get("symbol", "AAPL").strip().upper()

    try:
        data = get_stock_data(symbol)
        price = data["prices"][-1]
        amount = int(request.GET.get("amount", 0))
        owned = holdings.get(symbol, 0)

        if amount <= 0 or amount > owned:
            raise ValueError("Enter a valid number of shares to sell.")

        cash += amount * price
        holdings[symbol] -= amount

        return JsonResponse({
            "cash": round(cash, 2),
            "shares": holdings[symbol],
            "value": round(get_portfolio_value(), 2)
        })

    except requests.RequestException as error:
        return JsonResponse({"error": str(error)}, status=503)

    except (ValueError, KeyError) as error:
        return JsonResponse({"error": str(error)}, status=400)