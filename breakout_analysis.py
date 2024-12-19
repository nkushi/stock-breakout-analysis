import pandas as pd
import streamlit as st
from datetime import timedelta
import yfinance as yf

# Streamlit UI Setup
st.title("Stock Breakout Analysis Tool")

# User Inputs
ticker = st.text_input("Stock Ticker (e.g., AAPL)", "AAPL")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
volume_threshold = st.number_input("Volume Breakout Threshold (%)", min_value=100, value=200)
price_change_threshold = st.number_input("Daily Price Change Threshold (%)", min_value=1, value=2)
holding_period = st.number_input("Holding Period (Days)", min_value=1, value=10)

# Generate Report Button
if st.button("Generate Report"):
    st.write("Fetching Data...")

    try:
        # Fetch historical data using yfinance
        data = yf.download(ticker, start=start_date, end=end_date)

        # Validate data
        if data.empty:
            st.error("No data found for the given ticker and date range.")
        else:
            # Fill missing values in key columns
            data['Volume'] = data['Volume'].fillna(0)
            data['Close'] = data['Close'].ffill()

            # Calculate rolling average and daily change
            data['20DayAvgVol'] = data['Volume'].rolling(20).mean()
            data['DailyChangePct'] = (data['Close'].pct_change()) * 100

            # Debugging: Display the DataFrame to verify the structure
            st.write("### Debugging Data:")
            st.write(data.head(25))

            # Ensure NaN values are removed after calculations
            data = data.dropna(subset=['20DayAvgVol', 'DailyChangePct'])

            # More debugging: Ensure columns are created correctly
            if '20DayAvgVol' not in data.columns or 'DailyChangePct' not in data.columns:
                st.error("Columns '20DayAvgVol' and 'DailyChangePct' not found in the DataFrame.")
            else:
                # Identify Breakout Days
                breakout_days = data[(data['Volume'] > (volume_threshold / 100) * data['20DayAvgVol']) &
                                     (data['DailyChangePct'] > price_change_threshold)]

                # Debugging: Display breakout days DataFrame
                st.write("### Debugging Breakout Days:")
                st.write(breakout_days)

                # Calculate Holding Period Returns
                results = []
                for date in breakout_days.index:
                    buy_price = data.loc[date, 'Close']
                    sell_date = date + timedelta(days=holding_period)

                    # Ensure the sell date is within the data range
                    if sell_date in data.index:
                        sell_price = data.loc[sell_date, 'Close']
                        return_pct = ((sell_price - buy_price) / buy_price) * 100
                        results.append({
                            'Breakout Date': date,
                            'Buy Price': round(buy_price, 2),
                            'Sell Date': sell_date,
                            'Sell Price': round(sell_price, 2),
                            'Return (%)': round(return_pct, 2)
                        })

                # Display Results
                if results:
                    results_df = pd.DataFrame(results)
                    st.write("### Breakout Analysis Results")
                    st.dataframe(results_df)

                    # Downloadable CSV
                    csv = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Report as CSV", csv, f"{ticker}_breakout_analysis.csv", "text/csv")
                else:
                    st.write("No breakout days found based on the criteria.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
