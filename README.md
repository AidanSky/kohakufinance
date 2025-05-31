# Kohaku Finance

Kohaku Finance is a web application for visualizing stock market data, allowing users to graph stock prices, calculate technical indicators like Simple Moving Average (SMA) and Relative Strength Index (RSI), compare stocks, and analyze percentage changes over customizable date ranges.

This app was made by a novice and should not be used for reliable market information. It is currently in debug mode, and likely contains many bugs and malpractices.

Nothing on this website should be interpreted as advice. This was made for educational purposes only.

## Features

- **Stock Price Visualization**: Plot stock prices (Open, Close, High, Low) for a selected ticker.
- **Technical Indicators**:
  - Simple Moving Average (SMA) with customizable length.
  - Relative Strength Index (RSI) with customizable length and overbought/oversold thresholds.
- **Stock Comparison**: Compare percentage changes of two stocks.
- **Percentage Change**: View percentage changes for a single stock.
- **Flexible Date Ranges**: Choose predefined ranges (1 day, 1 week, 1 month, 6 months, YTD, 1 year, 5 years) or a custom range.
- **Responsive Design**: Built with Bootstrap for a mobile-friendly interface.
- **Error Handling**: Displays user-friendly error messages for invalid inputs or API issues.

## Technologies Used

- **Frontend**:
  - HTML, CSS (Bootstrap), JavaScript
  - Chart.js for plotting charts
- **Backend**:
  - Python with Flask
  - yfinance for fetching stock data
  - pandas for data processing
- **Deployment**:
  - Flask development server (debug mode)

## Setup and Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Git

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/AidanSky/kohakufinance.git
   cd sky-finance
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure `requirements.txt` includes:
   ```
   flask
   yfinance
   pandas
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

## Usage

1. **Select a Function**:
   - Choose from Graph, Compare, Percentage, or Simple Moving Average.
2. **Input Stock Symbol(s)**:
   - Enter a valid stock ticker (e.g., AAPL for Apple). For comparison, provide a second ticker.
3. **Choose Data Type**:
   - Select Open, Close, High, or Low prices.
4. **Set Date Range**:
   - Pick a predefined range or enable Custom Range to specify start and end dates.
5. **Configure Technical Indicators** (if applicable):
   - Enable SMA or RSI and set the calculation length.
6. **Update Chart**:
   - Click "Update Chart" to fetch and display the data.
7. **View Results**:
   - Stock price chart appears at the bottom, with RSI chart (if enabled) below it.
   - Error messages appear in a dismissible alert if issues occur.

## File Structure

- `app.py`: Flask backend handling API requests and stock data processing.
- `index.html`: Main HTML template for the frontend interface.
- `main.js`: JavaScript for Chart.js integration, event listeners, and API calls.
- `styles.css`: Custom CSS for styling charts.
- `templates/`: Directory containing `index.html` (Flask convention).
- `static/`: Directory for `main.js` and `styles.css`.

## Notes

- **API Limitations**: The app uses `yfinance`, which may have rate limits or data availability issues. Ensure a stable internet connection.
- **Time Zones**: Intraday data (1 day, 1 week) is converted to America/New_York time.
- **Error Handling**: Invalid tickers, date ranges, or missing inputs trigger error messages.
- **Future Improvements**:
  - Add more technical indicators (e.g., MACD, Bollinger Bands).
  - Implement user authentication for personalized watchlists.
  - Optimize data fetching for faster performance.

## Contributing

Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License

This project uses the `yfinance` library to fetch stock data from Yahoo Finance. Ensure compliance with Yahoo Finance's terms of service for non-commercial use.

## Third-Party Libraries
- yfinance (Apache 2.0 License)
- Chart.js (MIT License)
- Bootstrap (MIT License)
