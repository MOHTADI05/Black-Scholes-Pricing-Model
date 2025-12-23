# Black-Scholes Option Pricing Model with Interactive Heatmap

A Streamlit application that calculates Black-Scholes option prices and visualizes them as an interactive heatmap over Spot Price (S) and Volatility (σ).

## Features

- **Black-Scholes Pricing**: Calculate option prices for both Call and Put options
- **Interactive Heatmap**: Visualize how option prices vary with Spot Price and Volatility
- **Customizable Parameters**: Adjust all model inputs including strike, time to maturity, risk-free rate, and volatility
- **Adjustable Grid Resolution**: Control the smoothness of the heatmap visualization

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your default web browser.

## Parameters

- **Option Type**: Call or Put
- **Current Asset Price (S)**: Current spot price of the underlying asset
- **Strike Price (K)**: Option strike price
- **Time to Maturity (T)**: Time until expiration in years
- **Volatility (σ)**: Annual volatility (as a decimal, e.g., 0.2 for 20%)
- **Risk-Free Interest Rate (r)**: Annual risk-free rate (as a decimal, e.g., 0.03 for 3%)
- **Heatmap Ranges**: Define the range of Spot Prices and Volatilities to visualize
- **Grid Points**: Control the resolution of the heatmap (more points = smoother but slower)

## Model Details

The Black-Scholes model assumes:
- No dividends
- Constant volatility
- Constant risk-free rate
- Log-normal distribution of asset prices
- European-style options (exercisable only at expiration)

## Notes

- Rates and volatility should be entered as decimals (e.g., 0.2 = 20%)
- Higher grid point values will produce smoother heatmaps but may take longer to compute
- The heatmap shows option prices across different combinations of Spot Price and Volatility

