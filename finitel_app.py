"""
FinIntel GmbH – KI-gestützte Kapitalanlageberatung
User-Centered Redesign · Demo-Prototyp (Streamlit) für eine Universitätspräsentation.

Die Oberfläche ist um die Arbeitsabläufe der Nutzer herum gebaut (aufgabenorientiert)
statt um technische Features:

    🏠 Cockpit            – Tagesstart, Marktlage, nächste sinnvolle Aktion
    🧭 Kunde beraten       – geführter 3-Schritt-Wizard (Profil → KI-Vorschlag → Freigabe)
    📡 Portfolio überwachen – Markt/Krise & ESG (Tabs)
    ✅ Freigabe & Compliance – eigenständiger MiFID-II-Check

Zusätzlich ein Ansichts-Umschalter (👔 Berater / 🙋 Kunde), der Sprache und Detailtiefe
an die jeweilige Person anpasst (Hybrid / User-Centered).

WICHTIG: Alle Daten sind Dummy-/Demodaten. Keine externen APIs, kein echtes ML.
Start:  streamlit run finitel_app.py
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# Reproduzierbarkeit der Dummy-Daten & Farben
# --------------------------------------------------------------------------- #
np.random.seed(42)

NAVY = "#1E2761"
BLUE = "#4A90D9"
NAVY_PALETTE = ["#1E2761", "#3A4A99", "#4A90D9", "#9BC1E8"]

# --------------------------------------------------------------------------- #
# Seitenkonfiguration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="FinIntel – KI-Kapitalanlageberatung",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Session-State-Initialisierung
# --------------------------------------------------------------------------- #
st.session_state.setdefault("mode", "👔 Berater")
st.session_state.setdefault("nav_page", "🏠 Cockpit")
st.session_state.setdefault("wizard_step", 1)
st.session_state.setdefault("advisory_done", False)

# Persistentes Kundenprofil, getrennt von den Widget-Keys (w_*) aus Schritt 1.
# Streamlit entfernt einen Widget-Key automatisch aus session_state, sobald das
# zugehörige Widget in einem Rerun nicht gerendert wird (z.B. weil man auf
# Schritt 2/3 ist). Damit gingen Name/Betrag/Horizont/Risiko/Präferenzen beim
# Verlassen von Schritt 1 verloren. Das "profile"-Dict ist kein Widget-Key und
# bleibt deshalb über den ganzen Wizard-Ablauf hinweg erhalten.
st.session_state.setdefault("profile", {
    "name": "Dr. Maria Schmidt",
    "amount": 250_000,
    "horizon": "5–10 Jahre",
    "risk": "Moderat (Klasse 3)",
    "preferences": ["🌱 ESG / Nachhaltigkeit"],
})

NAV_OPTIONS = [
    "🏠 Cockpit",
    "🧭 Kunde beraten",
    "📡 Portfolio überwachen",
    "✅ Freigabe & Compliance",
]

# --------------------------------------------------------------------------- #
# Custom CSS (Navy professionell, aufgeräumt)
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 4rem; padding-bottom: 2.5rem; max-width: 1280px; }}
    html, body, [class*="css"] {{ font-size: 16px; }}

    /* Lesbarkeit erzwingen (Fallback, falls .streamlit/config.toml nicht greift):
       helle Flächen + dunkle Standardschrift. Steht VOR den Klassen mit weißer
       Schrift, damit Hero/Banner/Buttons/Badges (weiß auf Farbe) gewinnen. */
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"] {{ background-color:#ffffff; }}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, label,
    [data-testid="stWidgetLabel"] p {{ color:#262730; }}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] p {{ color:#262730; }}

    /* ---------- Hero-Begrüßungsband ---------- */
    .fi-hero {{
        background: linear-gradient(120deg, {NAVY} 0%, #2b3a86 55%, {BLUE} 130%);
        color: #ffffff;
        border-radius: 16px;
        padding: 26px 30px;
        margin-bottom: 1.4rem;
        box-shadow: 0 6px 24px rgba(30,39,97,0.18);
    }}
    .fi-hero h1 {{ font-size: 1.9rem; font-weight: 800; line-height: 1.25; margin: 0 0 4px 0; color:#fff; }}
    .fi-hero p  {{ font-size: 1.02rem; margin: 0; opacity: 0.92; }}
    .fi-hero .fi-eyebrow {{
        text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.72rem;
        font-weight: 700; opacity: 0.8; margin-bottom: 6px;
    }}

    /* ---------- Seiten-Header ---------- */
    .fi-title    {{ color:{NAVY}; font-size:1.7rem; font-weight:800; line-height:1.35; padding-top:0.1rem; margin-bottom:2px; }}
    .fi-subtitle {{ color:#5a6072; font-size:1.0rem; margin:0 0 1.2rem 0; }}
    .fi-section  {{ color:{NAVY}; font-size:1.15rem; font-weight:700; margin:0.4rem 0 0.6rem 0; }}

    /* ---------- Cards ---------- */
    .fi-card {{
        background:#f8f9fc; border:1px solid #e7ebf5; border-radius:14px;
        padding:20px 22px; margin-bottom:1rem;
        box-shadow:0 2px 12px rgba(30,39,97,0.06);
    }}
    .fi-card h4 {{ color:{NAVY}; margin-top:0; }}

    /* ---------- Next-Best-Action Callout ---------- */
    .fi-nba {{
        display:flex; align-items:center; gap:16px;
        background:#eef3fd; border:1px solid #cfe0fa; border-left:6px solid {BLUE};
        border-radius:14px; padding:18px 22px; margin-bottom:1.2rem;
    }}
    .fi-nba .fi-nba-icon {{ font-size:2.0rem; }}
    .fi-nba .fi-nba-title {{ font-weight:800; color:{NAVY}; font-size:1.05rem; }}
    .fi-nba .fi-nba-text  {{ color:#48506a; font-size:0.95rem; }}

    /* ---------- Banner ---------- */
    .fi-banner {{
        background:linear-gradient(90deg,{NAVY} 0%,{BLUE} 100%); color:#fff;
        border-radius:12px; padding:14px 20px; font-size:0.97rem; margin-bottom:1rem;
    }}
    .fi-banner-soft {{
        background:#eef3fd; border:1px solid #cfe0fa; color:{NAVY};
        border-radius:12px; padding:14px 20px; font-size:0.97rem; margin-bottom:1rem;
    }}

    /* ---------- Erfolg / Blockiert ---------- */
    .fi-success {{ background:#e6f6ec; border-left:6px solid #1f9d55; color:#14633a;
                   border-radius:10px; padding:14px 18px; font-weight:600; margin-top:0.8rem; }}
    .fi-blocked {{ background:#fdecec; border-left:6px solid #d64545; color:#8a1f1f;
                   border-radius:10px; padding:14px 18px; font-weight:600; margin-top:0.8rem; }}

    /* ---------- Badges ---------- */
    .badge-green,.badge-red,.badge-orange,.badge-blue {{
        display:inline-block; padding:5px 14px; border-radius:999px;
        font-size:0.85rem; font-weight:700; color:#fff;
    }}
    .badge-green {{ background:#1f9d55; }}
    .badge-red {{ background:#d64545; }}
    .badge-orange {{ background:#e08e0b; }}
    .badge-blue {{ background:{BLUE}; }}

    /* ---------- KPI-Metriken ---------- */
    div[data-testid="stMetric"] {{
        background:#f8f9fc; border:1px solid #e7ebf5; border-radius:14px;
        padding:16px 18px; box-shadow:0 2px 8px rgba(30,39,97,0.06);
    }}
    div[data-testid="stMetricValue"] {{ font-size:1.7rem; color:{NAVY}; font-weight:800; }}
    div[data-testid="stMetricLabel"] {{ font-weight:600; color:#5a6072; }}

    /* ---------- Step-Indicator (Wizard) ---------- */
    .fi-steps {{ display:flex; align-items:flex-start; justify-content:space-between;
                 margin:0.2rem 0 1.4rem 0; }}
    .fi-step {{ display:flex; flex-direction:column; align-items:center; width:120px; }}
    .fi-step .circle {{
        width:42px; height:42px; border-radius:50%; display:flex; align-items:center;
        justify-content:center; font-weight:800; font-size:1.05rem;
        background:#e3e8f4; color:#9aa3bd; border:2px solid #e3e8f4;
    }}
    .fi-step .lbl {{ margin-top:8px; font-size:0.85rem; color:#9aa3bd; font-weight:600;
                     text-align:center; }}
    .fi-step.active .circle {{ background:{NAVY}; color:#fff; border-color:{NAVY};
                               box-shadow:0 0 0 4px rgba(30,39,97,0.15); }}
    .fi-step.active .lbl {{ color:{NAVY}; }}
    .fi-step.done .circle {{ background:{BLUE}; color:#fff; border-color:{BLUE}; }}
    .fi-step.done .lbl {{ color:{BLUE}; }}
    .fi-line {{ flex:1; height:3px; background:#e3e8f4; margin:21px 6px 0 6px; border-radius:2px; }}
    .fi-line.done {{ background:{BLUE}; }}

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {{ font-weight:700; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:{NAVY}; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{NAVY}; }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{ background:#eef1f8; }}
    .fi-logo {{ color:{NAVY}; font-size:1.45rem; font-weight:800; line-height:1.1; }}
    .fi-logo-sub {{ color:{BLUE}; font-size:0.9rem; font-weight:600; margin-bottom:0.4rem; }}
    .fi-side-info {{ font-size:0.85rem; color:#404a66; line-height:1.7; }}
    .fi-footer {{ font-size:0.78rem; color:#8a92a8; margin-top:1rem; }}

    /* ---------- Primär-Buttons ---------- */
    div.stButton > button[kind="primary"] {{
        background:{NAVY}; border:none; color:#fff; font-weight:700;
        border-radius:9px; padding:0.62rem 1rem; width:100%;
    }}
    div.stButton > button[kind="primary"]:hover {{ background:{BLUE}; color:#fff; }}
    div.stButton > button[kind="secondary"] {{
        border-radius:9px; font-weight:600; width:100%;
    }}

    /* WICHTIG: Weiße Schrift auf farbigen Flächen muss den dunklen Text-Fallback
       (oben) schlagen – sonst dunkle Schrift auf Navy = unlesbar. Daher !important
       auf genau den Elementen, die auf farbigem Grund stehen. */
    .fi-hero, .fi-hero *,
    .fi-banner, .fi-banner *,
    .badge-green, .badge-red, .badge-orange, .badge-blue,
    .fi-step.active .circle, .fi-step.done .circle,
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] * {{ color:#ffffff !important; }}
    /* Sekundär-Buttons (heller Grund) -> dunkle, lesbare Schrift */
    div.stButton > button[kind="secondary"],
    div.stButton > button[kind="secondary"] * {{ color:{NAVY} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def is_advisor() -> bool:
    """True im Berater-Modus, False in der Kundensicht."""
    return st.session_state.get("mode", "👔 Berater").startswith("👔")


def t(advisor_text: str, client_text: str) -> str:
    """Wählt Text je nach aktiver Ansicht (User-Centered)."""
    return advisor_text if is_advisor() else client_text


def header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="fi-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fi-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def hero(eyebrow: str, title: str, text: str) -> None:
    st.markdown(
        f'<div class="fi-hero"><div class="fi-eyebrow">{eyebrow}</div>'
        f'<h1>{title}</h1><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def style_plotly(fig: go.Figure, height: int = 360) -> go.Figure:
    # Ohne gesetzten Layout-Titel rendert Plotly sonst "undefined" (z.B. beim Gauge).
    if fig.layout.title.text is None:
        fig.update_layout(title_text="")
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=60, b=70),
        font=dict(color=NAVY),
        title_font=dict(color=NAVY, size=16),
        # Legende unten, damit sie den oben-links platzierten Titel nicht überlappt.
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="left", x=0),
    )
    return fig


def status_badge(text: str) -> str:
    if "KRITISCH" in text:
        return "background-color:#d64545;color:white;font-weight:700;"
    if "WARNUNG" in text:
        return "background-color:#e08e0b;color:white;font-weight:700;"
    return "background-color:#1f9d55;color:white;font-weight:700;"


def step_indicator(current: int) -> None:
    steps = [("1", "Profil"), ("2", "KI-Vorschlag"), ("3", "Freigabe")]
    html = '<div class="fi-steps">'
    for i, (num, label) in enumerate(steps, start=1):
        state = "done" if i < current else ("active" if i == current else "")
        html += (f'<div class="fi-step {state}"><div class="circle">{num}</div>'
                 f'<div class="lbl">{label}</div></div>')
        if i < len(steps):
            html += f'<div class="fi-line {"done" if i < current else ""}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def goto(page: str, wizard_step: int | None = None) -> None:
    """Navigations-Wunsch hinterlegen (wird vor dem Sidebar-Widget angewandt)."""
    st.session_state["_goto"] = page
    if wizard_step is not None:
        st.session_state["wizard_step"] = wizard_step
    st.rerun()


# --------------------------------------------------------------------------- #
# Daten-Konstanten (wiederverwendet aus der Erstversion)
# --------------------------------------------------------------------------- #
RISK_ALLOC = {
    "Konservativ (Klasse 1-2)": {"Aktien": 20, "Anleihen": 55, "ETFs": 15, "Cash": 10},
    "Moderat (Klasse 3)":       {"Aktien": 40, "Anleihen": 35, "ETFs": 20, "Cash": 5},
    "Wachstumsorientiert (Klasse 4)": {"Aktien": 55, "Anleihen": 20, "ETFs": 22, "Cash": 3},
    "Aggressiv (Klasse 5)":     {"Aktien": 70, "Anleihen": 8, "ETFs": 20, "Cash": 2},
}
RISK_TO_CLASS = {
    "Konservativ (Klasse 1-2)": 2,
    "Moderat (Klasse 3)": 3,
    "Wachstumsorientiert (Klasse 4)": 4,
    "Aggressiv (Klasse 5)": 5,
}

# Pro Anlageklasse ein Standard- und ein ESG-Produkt, damit der Vorschlag in
# Schritt 2 tatsächlich auf Risikoklasse, Betrag und ESG-Präferenz reagiert
# (Name/ISIN/Rendite, Gewichtung & Euro-Betrag), statt eine statische Demo-Tabelle zu zeigen.
PRODUCT_CATALOG = {
    "Aktien": {
        "standard": ("iShares Core MSCI World ETF", "IE00B4L5Y983", "7,2 % p.a.", 4),
        "esg": ("iShares MSCI World SRI UCITS ETF", "IE00BYX5NX33", "6,9 % p.a.", 4),
    },
    "Anleihen": {
        "standard": ("DWS Zinseinkommen", "DE0008474560", "3,1 % p.a.", 2),
        "esg": ("DWS Invest ESG Euro Bonds", "LU0300357554", "2,8 % p.a.", 2),
    },
    "ETFs": {
        "standard": ("Xtrackers DAX UCITS ETF", "LU0274211480", "6,8 % p.a.", 4),
        "esg": ("Xtrackers MSCI Europe ESG UCITS ETF", "LU0292096186", "6,3 % p.a.", 3),
    },
    "Cash": {
        "standard": ("Cash / Tagesgeld", "–", "2,5 % p.a.", 1),
        "esg": ("Cash / Tagesgeld (Green Deposit)", "–", "2,3 % p.a.", 1),
    },
}

# Anzeigename je Anlageklasse für die Produkttabelle. "Aktien" und "ETFs" sind in
# RISK_ALLOC zwei separate Risikoklassen-Buckets, beide aber per ETF umgesetzt –
# ohne diese Differenzierung sah die blosse Bezeichnung "Aktien" neben einem
# Produktnamen mit "ETF" wie ein Widerspruch aus.
ASSET_DISPLAY = {
    "Aktien": "Aktien-ETF (Welt)",
    "Anleihen": "Anleihen-Fonds",
    "ETFs": "Themen-/Index-ETF",
    "Cash": "Cash",
}

# Auswahl an Ausschluss-/Nachhaltigkeitspräferenzen für das Multiselect in Schritt 1.
EXCLUSION_OPTIONS = [
    "🌱 ESG / Nachhaltigkeit",
    "🚫 Keine Rüstungsindustrie",
    "🚫 Keine Pharma-Industrie",
    "🚫 Keine fossile Brennstoffe",
    "🚫 Keine Tabakindustrie",
    "🚫 Keine Glücksspielindustrie",
]

# Einzelaktien-Satellit: wird nur bei höherer Risikobereitschaft beigemischt und
# zehrt einen Teil der "Aktien"-Gewichtung auf (siehe recommended_products()).
SATELLITE_STOCKS = {
    "Wachstumsorientiert (Klasse 4)": [
        ("NVIDIA Corp.", "US67066G1040", "18,4 % p.a.", 5),
    ],
    "Aggressiv (Klasse 5)": [
        ("NVIDIA Corp.", "US67066G1040", "18,4 % p.a.", 5),
        ("SpaceX (Pre-IPO, Demo)", "–", "n/a (illiquide)", 5),
    ],
}

# ESG-Scores je Produktname – einzige Quelle für Cockpit, Portfolio überwachen
# und den ESG-Filter, damit überall dieselben Positionen mit denselben Scores
# auftauchen, statt unabhängiger Demo-Positionen (Siemens, Allianz SE, ...).
ESG_SCORES = {
    "iShares Core MSCI World ETF": 74,
    "iShares MSCI World SRI UCITS ETF": 91,
    "DWS Zinseinkommen": 58,
    "DWS Invest ESG Euro Bonds": 86,
    "Xtrackers DAX UCITS ETF": 51,
    "Xtrackers MSCI Europe ESG UCITS ETF": 88,
    "Cash / Tagesgeld": 70,
    "Cash / Tagesgeld (Green Deposit)": 95,
    "NVIDIA Corp.": 64,
    "SpaceX (Pre-IPO, Demo)": 50,
}

# Produktname -> Anlageklassen-Key (für den ESG-Rebalancing-Vorschlag: damit lässt
# sich zu einem gehaltenen Standardprodukt die passende ESG-Alternative aus
# PRODUCT_CATALOG nachschlagen).
PRODUCT_TO_ASSET = {
    name: asset
    for asset, variants in PRODUCT_CATALOG.items()
    for name, _isin, _ret, _risk_class in variants.values()
}

# MiFID-II-Produktliste für den Compliance-Check – aus PRODUCT_CATALOG und
# SATELLITE_STOCKS abgeleitet, damit dort exakt dieselben Produkte/Risikoklassen
# erscheinen wie im KI-Vorschlag bei "Kunde beraten".
COMPLIANCE_PRODUCTS = {
    f"{name} (Klasse {risk_class})": risk_class
    for variants in PRODUCT_CATALOG.values()
    for name, _isin, _ret, risk_class in variants.values()
}
for _stocks in SATELLITE_STOCKS.values():
    for _name, _isin, _ret, _risk_class in _stocks:
        COMPLIANCE_PRODUCTS.setdefault(f"{_name} (Klasse {_risk_class})", _risk_class)


def portfolio_performance_fig() -> go.Figure:
    months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    # Beide Renditen strikt positiv; Benchmark als kleinerer Bruchteil der Portfolio-
    # Rendite -> beide steigen über 100, Benchmark bleibt durchgehend unter dem Portfolio.
    port_ret = np.abs(np.random.normal(1.3, 0.6, 12))
    bench_ret = port_ret * np.random.uniform(0.35, 0.55, 12)
    portfolio = 100 * np.cumprod(1 + port_ret / 100)
    benchmark = 100 * np.cumprod(1 + bench_ret / 100)
    portfolio[0], benchmark[0] = 100, 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=portfolio, name="Portfolio",
                             line=dict(color=BLUE, width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=benchmark, name="Benchmark",
                             line=dict(color="#888", width=2, dash="dash"), mode="lines"))
    fig.update_layout(title="Wertentwicklung vs. Vergleichsindex (Start = 100)")
    fig.update_yaxes(title="Index")
    return fig


def recommended_products(alloc: dict, amount: int, esg: bool, risk: str) -> pd.DataFrame:
    """Produktliste aus der Allokation ableiten, damit Risikoklasse, Betrag,
    ESG-Präferenz und (bei höherer Risikobereitschaft) Einzelaktien-Satelliten
    aus Schritt 1 sich tatsächlich im Vorschlag widerspiegeln."""
    variant = "esg" if esg else "standard"
    satellites = SATELLITE_STOCKS.get(risk, [])
    # Einzelaktien zehren einen Teil der Fonds-Aktienquote auf (max. 15 Punkte),
    # statt die Gesamtallokation zu verändern.
    aktien_carve = min(alloc.get("Aktien", 0), 15) if satellites else 0

    # "Anlageklasse" macht die Zuordnung zur Pie-Chart-Kategorie explizit, damit
    # Tabelle und Allokation auch bei ähnlich klingenden Produktnamen (mehrere
    # ETFs in unterschiedlichen Klassen) eindeutig zusammenpassen.
    rows = []
    for asset, pct in alloc.items():
        weight = pct - aktien_carve if asset == "Aktien" else pct
        if weight <= 0:
            continue
        name, isin, ret, risk_class = PRODUCT_CATALOG[asset][variant]
        betrag = f"{amount * weight / 100:,.0f} €".replace(",", ".")
        rows.append([ASSET_DISPLAY[asset], name, isin, f"{weight} %", betrag, ret, risk_class])

    if aktien_carve and satellites:
        # Ganzzahlige Gewichte, die exakt aktien_carve aufsummieren (Rest aufs letzte Element).
        base = aktien_carve // len(satellites)
        weights = [base] * len(satellites)
        weights[-1] += aktien_carve - base * len(satellites)
        for (name, isin, ret, risk_class), weight in zip(satellites, weights):
            betrag = f"{amount * weight / 100:,.0f} €".replace(",", ".")
            rows.append(["Aktien (Einzeltitel)", name, isin, f"{weight} %", betrag, ret, risk_class])

    return pd.DataFrame(
        rows,
        columns=["Anlageklasse", "Produkt", "ISIN", "Gewichtung", "Betrag", "Erw. Rendite", "Risikoklasse"],
    )


def current_holdings() -> pd.DataFrame:
    """Positionen des in Schritt 1 erfassten Kunden – von Cockpit, Portfolio
    überwachen und Compliance gemeinsam genutzt, damit überall dieselben
    Produkte (statt unabhängiger Demo-Listen) angezeigt werden."""
    profile = st.session_state["profile"]
    risk = profile["risk"]
    esg = "🌱 ESG / Nachhaltigkeit" in profile["preferences"]
    return recommended_products(RISK_ALLOC[risk], profile["amount"], esg, risk)


def portfolio_esg_score(holdings: pd.DataFrame) -> int:
    weights = holdings["Gewichtung"].str.rstrip(" %").astype(float)
    scores = holdings["Produkt"].map(ESG_SCORES).fillna(60)
    return round((weights * scores).sum() / weights.sum())


def allocation_pie(alloc: dict, title: str, hole: float = 0.0) -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=list(alloc.keys()), values=list(alloc.values()), hole=hole,
        marker=dict(colors=NAVY_PALETTE), textinfo="label+percent")])
    fig.update_layout(title=title)
    return fig


# --------------------------------------------------------------------------- #
# Bereich 1: Cockpit
# --------------------------------------------------------------------------- #
def page_cockpit() -> None:
    profile = st.session_state["profile"]
    name = profile["name"]
    risk = profile["risk"]
    cust_class = RISK_TO_CLASS[risk]
    risk_label = risk.split(" (")[0]
    holdings = current_holdings()
    esg_score = portfolio_esg_score(holdings)
    worst = holdings.assign(ESG=holdings["Produkt"].map(ESG_SCORES).fillna(60)).pipe(
        lambda df: df.loc[df["ESG"].idxmin()]
    )
    esg_alert = worst["ESG"] < 60
    betrag_str = f"{profile['amount']:,.0f} €".replace(",", ".")

    today = datetime.now().strftime("%A, %d.%m.%Y")
    if is_advisor():
        hero("FinIntel Cockpit · Berater-Ansicht",
             "Guten Tag 👋 Ihr Beratungs-Cockpit",
             f"{today} — Marktlage, Warnungen und Ihre nächste sinnvolle Aktion auf einen Blick.")
    else:
        hero("Mein FinIntel · Kundenansicht",
             f"Willkommen, {name} 👋",
             f"{today} — So steht es heute um Ihre Geldanlage. Alles verständlich erklärt.")

    # Next-Best-Action
    nba_title = t("Nächster Schritt: Neue Kundenanfrage bearbeiten",
                  "Empfehlung: Lassen Sie sich einen Anlagevorschlag erstellen")
    nba_text = t(f"Für {name} liegt eine vollständige Anfrage vor – starten Sie die geführte Beratung.",
                 "In wenigen Schritten erhalten Sie einen persönlichen, geprüften Vorschlag.")
    c_icon, c_txt, c_btn = st.columns([0.07, 0.73, 0.20])
    with c_icon:
        st.markdown('<div style="font-size:2.4rem;text-align:center;">🧭</div>',
                    unsafe_allow_html=True)
    with c_txt:
        st.markdown(f'<div class="fi-nba-title">{nba_title}</div>'
                    f'<div class="fi-nba-text">{nba_text}</div>', unsafe_allow_html=True)
    with c_btn:
        st.write("")
        if st.button(t("Beratung starten →", "Vorschlag erhalten →"),
                     type="primary", key="nba_btn"):
            goto("🧭 Kunde beraten", wizard_step=1)

    st.markdown(f'<div class="fi-section">{t("Marktlage & Kennzahlen", "Mein Überblick")}</div>',
                unsafe_allow_html=True)

    # KPI-Zeile – Betrag, Risikoklasse & ESG-Score stammen aus dem in
    # "Kunde beraten" erfassten Profil, statt aus unabhängigen Demo-Werten.
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Portfolio-Wert", "Mein Vermögen"), betrag_str, "+3,2 % diese Woche")
    k2.metric(t("YTD-Rendite", "Ertrag dieses Jahr"), "+7,3 %",
              t("Benchmark: +5,1 %", "Markt: +5,1 %"))
    k3.metric(t("Risikoscore", "Risiko-Stufe"), risk_label, f"Klasse {cust_class} / 5", delta_color="off")
    k4.metric("ESG-Score", f"{esg_score} / 100", "+4 " + t("seit letztem Monat", "Punkte"))

    st.write("")

    # Charts
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(style_plotly(portfolio_performance_fig()), width="stretch")
    with c2:
        st.plotly_chart(style_plotly(allocation_pie(RISK_ALLOC[risk],
                                                     t("Asset-Allokation", "Meine Aufteilung"))),
                        width="stretch")

    # Alerts – die ESG-Warnung bezieht sich auf die tatsächlich schwächste
    # Position aus den aktuellen Holdings, nicht auf eine unabhängige Demo-Aktie.
    st.markdown(f'<div class="fi-section">{t("Aktive Warnungen", "Wichtige Hinweise")}</div>',
                unsafe_allow_html=True)
    if is_advisor():
        st.error("🔴 **KRITISCH** — DAX -5,2 % in 24h · Krisenwarnung für 12 Portfolios ausgelöst")
        st.warning("🟠 **WARNUNG** — Zinskurven-Inversion erkannt · LSTM-Konfidenz 82 %")
        if esg_alert:
            st.info(f"🔵 **INFO** — ESG-Score {worst['Produkt']} {int(worst['ESG'])}/100 · Umschichtung prüfen")
        else:
            st.info("🔵 **INFO** — Keine ESG-Auffälligkeiten in der aktuellen Allokation")
    else:
        st.warning("🟠 Die Märkte schwanken aktuell stärker als üblich – Ihr Portfolio ist breit gestreut und gut aufgestellt.")
        if esg_alert:
            st.info(f"🔵 Eine Position ({worst['Produkt']}) erfüllt Ihre Nachhaltigkeits-Kriterien nicht mehr ganz – "
                    "Ihr Berater hat einen Tausch vorbereitet.")
        else:
            st.info("🔵 Alle Positionen erfüllen aktuell Ihre Nachhaltigkeits-Kriterien.")

    # ECA-Log nur im Berater-Modus
    if is_advisor():
        with st.expander("⚡ Systemereignisse (ECA-Ereignislog)"):
            esg_event = (f"{worst['Produkt']} ESG {int(worst['ESG'])} Punkte" if esg_alert
                         else "Keine ESG-Auffälligkeiten")
            log = pd.DataFrame([
                ["09.06.2026 08:23", "Kursrückgang", "DAX -5,2 % in 24h",
                 "🔴 KRITISCH", "Krisenwarnung + Berater-Alert"],
                ["09.06.2026 07:15", "ESG-Score Änderung", esg_event,
                 "🟠 WARNUNG" if esg_alert else "🟢 OK",
                 "Umschichtungsvorschlag generiert" if esg_alert else "Keine Aktion nötig"],
                ["08.06.2026 16:44", "Makro-Indikator", "Zinskurven-Inversion",
                 "🟠 WARNUNG", "LSTM-Frühwarnung ausgelöst"],
                ["08.06.2026 11:02", "Neue Kundenanfrage", f"Profil {name} vollständig",
                 "🟢 OK", "ML-Inference abgeschlossen"],
                ["07.06.2026 09:30", "Compliance-Check", "Portfolio-Rebalancing",
                 "🟢 OK", "MiFID-II Freigabe erteilt"],
            ], columns=["Zeitstempel", "Ereignistyp", "Auslöser-Wert", "Status", "Aktion"])
            st.dataframe(log.style.map(status_badge, subset=["Status"]),
                         width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Bereich 2: Kunde beraten (Wizard)
# --------------------------------------------------------------------------- #
def page_wizard() -> None:
    header(t("Kunde beraten", "Ihr persönlicher Anlagevorschlag"),
           t("Geführter Ablauf: Profil → KI-Vorschlag → MiFID-II-Freigabe",
             "In drei einfachen Schritten zu Ihrer geprüften Empfehlung"))

    step = st.session_state["wizard_step"]
    step_indicator(step)

    if step == 1:
        _wizard_step1()
    elif step == 2:
        _wizard_step2()
    else:
        _wizard_step3()


def _wizard_step1() -> None:
    st.markdown(f'<div class="fi-section">① {t("Kundenprofil erfassen", "Ihre Angaben")}</div>',
                unsafe_allow_html=True)

    profile = st.session_state["profile"]
    # Widget-Keys aus dem persistenten Profil "wiederbeleben": Streamlit hat sie
    # beim Verlassen von Schritt 1 aus session_state entfernt (siehe Hinweis bei
    # der Profil-Initialisierung oben), daher hier neu aus profile befüllen.
    st.session_state.setdefault("w_name", profile["name"])
    st.session_state.setdefault("w_amount", profile["amount"])
    st.session_state.setdefault("w_horizon", profile["horizon"])
    st.session_state.setdefault("w_risk", profile["risk"])
    st.session_state.setdefault("w_prefs", profile["preferences"])

    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Kundenname", key="w_name",
                      help="Name der zu beratenden Person.")
        st.slider("Anlagebetrag (€)", 10_000, 1_000_000, step=5000,
                  format="%d €", key="w_amount",
                  help="Wie viel soll insgesamt angelegt werden?")
    with c2:
        st.selectbox("Anlagehorizont",
                     ["1–3 Jahre", "3–5 Jahre", "5–10 Jahre", "> 10 Jahre"],
                     key="w_horizon",
                     help="Wie lange kann das Geld investiert bleiben?")
        st.radio("Risikobereitschaft", list(RISK_ALLOC.keys()), key="w_risk",
                 help=t("Bestimmt die MiFID-II-Risikoklasse des Kunden.",
                        "Wie stark dürfen Ihre Anlagen schwanken?"))
    st.multiselect(
        t("Anlagepräferenzen / Ausschlüsse", "Was ist Ihnen wichtig?"),
        EXCLUSION_OPTIONS, key="w_prefs",
        help=t("Schliesst Branchen aus dem Vorschlag aus bzw. priorisiert ESG-Produkte.",
               "Wählen Sie aus, was Ihnen bei der Geldanlage wichtig ist."),
    )

    # Sofort ins persistente Profil zurückschreiben, damit der aktuelle Stand
    # auch dann erhalten bleibt, wenn die Widgets im nächsten Rerun (Schritt 2/3)
    # nicht mehr existieren.
    profile["name"] = st.session_state["w_name"]
    profile["amount"] = st.session_state["w_amount"]
    profile["horizon"] = st.session_state["w_horizon"]
    profile["risk"] = st.session_state["w_risk"]
    profile["preferences"] = st.session_state["w_prefs"]

    st.write("")
    _, right = st.columns([0.7, 0.3])
    with right:
        if st.button(t("Weiter → KI-Vorschlag", "Weiter →"), type="primary", key="s1_next"):
            st.session_state["advisory_done"] = True
            st.session_state["wizard_step"] = 2
            st.rerun()


def _wizard_step2() -> None:
    profile = st.session_state["profile"]
    risk = profile["risk"]
    name = profile["name"]
    amount = profile["amount"]
    horizon = profile["horizon"]
    preferences = profile["preferences"]
    esg = "🌱 ESG / Nachhaltigkeit" in preferences
    exclusions = [p for p in preferences if p != "🌱 ESG / Nachhaltigkeit"]

    st.markdown(f'<div class="fi-section">② {t("KI-Anlagevorschlag", "Ihr Vorschlag")}</div>',
                unsafe_allow_html=True)

    if is_advisor():
        st.markdown('<span class="badge-green">KONFIDENZ: 87 % · ML-Modell: XGBoost v2.3</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-blue">Persönlich abgestimmt für {name}</span>',
                    unsafe_allow_html=True)
    st.write("")

    betrag_str = f"{amount:,.0f} €".replace(",", ".")
    caption = f"Anlagebetrag: {betrag_str} · Horizont: {horizon}"
    if esg:
        caption += " · ESG-Filter aktiv"
    if exclusions:
        caption += " · Ausschlüsse: " + ", ".join(e.split(" ", 1)[1] for e in exclusions)
    st.caption(caption)

    c1, c2 = st.columns([2, 3])
    with c1:
        alloc = RISK_ALLOC[risk]
        st.plotly_chart(
            style_plotly(allocation_pie(alloc, t("Empfohlene Allokation", "So legen wir an"),
                                        hole=0.55), height=320),
            width="stretch")
    with c2:
        title = t("##### Konkrete Produktempfehlungen", "##### Das ist enthalten")
        if risk in SATELLITE_STOCKS:
            title += " 📈 " + t("inkl. Einzelaktien-Satellit", "inkl. Einzelaktien")
        st.markdown(title)
        products = recommended_products(alloc, amount, esg, risk)
        if not is_advisor():
            products = products[["Anlageklasse", "Produkt", "Gewichtung", "Betrag", "Erw. Rendite"]]
        st.dataframe(products, width="stretch", hide_index=True)

    if not is_advisor():
        with st.expander("ℹ️ Einfach erklärt: Was bedeutet das?"):
            st.write("Ihr Geld wird auf mehrere Anlagen verteilt (Streuung). "
                     "Das senkt das Risiko, weil nicht alles von einer einzigen Entwicklung abhängt. "
                     "Die Mischung passt zu Ihrer gewählten Risikobereitschaft.")

    st.write("")
    left, _, right = st.columns([0.25, 0.45, 0.30])
    with left:
        if st.button("← Zurück", key="s2_back"):
            st.session_state["wizard_step"] = 1
            st.rerun()
    with right:
        if st.button(t("Weiter → Freigabe", "Weiter →"), type="primary", key="s2_next"):
            st.session_state["wizard_step"] = 3
            st.rerun()


def _wizard_step3() -> None:
    profile = st.session_state["profile"]
    risk = profile["risk"]
    cust_class = RISK_TO_CLASS[risk]
    exclusions = [p.split(" ", 1)[1] for p in profile["preferences"]
                  if p != "🌱 ESG / Nachhaltigkeit"]

    st.markdown(f'<div class="fi-section">③ {t("MiFID-II Compliance-Freigabe", "Prüfung & Freigabe")}</div>',
                unsafe_allow_html=True)

    screening = ("✅ Negative-Screening: passt zu Ausschlüssen (" + ", ".join(exclusions) + ")"
                 if exclusions else
                 "✅ Negative-Screening: Keine Ausschlusskriterien verletzt")

    if is_advisor():
        st.markdown(f"**Kundenrisikoklasse: {cust_class}** vs. "
                    f"**max. Produktrisikoklasse: {cust_class}** → ✅ Match")
        checklist = [
            "✅ MiFID-II Dokumentation vorhanden",
            "✅ KYC-Status: Verifiziert (gültig bis 01.2027)",
            f"✅ Risikoklassen-Match: Kunde Klasse {cust_class} = Vorschlag Klasse {cust_class}",
            "✅ Suitability-Test: Bestanden (Score: 94/100)",
            screening,
            "✅ Interessenkonflikt-Prüfung: Negativ",
        ]
    else:
        checklist = [
            "✅ Der Vorschlag passt zu Ihrer Risikobereitschaft",
            "✅ Ihre Identität ist verifiziert",
            "✅ Gesetzliche Eignungsprüfung bestanden",
            "✅ Nachhaltigkeits-Kriterien berücksichtigt",
            "✅ Keine Interessenkonflikte",
        ]

    st.markdown(t("##### Prüfergebnisse", "##### Das haben wir für Sie geprüft"))
    for item in checklist:
        st.markdown(item)

    st.markdown(
        '<div class="fi-success">✅ ' +
        t("FREIGEGEBEN – Anlagevorschlag kann dem Kunden präsentiert werden · "
          "Compliance-Protokoll #CP-2026-0847 erstellt",
          "Alles geprüft und freigegeben – Ihr Vorschlag ist startklar.") +
        '</div>', unsafe_allow_html=True)

    st.write("")
    left, _, right = st.columns([0.25, 0.45, 0.30])
    with left:
        if st.button("← Zurück", key="s3_back"):
            st.session_state["wizard_step"] = 2
            st.rerun()
    with right:
        if st.button(t("✓ Beratung abschließen", "✓ Fertig"), type="primary", key="s3_done"):
            st.success(t("Beratung dokumentiert. Protokoll #CP-2026-0847 abgelegt.",
                         "Vielen Dank! Ihr Vorschlag wurde gespeichert."))
            st.balloons()


# --------------------------------------------------------------------------- #
# Bereich 3: Portfolio überwachen
# --------------------------------------------------------------------------- #
def page_monitor() -> None:
    header(t("Portfolio überwachen", "Sicherheit & Nachhaltigkeit"),
           t("Markt-/Krisenfrüherkennung und ESG-Analyse laufender Portfolios",
             "Wie sicher und wie nachhaltig Ihre Geldanlage gerade ist"))

    tab_risk, tab_esg = st.tabs([t("📉 Markt & Krise", "📉 Sicherheit"),
                                 t("🌱 ESG / Nachhaltigkeit", "🌱 Nachhaltigkeit")])

    # ------------------- Tab: Markt & Krise -------------------
    with tab_risk:
        if is_advisor():
            st.markdown('<div class="fi-banner">🧠 <b>LSTM-Modell aktiv</b> · '
                        'Zeitreihen-Tiefe: 60 Tage · Konfidenz: 82 % · '
                        'Letzter Trainingslauf: 08.06.2026</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fi-banner-soft">🛡️ Unser Frühwarnsystem beobachtet '
                        'die Märkte rund um die Uhr und meldet ungewöhnliche Entwicklungen '
                        'frühzeitig.</div>', unsafe_allow_html=True)

        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=34,
            title={"text": t("Systemweiter Krisenindikator", "Aktuelle Marktstabilität") +
                           "<br><span style='font-size:0.85em;color:#e08e0b'>"
                           "Stufe: Erhöhte Aufmerksamkeit</span>"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": NAVY},
                   "steps": [{"range": [0, 25], "color": "#c8e6c9"},
                             {"range": [25, 60], "color": "#fff3c4"},
                             {"range": [60, 85], "color": "#ffd8a8"},
                             {"range": [85, 100], "color": "#f5bcbc"}],
                   "threshold": {"line": {"color": NAVY, "width": 4},
                                 "thickness": 0.8, "value": 34}}))
        st.plotly_chart(style_plotly(gauge, height=320), width="stretch")

        c1, c2 = st.columns([3, 2])
        with c1:
            days = 180
            dates = [datetime(2026, 6, 9) - timedelta(days=days - i) for i in range(days)]
            spread = np.linspace(0.9, -0.4, days) + np.random.normal(0, 0.08, days)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=spread, name="10J–2J Spread",
                                     line=dict(color=BLUE, width=2)))
            fig.add_hline(y=0, line_dash="dash", line_color="#888",
                          annotation_text="Neutral", annotation_position="top left")
            fig.add_vrect(x0=dates[-30], x1=dates[-1], fillcolor="#d64545",
                          opacity=0.12, line_width=0,
                          annotation_text="⚠️ Inversions-Phase", annotation_position="top right")
            fig.update_layout(title=t("Zinskurven-Analyse & Anomalie-Detection",
                                      "Markt-Frühindikator (Zinskurve)"))
            fig.update_yaxes(title="Spread (%-Punkte)")
            st.plotly_chart(style_plotly(fig, height=360), width="stretch")
        with c2:
            st.markdown(t("##### 🚨 Aktive Alerts", "##### Was das für Sie heißt"))
            holdings = current_holdings()
            worst = holdings.assign(ESG=holdings["Produkt"].map(ESG_SCORES).fillna(60)).pipe(
                lambda df: df.loc[df["ESG"].idxmin()]
            )
            esg_alert = worst["ESG"] < 60
            if is_advisor():
                st.error("🔴 **KRITISCH** — DAX -5,2 % in 24h · 12 Portfolios betroffen")
                st.warning("🟠 **WARNUNG** — Zinskurven-Inversion · LSTM-Konfidenz 82 %")
                if esg_alert:
                    st.warning(f"🟠 **WARNUNG** — ESG-Risiko {worst['Produkt']} {int(worst['ESG'])} · "
                               "Umschichtung empfohlen")
                st.info("🔵 **INFO** — Modell-Retraining: 10.06.2026 02:00 UTC")
            else:
                st.warning("🟠 Die Märkte sind aktuell unruhiger. Kein Grund zur Sorge – "
                           "Ihr Portfolio ist breit gestreut.")
                st.info("🔵 Ihr Berater beobachtet die Lage und meldet sich, falls etwas zu "
                        "tun ist.")

    # ------------------- Tab: ESG -------------------
    with tab_esg:
        if is_advisor():
            st.markdown('<div class="fi-banner-soft">ECA-Trigger: ESG-Score-Änderung → '
                        'Delta-Analyse → Umschichtungsvorschlag</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fi-banner-soft">🌱 So nachhaltig ist Ihre Geldanlage – '
                        'bewertet nach Umwelt, Sozialem und Unternehmensführung.</div>',
                        unsafe_allow_html=True)

        # Positionen & Scores stammen aus current_holdings()/ESG_SCORES, damit hier
        # exakt dieselben Produkte stehen wie im KI-Vorschlag bei "Kunde beraten".
        holdings = current_holdings().assign(
            ESG=lambda df: df["Produkt"].map(ESG_SCORES).fillna(60).astype(int)
        )
        threshold = 60

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("🌍 Umwelt (E)", "78 / 100", "+3")
        g2.metric("👥 Sozial (S)", "65 / 100", "-2")
        g3.metric("🏛️ Governance (G)", "74 / 100", "0", delta_color="off")
        g4.metric("⭐ Gesamt-ESG", f"{portfolio_esg_score(holdings)} / 100", "+4")

        st.write("")
        positions = holdings["Produkt"].tolist()
        scores = holdings["ESG"].tolist()
        colors = ["#1f9d55" if s >= threshold else "#d64545" for s in scores]
        fig = go.Figure(go.Bar(x=scores, y=positions, orientation="h",
                               marker=dict(color=colors), text=scores, textposition="auto"))
        fig.add_vline(x=threshold, line_dash="dash", line_color=NAVY,
                      annotation_text="Mindest-Score 60", annotation_position="top")
        fig.update_layout(title=t("ESG-Scores der Portfolio-Positionen",
                                  "Nachhaltigkeit Ihrer Anlagen"))
        fig.update_xaxes(range=[0, 100], title="ESG-Score")
        st.plotly_chart(style_plotly(fig, height=360), width="stretch")

        below = holdings[holdings["ESG"] < threshold]
        if st.toggle(t("ESG-Filter aktivieren (Mindest-Score: 60)",
                       "Nur nachhaltige Anlagen anzeigen (ab Score 60)")):
            if below.empty:
                st.success(t("Alle Positionen erfüllen den ESG-Mindest-Score.",
                             "Alle Ihre Anlagen erfüllen bereits den Nachhaltigkeits-Mindeststandard."))
            else:
                st.info(t(f"{len(below)} Position(en) unterschreiten den ESG-Mindest-Score. "
                          "Rebalancing-Vorschlag wird angezeigt.",
                          f"{len(below)} Ihrer Anlagen sind aktuell weniger nachhaltig. "
                          "Hier ein Tausch-Vorschlag:"))
                rebal_rows = []
                for _, row in below.iterrows():
                    asset = PRODUCT_TO_ASSET.get(row["Produkt"])
                    if asset:
                        esg_name, _isin, _ret, _rc = PRODUCT_CATALOG[asset]["esg"]
                        rebal_rows.append(["VERKAUFEN", row["Produkt"], f"ESG-Score {row['ESG']} < {threshold}",
                                          f"{esg_name} (ESG-Score {ESG_SCORES[esg_name]})"])
                        rebal_rows.append(["KAUFEN", esg_name, "ESG-konformer Ersatz", "–"])
                    else:
                        rebal_rows.append(["PRÜFEN", row["Produkt"],
                                          f"ESG-Score {row['ESG']} < {threshold} · Einzeltitel ohne Fonds-Substitut",
                                          "–"])
                rebal = pd.DataFrame(rebal_rows, columns=["Aktion", "Position", "Grund", "Vorgeschlagener Ersatz"])

                def color_action(val: str) -> str:
                    if val == "VERKAUFEN":
                        return "background-color:#d64545;color:white;font-weight:700;"
                    if val == "KAUFEN":
                        return "background-color:#1f9d55;color:white;font-weight:700;"
                    if val == "PRÜFEN":
                        return "background-color:#e08e0b;color:white;font-weight:700;"
                    return ""

                st.dataframe(rebal.style.map(color_action, subset=["Aktion"]),
                             width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Bereich 4: Freigabe & Compliance
# --------------------------------------------------------------------------- #
def page_compliance() -> None:
    header("Freigabe & Compliance",
           "MiFID-II Regelwerk-Engine · Eignungsprüfung vor jeder Empfehlung")

    if not is_advisor():
        st.info("Dieser Bereich ist für Ihren Berater. Er stellt sicher, dass jede Empfehlung "
                "gesetzlich zu Ihrem Profil passt, bevor sie Ihnen vorgeschlagen wird.")

    # Der aktuell in "Kunde beraten" erfasste Kunde steht hier an erster Stelle
    # (statt einer fest codierten "Dr. Maria Schmidt"), zusätzlich zwei feste
    # Demo-Profile, damit der Check weiterhin gegen beliebige Profile testbar bleibt.
    current = st.session_state["profile"]
    cust_class_current = RISK_TO_CLASS[current["risk"]]
    customer_options = {
        f"{current['name']} – Klasse {cust_class_current} (aktueller Kunde)": cust_class_current,
        "Klaus Weber – Klasse 2": 2,
        "Julia Bauer – Klasse 4": 4,
    }

    left, right = st.columns([2, 3])
    with left:
        product = st.selectbox("Anlageprodukt auswählen", list(COMPLIANCE_PRODUCTS.keys()))
        profile_choice = st.selectbox("Kundenprofil", list(customer_options.keys()))
        if st.button("🔍 Compliance-Check durchführen", type="primary"):
            st.session_state["compliance_done"] = True
            st.session_state["compliance_product"] = product
            st.session_state["compliance_profile"] = profile_choice

    with right:
        if not st.session_state.get("compliance_done"):
            st.info("Produkt und Kundenprofil auswählen, dann **Compliance-Check durchführen**.")
        else:
            product = st.session_state["compliance_product"]
            profile_choice = st.session_state["compliance_profile"]
            prod_class = COMPLIANCE_PRODUCTS[product]
            cust_class = customer_options.get(profile_choice)
            if cust_class is None:
                st.warning("Dieses Kundenprofil ist nicht mehr verfügbar (Name/Risiko wurde geändert). "
                           "Bitte Compliance-Check erneut durchführen.")
                return
            match = prod_class <= cust_class

            symbol = "✅ Match" if match else "❌ Mismatch"
            st.markdown(f"**Kundenrisikoklasse: {cust_class}** vs. "
                        f"**Produktrisikoklasse: {prod_class}** → {symbol}")

            mark = "✅" if match else "❌"
            rel = "≥" if match else "<"
            checklist = [
                "✅ MiFID-II Dokumentation vorhanden",
                "✅ KYC-Status: Verifiziert (gültig bis 01.2027)",
                f"{mark} Risikoklassen-Match: Kunde Klasse {cust_class} {rel} "
                f"Produkt Klasse {prod_class}",
                "✅ Suitability-Test: Bestanden (Score: 94/100)",
                "✅ Negative-Screening: Keine Ausschlusskriterien verletzt",
                "✅ Interessenkonflikt-Prüfung: Negativ",
            ]
            st.markdown("##### Prüfergebnisse")
            for item in checklist:
                st.markdown(item)

            if match:
                st.markdown('<div class="fi-success">✅ FREIGEGEBEN – Anlagevorschlag kann dem '
                            'Kunden präsentiert werden · Compliance-Protokoll #CP-2026-0847 '
                            'erstellt</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="fi-blocked">❌ BLOCKIERT – Risikoklassen-Mismatch. '
                            'Produkt nicht geeignet für dieses Kundenprofil.</div>',
                            unsafe_allow_html=True)

    if is_advisor():
        with st.expander("📋 Compliance-Protokoll-Historie"):
            hist = pd.DataFrame([
                ["#CP-2026-0847", "07.06.2026 09:30", "Dr. Maria Schmidt", "Allianz Interglobal",
                 "🟢 FREIGEGEBEN"],
                ["#CP-2026-0846", "06.06.2026 14:12", "Julia Bauer", "iShares MSCI World",
                 "🟢 FREIGEGEBEN"],
                ["#CP-2026-0845", "05.06.2026 11:48", "Klaus Weber", "Xtrackers DAX ETF",
                 "🔴 BLOCKIERT"],
            ], columns=["Protokoll", "Zeitstempel", "Kunde", "Produkt", "Ergebnis"])

            def color_res(val: str) -> str:
                if "BLOCKIERT" in val:
                    return "background-color:#d64545;color:white;font-weight:700;"
                return "background-color:#1f9d55;color:white;font-weight:700;"

            st.dataframe(hist.style.map(color_res, subset=["Ergebnis"]),
                         width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Sidebar & Routing
# --------------------------------------------------------------------------- #
def main() -> None:
    # ausstehenden Navigations-Wunsch anwenden (vor Widget-Instanziierung)
    if "_goto" in st.session_state:
        st.session_state["nav_page"] = st.session_state.pop("_goto")

    with st.sidebar:
        st.markdown('<div class="fi-logo">📈 FinIntel GmbH</div>', unsafe_allow_html=True)
        st.markdown('<div class="fi-logo-sub">KI-Kapitalanlageberatung</div>',
                    unsafe_allow_html=True)
        st.markdown("---")

        st.radio("Ansicht", ["👔 Berater", "🙋 Kunde"], key="mode",
                 help="Wechselt zwischen Fach-Ansicht (Berater) und vereinfachter Kundensicht.")
        st.markdown("**Navigation**")
        st.radio("Navigation", NAV_OPTIONS, key="nav_page", label_visibility="collapsed")

        st.markdown("---")
        now = datetime.now().strftime("%H:%M Uhr")
        st.markdown(
            f'<div class="fi-side-info"><b>ML-Modell Status:</b> 🟢 Online<br>'
            f'<b>Letztes Update:</b> heute, {now}<br>'
            f'<b>Projektphase:</b> MS2 → MS3</div>', unsafe_allow_html=True)
        st.markdown('<div class="fi-footer">FinIntel GmbH · Prototyp v0.1 · MS2→MS3</div>',
                    unsafe_allow_html=True)

    pages = {
        "🏠 Cockpit": page_cockpit,
        "🧭 Kunde beraten": page_wizard,
        "📡 Portfolio überwachen": page_monitor,
        "✅ Freigabe & Compliance": page_compliance,
    }
    pages[st.session_state["nav_page"]]()


if __name__ == "__main__":
    main()
