from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

def get_vpt(df):
    vpt = [0]
    for i in range(1, len(df)):
        prev_vpt = vpt[-1]
        pct_change = (df['Close'].iloc[i] - df['Close'].iloc[i - 1]) / df['Close'].iloc[i - 1]
        vpt.append(prev_vpt + pct_change * df['Volume'].iloc[i])
    df['VPT'] = vpt
    return df

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    tickers = data.get("tickers", "").split(",")
    buy_dates_raw = data.get("buy_dates", "")
    buy_dates_dict = {}

    # buy_dates 문자열 파싱
    for line in buy_dates_raw.strip().split("\n"):
        if ":" in line:
            ticker, date = line.strip().split(":")
            buy_dates_dict[ticker.strip()] = date.strip()

    results = []

    for ticker in tickers:
        ticker = ticker.strip()
        if not ticker:
            continue

        try:
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            df.dropna(inplace=True)

            if df.empty or len(df) < 20:
                continue

            df = get_vpt(df)
            df["MA20"] = df["Close"].rolling(window=20).mean()
            last_3_closes = df["Close"].tail(3).tolist()
            latest = df.iloc[-1]

            current_price = latest["Close"]
            below_ma20 = current_price < latest["MA20"]
            three_day_fall = all(x > y for x, y in zip(last_3_closes, last_3_closes[1:]))
            vpt_buy_signal = latest["VPT"] > df["VPT"].rolling(window=20).mean().iloc[-1]

            # 30일 경과 체크
            today = datetime.today().date()
            buy_date_str = buy_dates_dict.get(ticker, "")
            is_30days = False
            if buy_date_str:
                try:
                    buy_date = datetime.strptime(buy_date_str, "%Y-%m-%d").date()
                    is_30days = (today - buy_date).days >= 30
                except:
                    pass

            buy_signal = below_ma20 and three_day_fall and is_30days and vpt_buy_signal

            results.append({
                "종목": ticker,
                "현재가": round(current_price, 2),
                "20일선 이하": below_ma20,
                "3일 연속 하락": three_day_fall,
                "30일 경과": is_30days,
                "VPT 값": round(latest["VPT"], 2),
                "VPT 매수": vpt_buy_signal,
                "매수 신호": "✅" if buy_signal else "❌"
            })

        except Exception as e:
            results.append({
                "종목": ticker,
                "에러": str(e)
            })

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
