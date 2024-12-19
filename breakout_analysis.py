import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import timedelta

class StockBreakoutAnalyzer:
    def __init__(self):
        st.title("Stock Breakout Strategy Backtester")
        self.ticker = st.text_input("Stock Ticker (e.g., AAPL)", "AAPL")
        self.start_date = st.date_input("Start Date")
        self.end_date = st.date_input("End Date")
        self.volume_threshold = st.number_input("Volume Breakout Threshold (%)", min_value=100, value=200)
        self.price_change_threshold = st.number_input("Daily Price Change Threshold (%)", min_value=1, value=2)
        self.holding_period = st.number_input("Holding Period (Days)", min_value=1, value=10)

    def analyze(self):
        if st.button("Generate Report"):
            st.write("Fetching Data...")
            try:
                data = yf.download(self.ticker, start=self.start_date, end=self.end_date)

                if data.empty:
                    st.error("No data found for the given ticker and date range.")
                    return
                elif 'Volume' not in data.columns or 'Close' not in data.columns:
                    st.error("Missing required data (Volume, Close).")
                    return

                data['Volume'] = data['Volume'].fillna(0)
                data['Close'] = data['Close'].ffill()
                data['Adj Close'] = data['Adj Close'].ffill()

                # Key change: Reset index after rolling average
                data['20DayAvgVol'] = data['Volume'].rolling(20).mean().reset_index(drop=True)
                data['DailyChangePct'] = data['Close'].pct_change() * 100

                data.dropna(inplace=True)  # Drop NaN after calculations

                breakout_days = data[
                    (data['Volume'] > (self.volume_threshold / 100) * data['20DayAvgVol']) &
                    (data['DailyChangePct'] > self.price_change_threshold)
                ]

                results = []
                for date in breakout_days.index:
                    buy_price = data.loc[date, 'Close']
                    sell_date = date + timedelta(days=self.holding_period)

                    if sell_date < data.index[-1]:
                        try:
                            sell_price = data.loc[sell_date, 'Close']
                            return_pct = ((sell_price - buy_price) / buy_price) * 100
                            results.append({
                                'Breakout Date': date,
                                'Buy Price': round(buy_price, 2),
                                'Sell Date': sell_date,
                                'Sell Price': round(sell_price, 2),
                                'Return (%)': round(return_pct, 2)
                            })
                        except KeyError:  # Handle cases where sell_date is not a trading day
                            pass
                    else:
                        st.warning(f"Breakout on {date.strftime('%Y-%m-%d')} cannot be fully evaluated due to insufficient data for the holding period.")

                if results:
                    results_df = pd.DataFrame(results)
                    st.write("### Breakout Analysis Results")
                    st.dataframe(results_df)
                    csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Report as CSV", csv, f"{self.ticker}_breakout_analysis.csv", "text/csv")
                else:
                    st.write("No breakout days found based on the criteria.")

            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    analyzer = StockBreakoutAnalyzer()
    analyzer.analyze()