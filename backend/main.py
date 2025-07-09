from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

load_dotenv()  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_SYMBOLS = ["AAPL", "TSLA", "MSFT", "GOOG", "AMZN"]

class Asset(BaseModel):
    symbol: str
    quantity: float

class PortfolioRequest(BaseModel):
    assets: List[Asset]

def get_live_price_usd(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        return round(ticker.history(period="1d")['Close'][-1], 2)
    except Exception:
        return None

def get_usd_to_inr():
    try:
        fx = yf.Ticker("USDINR=X")
        return round(fx.history(period="1d")['Close'][-1], 2)
    except Exception:
        return 83.0  # fallback approx. exchange rate

def generate_ai_insight(breakdown):
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return "AI insight unavailable. GROQ API key not set."

        prompt = "Given the following portfolio with asset values, percentages, and risk ratings, provide a concise 2-3 line summary. Avoid repetition and be clear:\n\n"
        for item in breakdown:
            prompt += (
                f"{item['symbol']}: ₹{item['value']} ({item['percentage']:.2f}%), Risk: {item['risk']}\n"
            )
        prompt += "\nRespond with a short summary of the portfolio’s risk and allocation."

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",  # or gemma-7b-it
                "messages": [
                    {"role": "system", "content": "You are a financial analyst."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5
            }
        )

        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception:
        return "AI insight could not be generated."

@app.post("/analyze")
def analyze_portfolio(data: PortfolioRequest):
    breakdown = []
    total_value = 0
    usd_to_inr = get_usd_to_inr()

    for asset in data.assets:
        symbol = asset.symbol.upper()
        quantity = asset.quantity
        if symbol not in SUPPORTED_SYMBOLS:
            raise HTTPException(status_code=400, detail=f"Unsupported symbol: {symbol}")
        if quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid quantity for {symbol}")

        price_usd = get_live_price_usd(symbol)
        if price_usd is None:
            raise HTTPException(status_code=400, detail=f"Failed to fetch price for {symbol}")

        price_inr = round(price_usd * usd_to_inr, 2)
        value = price_inr * quantity
        total_value += value

        breakdown.append({
            "symbol": symbol,
            "quantity": quantity,
            "price": price_inr,
            "value": round(value, 2),
        })

    for item in breakdown:
        pct = (item["value"] / total_value) * 100 if total_value > 0 else 0
        item["percentage"] = round(pct, 2)
        item["risk"] = "High" if pct > 50 else "Normal" if pct > 25 else "Low"

    ai_insight = generate_ai_insight(breakdown)

    return {
        "total_value": round(total_value, 2),
        "currency": "INR",
        "breakdown": breakdown,
        "ai_insight": ai_insight
    }
