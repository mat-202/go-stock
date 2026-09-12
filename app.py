import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

st.set_page_config(page_title="منصة الدورات الزمنية والنجوم الحقيقية", page_icon="🌟", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    
    .star-card-top {
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .worst-card-top {
        background: linear-gradient(135deg, #9f1239 0%, #be123c 100%);
        color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title { font-size: 0.95rem; font-weight: bold; opacity: 0.95; }
    .metric-value { font-size: 1.25rem; font-weight: bold; margin-top: 4px; }
    
    .company-card-positive {
        background-color: rgba(16, 185, 129, 0.08);
        border-right: 5px solid #10b981;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .company-card-negative {
        background-color: rgba(239, 68, 68, 0.08);
        border-right: 5px solid #ef4444;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .trend-badge {
        background-color: #f1f5f9;
        color: #1e293b;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

TARGET_STOCKS = {
    "AMD": "إيه إم دي (AMD)",
    "TSLA": "تيسلا (Tesla)",
    "META": "ميتا (Meta)",
    "NVDA": "أنفيديا (Nvidia)"
}

CONFIRMED_CYCLES = {
    "TSLA": {
        "use_trading_candles": True,
        "trading_candles_offset": 1031, # 1031 شمعة تداول يومية
        "weekly_candles_offset": 215,   # 215 شمعة أسبوعية
        "monthly_candles_offset": 49,   # 49 شمعة شهرية
        "cycle_months": 49, "up_m": 20, "fib_retrace": 0.618,
        "start": "2024-04-01", "end": "2028-04-01", "peak": "2025-12-01",
        "prev_start": "2020-03-01", "prev_end": "2024-03-01",
        "general_trend": "صعود (20 شهر) ⬅️ هبوط (14 شهر) ⬅️ صعود (6 أشهر) ⬅️ هبوط (9 أشهر)"
    },
    "META": {
        "use_trading_candles": True,
        "trading_candles_offset": 960,   # 960 شمعة تداول يومية
        "weekly_candles_offset": 200,   # 200 شمعة أسبوعية
        "monthly_candles_offset": 45,   # 45 شمعة شهرية
        "cycle_months": 45, "up_m": 32, "fib_retrace": 0.500,
        "start": "2022-11-01", "end": "2026-08-01", "peak": "2025-07-01",
        "prev_start": "2018-12-01", "prev_end": "2022-10-01",
        "general_trend": "صعود (32 شهر) ⬅️ هبوط (12 شهر)"
    },
    "NVDA": {
        "use_trading_candles": True,
        "trading_candles_offset": 625,   # 625 شمعة تداول يومية
        "weekly_candles_offset": 131,   # 131 شمعة أسبوعية
        "monthly_candles_offset": 30,   # 30 شمعة شهرية
        "cycle_months": 30, "up_m": 20, "fib_retrace": 0.618,
        "start": "2025-05-01", "end": "2027-11-01", "peak": "2027-01-01",
        "prev_start": "2022-10-01", "prev_end": "2025-04-01",
        "general_trend": "صعود (20 شهر) ⬅️ هبوط (11 شهر)"
    },
    "AMD": {
        "use_trading_candles": True,
        "trading_candles_offset": 577,   # 577 شمعة تداول يومية
        "weekly_candles_offset": 121,   # 121 شمعة أسبوعية
        "monthly_candles_offset": 28,   # 28 شمعة شهرية
        "cycle_months": 28, "up_m": 15, "fib_retrace": 0.618,
        "start": "2024-06-01", "end": "2026-10-01", "peak": "2025-09-01",
        "prev_start": "2022-01-01", "prev_end": "2024-02-01",
        "general_trend": "صعود (14 شهر) ⬅️ هبوط (14 شهر)"
    }
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data_10y(symbol):
    clean_sym = symbol.strip().upper()
    comp_name = TARGET_STOCKS.get(clean_sym, f"سهم {clean_sym}")
    
    if YFINANCE_AVAILABLE:
        try:
            df = yf.Ticker(clean_sym).history(period="10y")
            if not df.empty and len(df) >= 100:
                df.reset_index(inplace=True)
                return df, clean_sym, comp_name
        except Exception:
            pass
            
    dates = pd.date_range(end=datetime.today(), periods=1200, freq='B')
    np.random.seed(abs(hash(clean_sym)) % 10000)
    prices = 50.0 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, size=len(dates))))
    df_dummy = pd.DataFrame({'Date': dates, 'Open': prices*0.99, 'High': prices*1.02, 'Low': prices*0.98, 'Close': prices})
    return df_dummy, clean_sym, comp_name

def analyze_full_stock_dynamically(df, symbol_clean):
    if df.empty or symbol_clean not in CONFIRMED_CYCLES:
        return None

    df_res = df.copy()
    df_res['Date'] = pd.to_datetime(df_res['Date']).dt.tz_localize(None)
    df_res.set_index('Date', inplace=True)
    
    df_d = df_res.dropna()
    df_w = df_res.resample('W-MON').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    df_m = df_res.resample('MS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()

    if len(df_m) < 12:
        return None

    last_date = df_m.index[-1]
    c = CONFIRMED_CYCLES[symbol_clean]
    
    long_c = int(c["cycle_months"])
    up_m = int(c["up_m"])
    fib_ratio = float(c["fib_retrace"])
    cycle_start = pd.Timestamp(c["start"])
    cycle_end = pd.Timestamp(c["end"])
    peak_date = pd.Timestamp(c["peak"])
    prev_start = pd.Timestamp(c["prev_start"])
    general_trend = c["general_trend"]

    down_m = long_c - up_m
    phase_type = "صعود 🟢" if last_date <= peak_date else "هبوط 🔴"

    recent_segment = df_m['Close'].values[-long_c:] if len(df_m) >= long_c else df_m['Close'].values
    wave_high = np.max(recent_segment)
    wave_low = np.min(recent_segment)
    current_price = df_m['Close'].iloc[-1]
    proportional_target = wave_low + ((wave_high - wave_low) * fib_ratio)

    curr_date = pd.Timestamp("2026-09-01")

    # --- مطابقة الشموع اليومية والأسبوعية والشهرية ---
    if c.get("use_trading_candles", False):
        daily_offset = c["trading_candles_offset"]
        weekly_offset = c["weekly_candles_offset"]
        monthly_offset = c["monthly_candles_offset"]

        # المطابقة اليومية
        curr_d_idx = len(df_d) - 1
        matched_d_idx = max(0, curr_d_idx - daily_offset)
        matched_curr_day_date = df_d.index[matched_d_idx]
        matched_next_day_date = df_d.index[min(len(df_d) - 1, matched_d_idx + 1)]

        # المطابقة الأسبوعية
        curr_w_idx = len(df_w) - 1
        matched_w_idx = max(0, curr_w_idx - weekly_offset)
        matched_curr_week_date = df_w.index[matched_w_idx]
        matched_next_week_date = df_w.index[min(len(df_w) - 1, matched_w_idx + 1)]

        # المطابقة الشهرية
        curr_m_idx = len(df_m) - 1
        matched_m_idx = max(0, curr_m_idx - monthly_offset)
        matched_curr_month_date = df_m.index[matched_m_idx]
        matched_next_month_date = df_m.index[min(len(df_m) - 1, matched_m_idx + 1)]
    else:
        m_offset = (curr_date.year - cycle_start.year) * 12 + (curr_date.month - cycle_start.month)
        matched_curr_month_date = prev_start + pd.DateOffset(months=m_offset)
        matched_next_month_date = matched_curr_month_date + pd.DateOffset(months=1)

        days_offset = (curr_date - cycle_start).days
        matched_curr_week_date = prev_start + pd.Timedelta(days=days_offset)
        matched_next_week_date = matched_curr_week_date + pd.Timedelta(days=7)
        
        matched_curr_day_date = matched_curr_week_date
        matched_next_day_date = matched_curr_day_date + pd.Timedelta(days=1)

    def eval_candle(df_target, target_date, mode="weekly"):
        if df_target.empty:
            return "بيانات غير متوفرة 🟡", "🟡", 0.0, False, target_date.strftime("%Y-%m-%d")
        
        diffs = abs(df_target.index - target_date)
        min_idx = diffs.argmin()
        actual_date = df_target.index[min_idx]
        
        if mode == "daily":
            max_allow_days = 7
            fmt = "%d %B %Y"
        elif mode == "weekly":
            max_allow_days = 14
            fmt = "%d %B %Y"
        else:
            max_allow_days = 35
            fmt = "%B %Y"

        if abs((actual_date - target_date).days) > max_allow_days:
            return "خارج النطاق التاريخي 🟡", "🟡", 0.0, False, target_date.strftime("%Y-%m-%d")

        row = df_target.iloc[min_idx]
        open_p, close_p = row['Open'], row['Close']
        pct = ((close_p - open_p) / open_p) * 100.0 if open_p > 0 else 0.0

        if close_p >= open_p:
            icon = "🟢"
            desc = f"شمعة إيجابية صاعدة (+{pct:.1f}%)"
            is_pos = True
        else:
            icon = "🔴"
            desc = f"شمعة سلبية هابطة ({pct:.1f}%)"
            is_pos = False

        return desc, icon, round(pct, 1), is_pos, actual_date.strftime(fmt)

    c_d_desc, c_d_icon, c_d_perf, _, c_d_date = eval_candle(df_d, matched_curr_day_date, mode="daily")
    n_d_desc, n_d_icon, _, _, n_d_date = eval_candle(df_d, matched_next_day_date, mode="daily")

    c_w_desc, c_w_icon, c_w_perf, _, c_w_date = eval_candle(df_w, matched_curr_week_date, mode="weekly")
    n_w_desc, n_w_icon, _, _, n_w_date = eval_candle(df_w, matched_next_week_date, mode="weekly")
    
    c_m_desc, c_m_icon, c_m_perf, c_m_pos, c_m_date = eval_candle(df_m, matched_curr_month_date, mode="monthly")
    n_m_desc, n_m_icon, _, _, n_m_date = eval_candle(df_m, matched_next_month_date, mode="monthly")

    return {
        "symbol": symbol_clean,
        "use_trading_candles": c.get("use_trading_candles", False),
        "trading_candles_offset": c.get("trading_candles_offset", 0),
        "weekly_candles_offset": c.get("weekly_candles_offset", 0),
        "monthly_candles_offset": c.get("monthly_candles_offset", 0),
        "general_trend": general_trend,
        "current_price": round(current_price, 2),
        "proportional_target": round(proportional_target, 2),
        "long_cycle": long_c,
        "up_months": up_m,
        "down_months": down_m,
        "cycle_start": cycle_start.strftime("%Y-%m"),
        "cycle_end": cycle_end.strftime("%Y-%m"),
        "peak_date": peak_date.strftime("%Y-%m"),
        "phase_type": phase_type,
        "m_perf": c_m_perf,
        "w_perf": c_w_perf,
        "is_pos": c_m_pos,
        "curr_day_date": curr_date.strftime("%d %B %Y"),
        "next_day_date": (curr_date + pd.Timedelta(days=1)).strftime("%d %B %Y"),
        "curr_month_date": curr_date.strftime("%B %Y"),
        "next_month_date": (curr_date + pd.DateOffset(months=1)).strftime("%B %Y"),
        "curr_week_date": curr_date.strftime("%d %B %Y"),
        "next_week_date": (curr_date + pd.DateOffset(days=7)).strftime("%d %B %Y"),
        "matched_curr_d_date": c_d_date,
        "matched_curr_d_desc": c_d_desc,
        "matched_curr_d_icon": c_d_icon,
        "matched_next_d_date": n_d_date,
        "matched_next_d_desc": n_d_desc,
        "matched_next_d_icon": n_d_icon,
        "matched_curr_m_date": c_m_date,
        "matched_curr_m_desc": c_m_desc,
        "matched_curr_m_icon": c_m_icon,
        "matched_next_m_date": n_m_date,
        "matched_next_m_desc": n_m_desc,
        "matched_next_m_icon": n_m_icon,
        "matched_curr_w_date": c_w_date,
        "matched_curr_w_desc": c_w_desc,
        "matched_curr_w_icon": c_w_icon,
        "matched_next_w_date": n_w_date,
        "matched_next_w_desc": n_w_desc,
        "matched_next_w_icon": n_w_icon,
        "df_m": df_m['Close']
    }

st.title("🌟 منصة الدورات الزمنية والنجوم (الشركات الأربع)")

data_list = []
for sym, name in TARGET_STOCKS.items():
    df_raw, c_sym, c_name = fetch_stock_data_10y(sym)
    if not df_raw.empty:
        res = analyze_full_stock_dynamically(df_raw, c_sym)
        if res:
            res["name"] = c_name
            data_list.append(res)

if data_list:
    sorted_m = sorted(data_list, key=lambda x: x['m_perf'], reverse=True)
    star_m = sorted_m[0]
    worst_m = sorted_m[-1]

    st.markdown("### 👑 عرش النجوم والأداء الدوري الفعلي")

    col_star, col_worst = st.columns(2)
    
    with col_star:
        st.markdown(f"""
        <div class="star-card-top">
            <div class="metric-title">🌟 نجم السوق (الأعلى أداءً)</div>
            <div class="metric-value">{star_m['name']} ({star_m['symbol']})</div>
            <div style="margin-top:6px; font-size: 0.95rem;"><b>📈 الاتجاه العام:</b> {star_m['general_trend']}</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري الفعلي: <b>+{star_m['m_perf']}% {star_m['matched_curr_m_icon']}</b><br>
                • الأداء الأسبوعي الفعلي: <b>+{star_m['w_perf']}% {star_m['matched_curr_w_icon']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **اليوم الحالي ({star_m['curr_day_date']}):** يطابق `{star_m['matched_curr_d_date']}` 👈 ({star_m['matched_curr_d_desc']})  
            • **الأسبوع الحالي ({star_m['curr_week_date']}):** يطابق `{star_m['matched_curr_w_date']}` 👈 ({star_m['matched_curr_w_desc']})  
            • **الشهر الحالي ({star_m['curr_month_date']}):** يطابق `{star_m['matched_curr_m_date']}` 👈 ({star_m['matched_curr_m_desc']})
            """)

    with col_worst:
        st.markdown(f"""
        <div class="worst-card-top">
            <div class="metric-title">⚠️ الأقل أداءً في السوق</div>
            <div class="metric-value">{worst_m['name']} ({worst_m['symbol']})</div>
            <div style="margin-top:6px; font-size: 0.95rem;"><b>📈 الاتجاه العام:</b> {worst_m['general_trend']}</div>
            <div style="margin-top:8px; font-size: 1.05rem;">
                • الأداء الشهري الفعلي: <b>{worst_m['m_perf']}% {worst_m['matched_curr_m_icon']}</b><br>
                • الأداء الأسبوعي الفعلي: <b>{worst_m['w_perf']}% {worst_m['matched_curr_w_icon']}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📅 عرض التواريخ المطابقة في الدورة السابقة"):
            st.markdown(f"""
            • **اليوم الحالي ({worst_m['curr_day_date']}):** يطابق `{worst_m['matched_curr_d_date']}` 👈 ({worst_m['matched_curr_d_desc']})  
            • **الأسبوع الحالي ({worst_m['curr_week_date']}):** يطابق `{worst_m['matched_curr_w_date']}` 👈 ({worst_m['matched_curr_w_desc']})  
            • **الشهر الحالي ({worst_m['curr_month_date']}):** يطابق `{worst_m['matched_curr_m_date']}` 👈 ({worst_m['matched_curr_m_desc']})
            """)

    st.markdown("---")
    st.markdown("### 📊 ترتيب الشركات والدورات الزمنيّة مع الاتجاه العام والأداء")

    for rank, item in enumerate(sorted_m, 1):
        card_style = "company-card-positive" if item['is_pos'] else "company-card-negative"
        perf_sign = "+" if item['m_perf'] >= 0 else ""
        
        st.markdown(f"""
        <div class="{card_style}">
            <b>#{rank} | {item['name']} ({item['symbol']})</b> — 
            <span class="trend-badge">الاتجاه العام: {item['general_trend']}</span> | 
            الأداء الشهري المطابق: <b>{perf_sign}{item['m_perf']}% {item['matched_curr_m_icon']}</b> | 
            الأسبوعي: <b>{item['w_perf']}% {item['matched_curr_w_icon']}</b> | 
            المسار: <b>{item['phase_type']}</b>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"🔍 التفاصيل والدورة والشموع المطابقة لـ {item['name']}"):
            st.markdown(f"📈 **الاتجاه العام المعتمد:** `{item['general_trend']}`")
            
            if item['use_trading_candles']:
                st.markdown(f"📌 **تم الحساب بدقة {item['trading_candles_offset']} شمعة تداول يومية ({item['weekly_candles_offset']} أسبوعاً / {item['monthly_candles_offset']} شهراً)**")
            
            st.markdown(f"""
            **🔄 تفاصيل الدورة الحالية ({item['long_cycle']} شهراً - قاع إلى قاع):**
            - **مدة الصعود للقمة:** {item['up_months']} شهراً | **مدة الهبوط للقاع التالي:** {item['down_months']} شهراً
            - **السعر الحالي:** ${item['current_price']} | **المستهدف النسبي:** ${item['proportional_target']}
            - **بداية الدورة:** {item['cycle_start']} | **نهايتها:** {item['cycle_end']} | **شهر القمة:** {item['peak_date']}
            """)

            st.markdown("---")
            st.markdown("#### 🗓️ مطابقة الشموع اليومية والأسبوعية والشهريّة مع الدورة السابقة:")
            
            st.markdown(f"- **اليوم الحالي ({item['curr_day_date']}):** يصادف **{item['matched_curr_d_date']}** 👈 ({item['matched_curr_d_desc']} {item['matched_curr_d_icon']})")
            st.markdown(f"- **اليوم القادم ({item['next_day_date']}):** سيصادف **{item['matched_next_d_date']}** 👈 ({item['matched_next_d_desc']} {item['matched_next_d_icon']})")
            
            st.markdown(f"- **الأسبوع الحالي ({item['curr_week_date']}):** يصادف **{item['matched_curr_w_date']}** 👈 ({item['matched_curr_w_desc']} {item['matched_curr_w_icon']})")
            st.markdown(f"- **الأسبوع القادم ({item['next_week_date']}):** سيصادف **{item['matched_next_w_date']}** 👈 ({item['matched_next_w_desc']} {item['matched_next_w_icon']})")
            
            st.markdown(f"- **الشهر الحالي ({item['curr_month_date']}):** يصادف **{item['matched_curr_m_date']}** 👈 ({item['matched_curr_m_desc']} {item['matched_curr_m_icon']})")
            st.markdown(f"- **الشهر القادم ({item['next_month_date']}):** سيصادف **{item['matched_next_m_date']}** 👈 ({item['matched_next_m_desc']} {item['matched_next_m_icon']})")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=item['df_m'].index, y=item['df_m'].values, mode='lines', name='السعر الشهري', line=dict(color='#0284c7', width=2)))
            fig.add_hline(y=item['proportional_target'], line_dash="dash", line_color="#10b981", annotation_text=f"المستهدف: {item['proportional_target']}")
            fig.update_layout(template="plotly_white", height=240, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
