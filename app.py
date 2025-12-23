# app.py
import math
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# -----------------------------
# Math helpers (no scipy needed)
# -----------------------------
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x: float) -> float:
    """Standard normal probability density function"""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

def black_scholes_price(S: float, K: float, T: float, sigma: float, r: float, option_type: str) -> float:
    """
    Black-Scholes (no dividends).
    S: spot
    K: strike
    T: time to maturity in years
    sigma: volatility (decimal, e.g. 0.2)
    r: risk-free rate (decimal, e.g. 0.03)
    option_type: 'Call' or 'Put'
    """
    if T <= 0:
        # Expired: intrinsic value
        if option_type == "Call":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    if sigma <= 0:
        # Zero vol: discounted intrinsic at expiry approximation
        forward = S * math.exp(r * T)
        if option_type == "Call":
            return math.exp(-r * T) * max(forward - K, 0.0)
        return math.exp(-r * T) * max(K - forward, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "Call":
        return S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)

def calculate_greeks(S: float, K: float, T: float, sigma: float, r: float, option_type: str) -> dict:
    """Calculate option Greeks: Delta, Gamma, Theta, Vega"""
    if T <= 0 or sigma <= 0:
        return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}
    
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    # Delta
    if option_type == "Call":
        delta = norm_cdf(d1)
    else:
        delta = norm_cdf(d1) - 1.0
    
    # Gamma (same for Call and Put)
    gamma = norm_pdf(d1) / (S * sigma * math.sqrt(T))
    
    # Theta (per year, negative for time decay)
    if option_type == "Call":
        theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                 - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365.0
    else:
        theta = (-S * norm_pdf(d1) * sigma / (2 * math.sqrt(T)) 
                 + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365.0
    
    # Vega (same for Call and Put, per 1% vol change)
    vega = S * norm_pdf(d1) * math.sqrt(T) / 100.0
    
    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega
    }

def calculate_payoff(S: float, K: float, option_type: str, premium: float = 0.0) -> float:
    """Calculate profit/loss at expiration"""
    if option_type == "Call":
        intrinsic = max(S - K, 0.0)
    else:
        intrinsic = max(K - S, 0.0)
    return intrinsic - premium

# -----------------------------
# Custom CSS Styling
# -----------------------------
def inject_custom_css():
    """Inject custom CSS matching the portfolio design system"""
    custom_css = """
    <style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* CSS Variables */
    :root {
        --primary-green: #123513;
        --deep-green: #0a1f0b;
        --accent-green: #1a4d1b;
        --neon-green: #39ff14;
        --cloud-white: #f5f5f0;
        --dark-bg: #0a0e0d;
        --darker-bg: #050807;
        --card-bg: rgba(18, 53, 19, 0.15);
        --glass-bg: rgba(255, 255, 255, 0.05);
        --text-primary: #f5f5f0;
        --text-secondary: #b8b8a8;
        --text-muted: #808070;
        --gradient-primary: linear-gradient(135deg, #123513 0%, #1a4d1b 100%);
        --gradient-glow: linear-gradient(135deg, rgba(57, 255, 20, 0.1) 0%, rgba(18, 53, 19, 0.2) 100%);
        --shadow-glow: 0 0 20px rgba(57, 255, 20, 0.3);
        --transition-smooth: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Main App Background */
    .stApp {
        background: var(--dark-bg);
        background-image: radial-gradient(circle at 50% 50%, rgba(18, 53, 19, 0.1) 0%, transparent 50%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Title Styling */
    h1 {
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--neon-green) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        text-shadow: 0 0 30px rgba(57, 255, 20, 0.3);
        margin-bottom: 1.5rem;
    }
    
    h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
    }
    
    /* Hide Sidebar */
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Main content full width */
    .main .block-container {
        max-width: 95%;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Ensure content is responsive */
    .stColumn {
        min-width: 0;
        flex: 1 1 0%;
    }
    
    /* Input Fields Container */
    .stNumberInput > div,
    .stSelectbox > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 1.2rem;
    }
    
    /* Glass card hover effect for input containers */
    .stColumn > div:has(.stNumberInput):hover,
    .stColumn > div:has(.stSelectbox):hover,
    .stColumn > div:has(.stSlider):hover {
        transform: translateY(-3px);
    }
    
    /* Input Fields */
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px;
        color: var(--text-primary) !important;
        font-size: 1rem;
        padding: 0.75rem 1rem !important;
        transition: var(--transition-smooth);
        width: 100%;
    }
    
    .stNumberInput > div > div > input:hover,
    .stSelectbox > div > div > select:hover {
        border-color: rgba(57, 255, 20, 0.4) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        outline: none !important;
        border-color: var(--neon-green) !important;
        box-shadow: 0 0 0 3px rgba(57, 255, 20, 0.2), 0 0 15px rgba(57, 255, 20, 0.3) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Input buttons */
    .stNumberInput button {
        background: rgba(57, 255, 20, 0.1) !important;
        border: 1px solid rgba(57, 255, 20, 0.3) !important;
        color: var(--neon-green) !important;
        border-radius: 8px !important;
        transition: var(--transition-smooth);
    }
    
    .stNumberInput button:hover {
        background: rgba(57, 255, 20, 0.2) !important;
        border-color: var(--neon-green) !important;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
        transform: scale(1.05);
    }
    
    /* Labels */
    label {
        color: var(--text-primary) !important;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    label:hover {
        color: var(--neon-green);
        text-shadow: 0 0 8px rgba(57, 255, 20, 0.5);
    }
    
    /* Metrics */
    .stMetric {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        transition: var(--transition-smooth);
    }
    
    .stMetric:hover {
        border-color: var(--neon-green);
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }
    
    .stMetric > div > div {
        color: var(--neon-green);
        font-weight: 700;
        font-size: 1.5rem;
    }
    
    .stMetric > div > label {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 15px;
        padding: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        font-weight: 600;
        border-radius: 10px;
        transition: var(--transition-smooth);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-primary);
        color: var(--neon-green);
        box-shadow: var(--shadow-glow);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--neon-green);
        background: rgba(57, 255, 20, 0.1);
    }
    
    /* Dividers */
    hr {
        border-color: rgba(57, 255, 20, 0.2);
        margin: 1.5rem 0;
    }
    
    /* Buttons (if any) */
    .stButton > button {
        background: var(--gradient-primary);
        color: var(--text-primary);
        border: 2px solid var(--neon-green);
        border-radius: 50px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: var(--transition-smooth);
    }
    
    .stButton > button:hover {
        box-shadow: var(--shadow-glow);
        transform: translateY(-2px);
    }
    
    /* Captions */
    .stCaption {
        color: var(--text-muted);
        font-size: 0.85rem;
    }
    
    /* Error Messages */
    .stAlert {
        background: rgba(255, 0, 0, 0.1);
        border: 1px solid rgba(255, 0, 0, 0.3);
        border-radius: 12px;
        color: var(--text-primary);
    }
    
    /* Info Messages */
    .stInfo {
        background: var(--glass-bg);
        border: 1px solid rgba(57, 255, 20, 0.3);
        border-radius: 12px;
        color: var(--text-primary);
    }
    
    /* Columns - Apply glass card styling */
    .stColumn {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: clamp(1rem, 2vw, 1.5rem);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .stColumn:hover {
        border-color: rgba(57, 255, 20, 0.5);
        box-shadow: 0 0 25px rgba(57, 255, 20, 0.25), 0 8px 30px rgba(0, 0, 0, 0.4);
        transform: translateY(-3px);
    }
    
    /* Plotly Chart Containers */
    .js-plotly-plot {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Slider Container */
    .stSlider > div {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: var(--transition-smooth);
    }
    
    .stSlider > div:hover {
        border-color: rgba(57, 255, 20, 0.4);
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.15);
        transform: translateY(-2px);
    }
    
    /* Slider Track */
    .stSlider > div > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        height: 6px;
        border-radius: 3px;
    }
    
    /* Slider Thumb */
    .stSlider > div > div > div > div {
        background: var(--neon-green) !important;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.6), 0 0 30px rgba(57, 255, 20, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.2);
        width: 20px;
        height: 20px;
        transition: var(--transition-smooth);
    }
    
    .stSlider > div > div > div > div:hover {
        box-shadow: 0 0 20px rgba(57, 255, 20, 0.8), 0 0 40px rgba(57, 255, 20, 0.5);
        transform: scale(1.2);
    }
    
    /* Slider Value Display */
    .stSlider > div > div > div + div {
        color: var(--neon-green) !important;
        font-weight: 700;
        font-size: 1rem;
        text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
    }
    
    /* Selectbox Dropdown */
    .stSelectbox > div > div {
        background: transparent !important;
        border: none !important;
    }
    
    .stSelectbox > div > div > select {
        background: transparent !important;
        color: var(--text-primary) !important;
    }
    
    .stSelectbox > div > div > select:hover {
        color: var(--neon-green);
    }
    
    /* Selectbox Dropdown Menu */
    [data-baseweb="select"] > div {
        background: rgba(10, 14, 13, 0.95) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(57, 255, 20, 0.3) !important;
        border-radius: 12px;
    }
    
    [data-baseweb="popover"] {
        background: rgba(10, 14, 13, 0.95) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(57, 255, 20, 0.3) !important;
        border-radius: 12px;
    }
    
    [data-baseweb="menu"] {
        background: transparent !important;
    }
    
    [data-baseweb="menu"] li {
        color: var(--text-secondary) !important;
        transition: var(--transition-smooth);
    }
    
    [data-baseweb="menu"] li:hover {
        background: rgba(57, 255, 20, 0.15) !important;
        color: var(--neon-green) !important;
    }
    
    [data-baseweb="menu"] li[aria-selected="true"] {
        background: rgba(57, 255, 20, 0.2) !important;
        color: var(--neon-green) !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--darker-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--gradient-primary);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--neon-green);
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
    }
    
    /* Text Colors */
    p, span, div {
        color: var(--text-secondary);
    }
    
    /* Glass Card Effect for Sections */
    .element-container {
        background: transparent;
    }
    
    /* Plotly Dark Theme Override */
    .plotly .modebar {
        background: var(--glass-bg) !important;
        border-radius: 8px;
    }
    
    .plotly .modebar-btn {
        color: var(--neon-green) !important;
    }
    
    /* Custom glow effect for important elements */
    .glow-text {
        text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
        color: var(--neon-green);
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* LaTeX Formula Styling */
    .katex {
        color: var(--neon-green) !important;
        font-size: 1.3rem !important;
    }
    
    .katex .mathnormal {
        color: var(--neon-green) !important;
    }
    
    .katex .mord {
        color: var(--neon-green) !important;
    }
    
    .katex .mrel {
        color: var(--neon-green) !important;
    }
    
    .katex .mbin {
        color: var(--neon-green) !important;
    }
    
    .katex .mopen {
        color: var(--neon-green) !important;
    }
    
    .katex .mclose {
        color: var(--neon-green) !important;
    }
    
    .katex .mpunct {
        color: var(--neon-green) !important;
    }
    
    .katex .mfrac {
        color: var(--neon-green) !important;
    }
    
    .katex .sqrt {
        color: var(--neon-green) !important;
    }
    
    .katex .mspace {
        color: var(--neon-green) !important;
    }
    
    .katex .msupsub {
        color: var(--neon-green) !important;
    }
    
    .katex .msubsup {
        color: var(--neon-green) !important;
    }
    
    .katex .mord.mathdefault {
        color: var(--neon-green) !important;
    }
    
    /* Ensure LaTeX formulas have proper spacing and styling */
    .element-container:has(.katex) {
        padding: 0.5rem 0;
        text-align: center;
    }
    
    /* Style LaTeX containers to match the design */
    .stLaTeX {
        background: transparent !important;
        padding: 0.5rem 0 !important;
    }
    
    /* Ensure formulas are centered within their containers */
    .katex-display {
        margin: 0.5rem 0 !important;
    }
    
    /* Glass card hover effects */
    div[style*="background: rgba(255, 255, 255, 0.05)"]:hover {
        border-color: rgba(57, 255, 20, 0.5) !important;
        box-shadow: 0 0 25px rgba(57, 255, 20, 0.25), 0 8px 30px rgba(0, 0, 0, 0.4) !important;
        transform: translateY(-3px);
    }
    
    /* Smooth transition for all glass cards */
    div[style*="background: rgba(255, 255, 255, 0.05)"] {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    /* ============================================
       RESPONSIVE DESIGN - MOBILE FIRST
       ============================================ */
    
    /* Tablets and below (max-width: 1024px) */
    @media (max-width: 1024px) {
        .main .block-container {
            max-width: 100%;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
        }
        
        h1 {
            font-size: 2rem !important;
        }
        
        h2 {
            font-size: 1.5rem !important;
        }
        
        h3 {
            font-size: 1.2rem !important;
        }
        
        /* Stack columns vertically */
        .stColumn {
            width: 100% !important;
            min-width: 100% !important;
        }
        
        /* Reduce padding in glass cards */
        div[style*="background: rgba(255, 255, 255, 0.05)"] {
            padding: 1rem !important;
        }
    }
    
    /* Mobile devices (max-width: 768px) */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        
        h1 {
            font-size: 1.8rem !important;
        }
        
        h2 {
            font-size: 1.3rem !important;
        }
        
        h3 {
            font-size: 1.1rem !important;
        }
        
        /* Input fields */
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            font-size: 0.9rem !important;
            padding: 0.6rem 0.8rem !important;
        }
        
        /* Labels */
        label {
            font-size: 0.85rem !important;
        }
        
        /* Buttons */
        .stNumberInput button {
            padding: 0.4rem !important;
        }
        
        /* Glass cards */
        div[style*="background: rgba(255, 255, 255, 0.05)"] {
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        
        /* Slider styling */
        .stSlider > div {
            padding: 0.8rem !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.85rem;
            padding: 0.5rem 0.8rem;
        }
        
        /* Metrics */
        .stMetric > div > div {
            font-size: 1.2rem !important;
        }
        
        .stMetric > div > label {
            font-size: 0.8rem !important;
        }
        
        /* Plotly charts */
        .js-plotly-plot {
            padding: 0.5rem !important;
        }
        
        /* Reduce hover lift effect on mobile */
        div[style*="background: rgba(255, 255, 255, 0.05)"]:hover {
            transform: none !important;
        }
    }
    
    /* Small mobile devices (max-width: 480px) */
    @media (max-width: 480px) {
        .main .block-container {
            padding-left: 0.75rem;
            padding-right: 0.75rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
        
        h2 {
            font-size: 1.2rem !important;
        }
        
        h3, h4 {
            font-size: 1rem !important;
        }
        
        /* Input fields */
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            font-size: 0.85rem !important;
            padding: 0.5rem 0.7rem !important;
        }
        
        /* Labels */
        label {
            font-size: 0.8rem !important;
        }
        
        /* Glass cards */
        div[style*="background: rgba(255, 255, 255, 0.05)"] {
            padding: 0.8rem !important;
            border-radius: 12px !important;
        }
        
        /* Buttons smaller */
        .stNumberInput button {
            padding: 0.3rem !important;
            min-width: 2rem;
        }
        
        /* Slider */
        .stSlider > div {
            padding: 0.6rem !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            font-size: 0.75rem;
            padding: 0.4rem 0.6rem;
        }
        
        /* Metrics */
        .stMetric > div > div {
            font-size: 1rem !important;
        }
        
        /* LaTeX formulas */
        .katex {
            font-size: 1rem !important;
        }
    }
    
    /* Ensure columns stack properly on mobile */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 0 0 100% !important;
            max-width: 100% !important;
        }
    }
    
    /* Fix grid layout on mobile */
    @media (max-width: 768px) {
        div[style*="display: grid"] {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Options Price • 3D Analysis (Black–Scholes)", layout="wide")

# Inject custom CSS
inject_custom_css()

# Header with gradient effect
st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="background: linear-gradient(135deg, #f5f5f0 0%, #39ff14 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-weight: 800;
                    font-size: 2.5rem;
                    text-shadow: 0 0 30px rgba(57, 255, 20, 0.3);
                    margin-bottom: 0.5rem;">
            Black-Scholes Options Pricing Model
        </h1>
        <p style="color: #b8b8a8; font-size: 1.1rem; margin-top: 0.5rem;">
            3D Visualization & Greeks Analysis
        </p>
    </div>
""", unsafe_allow_html=True)

# Black-Scholes Formula Explanation Section
st.markdown("""
    <div style="background: rgba(18, 53, 19, 0.3);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(57, 255, 20, 0.3);
                border-radius: 20px;
                padding: clamp(1rem, 3vw, 2rem);
                margin-bottom: 2rem;
                box-shadow: 0 0 30px rgba(57, 255, 20, 0.2);">
        <h2 style="color: #39ff14; 
                   font-weight: 700; 
                   text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                   margin-bottom: 1.5rem;
                   text-align: center;
                   font-size: clamp(1.2rem, 4vw, 1.8rem);">
            The Black-Scholes Formula
        </h2>
    </div>
""", unsafe_allow_html=True)

# Formulas Section
col_form1, col_form2 = st.columns(2)

with col_form1:
    st.markdown("""
        <div style="background: rgba(0, 0, 0, 0.3);
                    border-radius: 15px;
                    padding: clamp(1rem, 2.5vw, 1.5rem);
                    margin-bottom: 1rem;
                    border: 1px solid rgba(57, 255, 20, 0.2);">
            <h3 style="color: #f5f5f0; font-weight: 600; margin-bottom: 0.5rem; font-size: clamp(1rem, 3vw, 1.2rem);">Call Option Price:</h3>
        </div>
    """, unsafe_allow_html=True)
    st.latex(r"C = S_0 N(d_1) - K e^{-rT} N(d_2)")

with col_form2:
    st.markdown("""
        <div style="background: rgba(0, 0, 0, 0.3);
                    border-radius: 15px;
                    padding: clamp(1rem, 2.5vw, 1.5rem);
                    margin-bottom: 1rem;
                    border: 1px solid rgba(57, 255, 20, 0.2);">
            <h3 style="color: #f5f5f0; font-weight: 600; margin-bottom: 0.5rem; font-size: clamp(1rem, 3vw, 1.2rem);">Put Option Price:</h3>
        </div>
    """, unsafe_allow_html=True)
    st.latex(r"P = K e^{-rT} N(-d_2) - S_0 N(-d_1)")

# Where section
st.markdown("""
    <div style="background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: clamp(1rem, 2.5vw, 1.5rem);
                margin-top: 1rem;
                margin-bottom: 1rem;
                border: 1px solid rgba(57, 255, 20, 0.2);">
        <h4 style="color: #39ff14; font-weight: 600; margin-bottom: 0.5rem; font-size: clamp(0.9rem, 2.5vw, 1.1rem);">Where:</h4>
    </div>
""", unsafe_allow_html=True)

st.latex(r"d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}")
st.latex(r"d_2 = d_1 - \sigma\sqrt{T}")

# Spacer
st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

# Variable explanations in columns to ensure proper rendering
st.markdown("""
    <h3 style="color: #39ff14; 
               font-weight: 700; 
               text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
               margin-bottom: 1.5rem;
               text-align: center;
               font-size: clamp(1rem, 3vw, 1.3rem);">
        Variable Explanations
    </h3>
""", unsafe_allow_html=True)

# Use Streamlit columns for variable cards
var_col1, var_col2, var_col3 = st.columns(3)

with var_col1:
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">S₀</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Current Asset Price</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">The current market price of the underlying asset</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">K</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Strike Price</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">The price at which the option can be exercised</div>
        </div>
    """, unsafe_allow_html=True)

with var_col2:
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">T</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Time to Maturity</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">Time remaining until option expiration (in years)</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">σ (sigma)</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Volatility</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">Annualized standard deviation of asset returns (as decimal, e.g., 0.2 = 20%)</div>
        </div>
    """, unsafe_allow_html=True)

with var_col3:
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">r</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Risk-Free Rate</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">Annual risk-free interest rate (as decimal, e.g., 0.03 = 3%)</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: clamp(0.8rem, 2vw, 1.2rem);
                    margin-bottom: 1rem;">
            <div style="color: #39ff14; font-weight: 700; font-size: clamp(1rem, 2.5vw, 1.2rem); margin-bottom: 0.5rem;">N(·)</div>
            <div style="color: #b8b8a8; font-size: clamp(0.85rem, 2vw, 0.95rem); margin-bottom: 0.5rem;">Cumulative Distribution</div>
            <div style="color: #808070; font-size: clamp(0.75rem, 1.8vw, 0.85rem);">Standard normal cumulative distribution function</div>
        </div>
    """, unsafe_allow_html=True)

# Model Assumptions
st.markdown("""
    <div style="margin-top: 1.5rem; padding: clamp(0.8rem, 2vw, 1.2rem); 
                background: rgba(18, 53, 19, 0.4);
                border-radius: 12px;
                border-left: 3px solid #39ff14;
                margin-bottom: 2rem;">
        <h4 style="color: #39ff14; font-weight: 600; margin-bottom: 0.8rem; font-size: clamp(0.9rem, 2.5vw, 1.1rem);">Model Assumptions:</h4>
        <ul style="color: #b8b8a8; line-height: 1.8; margin-left: clamp(1rem, 2vw, 1.5rem); font-size: clamp(0.8rem, 2vw, 0.95rem);">
            <li>No dividends paid during the option's life</li>
            <li>European-style options (exercisable only at expiration)</li>
            <li>Constant volatility and risk-free rate</li>
            <li>Log-normal distribution of asset prices</li>
            <li>No transaction costs or taxes</li>
            <li>Continuous trading is possible</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

# Input Parameters Section
st.markdown("""
    <div style="background: rgba(18, 53, 19, 0.3);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(57, 255, 20, 0.3);
                border-radius: 20px;
                padding: clamp(1rem, 3vw, 2rem);
                margin-bottom: 2rem;
                box-shadow: 0 0 30px rgba(57, 255, 20, 0.2);">
        <h2 style="color: #39ff14; 
                   font-weight: 700; 
                   text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                   margin-bottom: 1.5rem;
                   text-align: center;
                   font-size: clamp(1.2rem, 4vw, 1.8rem);">
            Input Parameters
        </h2>
    </div>
""", unsafe_allow_html=True)

# Input fields in columns - styled via CSS
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    option_type = st.selectbox("Option Type", ["Call", "Put"], index=0)
    S0 = st.number_input("Current Asset Price (S₀)", min_value=0.0001, value=100.0, step=1.0, format="%.4f")
    K = st.number_input("Strike Price (K)", min_value=0.0001, value=100.0, step=1.0, format="%.4f")

with col2:
    T = st.number_input("Time to Maturity (T) - Years", min_value=0.0, value=1.0, step=0.05, format="%.4f")
    sigma = st.number_input("Volatility (σ)", min_value=0.0, value=0.20, step=0.01, format="%.4f")
    r = st.number_input("Risk-Free Rate (r)", value=0.03, step=0.005, format="%.4f")

with col3:
    min_spot = st.number_input("Min Spot Price", min_value=0.0001, value=max(1.0, S0 * 0.5), step=1.0, format="%.4f")
    max_spot = st.number_input("Max Spot Price", min_value=0.0001, value=S0 * 1.5, step=1.0, format="%.4f")

# Additional inputs for visualization
col4, col5 = st.columns(2, gap="medium")

with col4:
    min_vol = st.number_input("Min Volatility for Visualization", min_value=0.0, value=0.05, step=0.01, format="%.4f")
    max_vol = st.number_input("Max Volatility for Visualization", min_value=0.0, value=0.80, step=0.01, format="%.4f")

with col5:
    spot_points = st.slider("Spot Grid Points", min_value=20, max_value=200, value=80)
    vol_points = st.slider("Volatility Grid Points", min_value=20, max_value=200, value=80)

# Validation
errors = []
if max_spot <= min_spot:
    errors.append("Max Spot Price must be greater than Min Spot Price.")
if max_vol <= min_vol:
    errors.append("Max Volatility must be greater than Min Volatility.")
if K <= 0:
    errors.append("Strike must be > 0.")
if S0 <= 0:
    errors.append("Spot must be > 0.")

# Main content tabs
tab1, tab2, tab3 = st.tabs(["3D Surface & Price Analysis", "Payoff Diagram", "Greeks Analysis"])

with tab1:
    colA, colB = st.columns([1, 2], vertical_alignment="top")
    
    with colA:
        st.markdown("""
            <h3 style="color: #39ff14; 
                       font-weight: 700; 
                       text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                       margin-bottom: 1rem;">
                Current Option Metrics
            </h3>
        """, unsafe_allow_html=True)
        
        if errors:
            for e in errors:
                st.error(e)
        else:
            price = black_scholes_price(S0, K, T, sigma, r, option_type)
            greeks = calculate_greeks(S0, K, T, sigma, r, option_type)
            
            # Custom styled metric
            st.markdown(f"""
                <div style="background: rgba(18, 53, 19, 0.3);
                            backdrop-filter: blur(20px);
                            border: 1px solid rgba(57, 255, 20, 0.3);
                            border-radius: 15px;
                            padding: 1.5rem;
                            margin-bottom: 1rem;
                            box-shadow: 0 0 20px rgba(57, 255, 20, 0.2);">
                    <div style="color: #b8b8a8; font-size: 0.9rem; margin-bottom: 0.5rem;">Option Price</div>
                    <div style="color: #39ff14; font-size: 2rem; font-weight: 700; text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);">
                        ${price:.4f}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <div style="height: 1px; 
                            background: linear-gradient(90deg, transparent, rgba(57, 255, 20, 0.3), transparent);
                            margin: 1.5rem 0;"></div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <h4 style="color: #39ff14; 
                           font-weight: 600; 
                           margin-bottom: 1rem;">
                    Greeks
                </h4>
            """, unsafe_allow_html=True)
            
            # Styled Greeks metrics
            greeks_html = f"""
            <div style="display: grid; gap: 0.75rem;">
                <div style="background: rgba(255, 255, 255, 0.05);
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 12px;
                            padding: 1rem;
                            transition: all 0.3s ease;">
                    <div style="color: #b8b8a8; font-size: 0.85rem; margin-bottom: 0.3rem;">Delta (Δ)</div>
                    <div style="color: #39ff14; font-size: 1.3rem; font-weight: 700;">{greeks['delta']:.4f}</div>
                    <div style="color: #808070; font-size: 0.75rem; margin-top: 0.3rem;">Price sensitivity</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.05);
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 12px;
                            padding: 1rem;">
                    <div style="color: #b8b8a8; font-size: 0.85rem; margin-bottom: 0.3rem;">Gamma (Γ)</div>
                    <div style="color: #39ff14; font-size: 1.3rem; font-weight: 700;">{greeks['gamma']:.6f}</div>
                    <div style="color: #808070; font-size: 0.75rem; margin-top: 0.3rem;">Delta sensitivity</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.05);
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 12px;
                            padding: 1rem;">
                    <div style="color: #b8b8a8; font-size: 0.85rem; margin-bottom: 0.3rem;">Theta (Θ)</div>
                    <div style="color: #39ff14; font-size: 1.3rem; font-weight: 700;">${greeks['theta']:.4f}/day</div>
                    <div style="color: #808070; font-size: 0.75rem; margin-top: 0.3rem;">Time decay</div>
                </div>
                <div style="background: rgba(255, 255, 255, 0.05);
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 12px;
                            padding: 1rem;">
                    <div style="color: #b8b8a8; font-size: 0.85rem; margin-bottom: 0.3rem;">Vega (ν)</div>
                    <div style="color: #39ff14; font-size: 1.3rem; font-weight: 700;">${greeks['vega']:.4f}/1%</div>
                    <div style="color: #808070; font-size: 0.75rem; margin-top: 0.3rem;">Volatility sensitivity</div>
                </div>
            </div>
            """
            st.markdown(greeks_html, unsafe_allow_html=True)
            
            st.markdown("""
                <div style="margin-top: 1rem; padding: 1rem; 
                            background: rgba(18, 53, 19, 0.2);
                            border-radius: 10px;
                            border-left: 3px solid #39ff14;">
                    <p style="color: #b8b8a8; font-size: 0.85rem; margin: 0;">
                        <strong style="color: #39ff14;">Model:</strong> Black–Scholes (no dividends)<br>
                        Rates & vol in decimals (e.g., 0.2 = 20%)
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    with colB:
        st.markdown("""
            <h3 style="color: #39ff14; 
                       font-weight: 700; 
                       text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                       margin-bottom: 1rem;">
                3D Surface Plot: Option Price (Buy/Sell Values)
            </h3>
        """, unsafe_allow_html=True)
        
        if errors:
            st.info("Fix the input errors to render the 3D surface.")
        else:
            S_vals = np.linspace(min_spot, max_spot, spot_points)
            vol_vals = np.linspace(min_vol, max_vol, vol_points)
            
            # Create meshgrid for 3D surface
            S_mesh, vol_mesh = np.meshgrid(S_vals, vol_vals)
            
            # Calculate prices for all combinations
            Z = np.zeros_like(S_mesh, dtype=float)
            for i in range(len(vol_vals)):
                for j in range(len(S_vals)):
                    Z[i, j] = black_scholes_price(float(S_mesh[i, j]), float(K), float(T), 
                                                  float(vol_mesh[i, j]), float(r), option_type)
            
            # Create 3D surface plot
            fig = go.Figure(
                data=go.Surface(
                    x=S_mesh,
                    y=vol_mesh,
                    z=Z,
                    colorscale="Viridis",
                    colorbar={"title": "Option Price ($)"},
                    hovertemplate="Spot: $%{x:.2f}<br>Vol: %{y:.2%}<br>Price: $%{z:.4f}<extra></extra>",
                )
            )
            
            # Add current point marker
            current_price = black_scholes_price(S0, K, T, sigma, r, option_type)
            fig.add_trace(go.Scatter3d(
                x=[S0],
                y=[sigma],
                z=[current_price],
                mode='markers',
                marker=dict(
                    size=10,
                    color='red',
                    symbol='diamond',
                    line=dict(width=2, color='white')
                ),
                name='Current Position',
                hovertemplate=f"Current Spot: ${S0:.2f}<br>Current Vol: {sigma:.2%}<br>Current Price: ${current_price:.4f}<extra></extra>"
            ))
            
            fig.update_layout(
                scene=dict(
                    xaxis_title="Spot Price (S) [$]",
                    yaxis_title="Volatility (σ) [%]",
                    zaxis_title="Option Price [$]",
                    camera=dict(
                        eye=dict(x=1.5, y=1.5, z=1.2)
                    ),
                    aspectmode="manual",
                    aspectratio=dict(x=1, y=1, z=0.7)
                ),
                height=700,
                margin={"l": 0, "r": 0, "t": 20, "b": 0},
                title=f"3D Surface: {option_type} Option Price Surface"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.caption("Tip: Rotate, zoom, and pan the 3D surface to explore buy/sell values at different spot prices and volatilities.")

with tab2:
    st.markdown("""
        <h3 style="color: #39ff14; 
                   font-weight: 700; 
                   text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                   margin-bottom: 1rem;">
            Payoff Diagram: Profit/Loss at Expiration
        </h3>
    """, unsafe_allow_html=True)
    
    if errors:
        st.info("Fix the input errors to render the payoff diagram.")
    else:
        # Calculate current option price
        current_premium = black_scholes_price(S0, K, T, sigma, r, option_type)
        
        # Create spot price range for payoff
        payoff_range = max(max_spot, K * 2) - min(min_spot, K * 0.5)
        S_payoff = np.linspace(max(1.0, K * 0.5), K * 2, 200)
        
        # Calculate payoffs
        payoffs_long = [calculate_payoff(s, K, option_type, current_premium) for s in S_payoff]
        payoffs_short = [-p for p in payoffs_long]  # Short position is opposite
        
        # Intrinsic values
        if option_type == "Call":
            intrinsic = [max(s - K, 0) for s in S_payoff]
        else:
            intrinsic = [max(K - s, 0) for s in S_payoff]
        
        fig = go.Figure()
        
        # Long position payoff
        fig.add_trace(go.Scatter(
            x=S_payoff,
            y=payoffs_long,
            mode='lines',
            name=f'Long {option_type} (Buy)',
            line=dict(color='#39ff14', width=3),
            hovertemplate="Spot: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
        ))
        
        # Short position payoff
        fig.add_trace(go.Scatter(
            x=S_payoff,
            y=payoffs_short,
            mode='lines',
            name=f'Short {option_type} (Sell)',
            line=dict(color='#ff3333', width=3, dash='dash'),
            hovertemplate="Spot: $%{x:.2f}<br>P&L: $%{y:.2f}<extra></extra>"
        ))
        
        # Intrinsic value line
        fig.add_trace(go.Scatter(
            x=S_payoff,
            y=intrinsic,
            mode='lines',
            name='Intrinsic Value',
            line=dict(color='gray', width=2, dash='dot'),
            hovertemplate="Spot: $%{x:.2f}<br>Intrinsic: $%{y:.2f}<extra></extra>"
        ))
        
        # Break-even line
        if option_type == "Call":
            breakeven = K + current_premium
        else:
            breakeven = K - current_premium
        
        fig.add_vline(
            x=breakeven,
            line_dash="dash",
            line_color="yellow",
            annotation_text=f"Break-even: ${breakeven:.2f}",
            annotation_position="top"
        )
        
        # Strike line
        fig.add_vline(
            x=K,
            line_dash="dot",
            line_color="white",
            annotation_text=f"Strike: ${K:.2f}",
            annotation_position="bottom"
        )
        
        # Current spot line
        fig.add_vline(
            x=S0,
            line_dash="solid",
            line_color="cyan",
            annotation_text=f"Current Spot: ${S0:.2f}",
            annotation_position="top"
        )
        
        # Zero P&L line
        fig.add_hline(y=0, line_dash="dot", line_color="white", opacity=0.5)
        
        fig.update_layout(
            xaxis_title="Spot Price at Expiration ($)",
            yaxis_title="Profit/Loss ($)",
            height=600,
            hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            title=f"{option_type} Option Payoff Diagram (Premium: ${current_premium:.4f})"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Payoff metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Premium Paid", f"${current_premium:.4f}")
        with col2:
            st.metric("Break-even Price", f"${breakeven:.2f}")
        with col3:
            max_profit = max(payoffs_long) if option_type == "Call" else max(payoffs_long)
            st.metric("Max Profit", f"${max_profit:.2f}")
        with col4:
            max_loss = min(payoffs_long)
            st.metric("Max Loss", f"${max_loss:.2f}")

with tab3:
    st.markdown("""
        <h3 style="color: #39ff14; 
                   font-weight: 700; 
                   text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
                   margin-bottom: 1rem;">
            Greeks Sensitivity Analysis
        </h3>
    """, unsafe_allow_html=True)
    
    if errors:
        st.info("Fix the input errors to render the Greeks analysis.")
    else:
        # Delta analysis
        st.markdown("""
            <h4 style="color: #39ff14; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;">
                Delta (Δ) - Price Sensitivity
            </h4>
        """, unsafe_allow_html=True)
        S_delta = np.linspace(min_spot, max_spot, 100)
        deltas = []
        for s in S_delta:
            g = calculate_greeks(s, K, T, sigma, r, option_type)
            deltas.append(g['delta'])
        
        fig_delta = go.Figure()
        fig_delta.add_trace(go.Scatter(
            x=S_delta,
            y=deltas,
            mode='lines',
            name='Delta',
            line=dict(color='#39ff14', width=3),
            hovertemplate="Spot: $%{x:.2f}<br>Delta: %{y:.4f}<extra></extra>"
        ))
        fig_delta.add_vline(x=S0, line_dash="dash", line_color="cyan", 
                           annotation_text=f"Current: ${S0:.2f}")
        fig_delta.update_layout(
            xaxis_title="Spot Price ($)",
            yaxis_title="Delta (Δ)",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_delta, use_container_width=True)
        
        # Gamma analysis
        st.markdown("""
            <h4 style="color: #39ff14; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;">
                Gamma (Γ) - Delta Sensitivity
            </h4>
        """, unsafe_allow_html=True)
        gammas = []
        for s in S_delta:
            g = calculate_greeks(s, K, T, sigma, r, option_type)
            gammas.append(g['gamma'])
        
        fig_gamma = go.Figure()
        fig_gamma.add_trace(go.Scatter(
            x=S_delta,
            y=gammas,
            mode='lines',
            name='Gamma',
            line=dict(color='#ff6b6b', width=3),
            hovertemplate="Spot: $%{x:.2f}<br>Gamma: %{y:.6f}<extra></extra>"
        ))
        fig_gamma.add_vline(x=S0, line_dash="dash", line_color="cyan",
                           annotation_text=f"Current: ${S0:.2f}")
        fig_gamma.update_layout(
            xaxis_title="Spot Price ($)",
            yaxis_title="Gamma (Γ)",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_gamma, use_container_width=True)
        
        # Theta analysis (time decay)
        st.markdown("""
            <h4 style="color: #39ff14; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;">
                Theta (Θ) - Time Decay
            </h4>
        """, unsafe_allow_html=True)
        if T > 0:
            time_remaining = np.linspace(0.01, T * 1.5, 100)
            thetas = []
            for t in time_remaining:
                g = calculate_greeks(S0, K, t, sigma, r, option_type)
                thetas.append(g['theta'])
            
            fig_theta = go.Figure()
            fig_theta.add_trace(go.Scatter(
                x=time_remaining * 365,  # Convert to days
                y=thetas,
                mode='lines',
                name='Theta',
                line=dict(color='#ffa500', width=3),
                hovertemplate="Days Remaining: %{x:.1f}<br>Theta: $%{y:.4f}/day<extra></extra>"
            ))
            fig_theta.add_vline(x=T * 365, line_dash="dash", line_color="cyan",
                               annotation_text=f"Current: {T*365:.1f} days")
            fig_theta.update_layout(
                xaxis_title="Days to Expiration",
                yaxis_title="Theta (Θ) [$/day]",
                height=300,
                hovermode='x unified'
            )
            st.plotly_chart(fig_theta, use_container_width=True)
        
        # Vega analysis
        st.markdown("""
            <h4 style="color: #39ff14; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem;">
                Vega (ν) - Volatility Sensitivity
            </h4>
        """, unsafe_allow_html=True)
        vol_range = np.linspace(max(0.01, min_vol), max_vol, 100)
        vegas = []
        for v in vol_range:
            g = calculate_greeks(S0, K, T, v, r, option_type)
            vegas.append(g['vega'])
        
        fig_vega = go.Figure()
        fig_vega.add_trace(go.Scatter(
            x=vol_range * 100,  # Convert to percentage
            y=vegas,
            mode='lines',
            name='Vega',
            line=dict(color='#9b59b6', width=3),
            hovertemplate="Volatility: %{x:.2f}%<br>Vega: $%{y:.4f}/1%<extra></extra>"
        ))
        fig_vega.add_vline(x=sigma * 100, line_dash="dash", line_color="cyan",
                          annotation_text=f"Current: {sigma*100:.1f}%")
        fig_vega.update_layout(
            xaxis_title="Volatility (%)",
            yaxis_title="Vega (ν) [$/1%]",
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig_vega, use_container_width=True)
        
        st.caption("Greeks show how option price changes with underlying parameters. Use these to understand risk exposure.")

# Footer
st.markdown("""
    <div style="margin-top: 3rem; padding: 1.5rem; 
                background: rgba(18, 53, 19, 0.2);
                border-radius: 15px;
                border: 1px solid rgba(57, 255, 20, 0.2);
                text-align: center;">
        <p style="color: #b8b8a8; margin: 0; font-size: 0.9rem;">
            <strong style="color: #39ff14;">Tip:</strong> Increase grid points for smoother 3D surface (may be slower). 
            Use the interactive charts to analyze buy/sell opportunities.
        </p>
    </div>
""", unsafe_allow_html=True)

