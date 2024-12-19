import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import timedelta

# Streamlit UI Setup
st.title("Stock Breakout Strategy Backtester")

# User Inputs
ticker = st.text_input("Stock Ticker (e.g., AAPL)", "AAPL")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
volume_threshold = st.number_input("Volume Breakout Threshold (%)", min_value=100, value=200)
price_change_threshold = st.number_input("Daily Price Change Threshold (%)", min_value=1, value=2)
holding_period = st.number_input("Holding Period (Days)", min_value=1, value=10)

if st.button("Generate Report"):
    st.write("Fetching Data...")
    try:
        data = yf.download(ticker, start=start_date, end=end_date)

        if data.empty:
            st.error("No data found for the given ticker and date range.")
        elif 'Volume' not in data.columns or 'Close' not in data.columns:
            st.error("Missing required data (Volume, Close).")
        else:
            data['Volume'] = data['Volume'].fillna(0)
            data['Close'] = data['Close'].fillna(method='ffill')
            data['Adj Close'] = data['Adj Close'].fillna(method='ffill')

            data['20DayAvgVol'] = data['Volume'].rolling(20).mean()
            data['DailyChangePct'] = data['Close'].pct_change() * 100
            data.dropna(inplace=True)  # Crucial: Remove NaN from rolling calculations

            breakout_days = data[
                (data['Volume'] > (volume_threshold / 100) * data['20DayAvgVol']) &
                (data['DailyChangePct'] > price_change_threshold)
            ]

            results = []
            for date in breakout_days.index:
                buy_price = data.loc[date, 'Close']
                sell_date = date + timedelta(days=holding_period)

                # Lookahead Bias Prevention: Check if sell_date is within the data range
                if sell_date < data.index[-1]:  # Check if sell date is not beyond the last date
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
                    except KeyError: # Handle cases where the exact sell_date might not be a trading day
                        pass
                else:
                    st.warning(f"Breakout on {date.strftime('%Y-%m-%d')} cannot be fully evaluated due to insufficient data for the holding period.")

            if results:
                results_df = pd.DataFrame(results)
                st.write("### Breakout Analysis Results")
                st.dataframe(results_df)
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Report as CSV", csv, f"{ticker}_breakout_analysis.csv", "text/csv")
            else:
                st.write("No breakout days found based on the criteria.")

    except Exception as e:
        st.error(f"Error: {e}")