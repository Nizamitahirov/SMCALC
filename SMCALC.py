import streamlit as st
import pandas as pd

# --- Helper Functions ---
def format_percent(value, decimals=1):
    if value is None or pd.isna(value): return "N/A"
    try: return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError): return "N/A"

# DAX-inspired calculation functions
def calculate_sales_performance(actual_sales, forecast_sales):
    if forecast_sales is None or forecast_sales == 0 or actual_sales is None: 
        return 0.0
    try:
        result = actual_sales / forecast_sales
        return min(result, 1.0)
    except ZeroDivisionError:
        return 0.0

def calculate_wastage_performance(actual_wastage, actual_sales, wastage_target_amount):
    if actual_wastage is None or actual_sales is None or wastage_target_amount is None:
        return 0.0
    
    try:
        # Calculate wastage percentage
        wastage_percentage = actual_wastage / actual_sales if actual_sales != 0 else 0
        
        # Determine performance
        if actual_wastage <= wastage_target_amount:
            return 1.0  # Best case
        elif wastage_target_amount == 0:
            return 0.0  # Avoid division by zero
        elif actual_wastage >= wastage_target_amount * 1.2:
            return 0.0  # Worst case
        else:
            # Calculate penalty
            denominator = wastage_target_amount * 20
            if denominator == 0:
                return 0.0
            accepted = 1.0 - ((actual_wastage - wastage_target_amount) * (100 / denominator))
            return max(0.0, min(accepted, 1.0))
    except ZeroDivisionError:
        return 0.0

def calculate_opex_performance(actual_opex, target_opex, actual_sales):
    if actual_opex is None or target_opex is None or actual_sales is None:
        return 0.0
    
    try:
        # Calculate percentages
        if actual_sales == 0:
            return 0.0  # Avoid division by zero
            
        opex_target_percentage = target_opex / actual_sales
        actual_opex_percentage = actual_opex / actual_sales
        
        # Determine performance
        if actual_opex_percentage <= opex_target_percentage:
            return 1.0  # Best case
        elif opex_target_percentage == 0:
            return 0.0  # Avoid division by zero
        elif actual_opex_percentage >= opex_target_percentage * 1.2:
            return 0.0  # Worst case
        else:
            # Calculate penalty
            denominator = opex_target_percentage * 20
            if denominator == 0:
                return 0.0
            accepted = 1.0 - ((actual_opex_percentage - opex_target_percentage) * (100 / denominator))
            return max(0.0, min(accepted, 1.0))
    except ZeroDivisionError:
        return 0.0

def calculate_turnover_performance(actual_separations, target_separations):
    if actual_separations is None or target_separations is None:
        return 0.0
    
    try:
        # Determine performance
        if actual_separations <= target_separations:
            return 1.0  # Best case
        elif target_separations == 0:
            return 0.0  # Avoid division by zero
        elif actual_separations >= target_separations * 1.2:
            return 0.0  # Worst case
        else:
            # Calculate penalty - similar to DAX's 1 - (ratio - 1) * 5
            performance = 1.0 - ((actual_separations / target_separations) - 1.0) * 5.0
            return max(0.0, min(performance, 1.0))
    except ZeroDivisionError:
        return 0.0

def calculate_mystery_shopper_performance(actual_value):
    if actual_value is None: 
        return 0.0
    try:
        result = actual_value / 100.0  # Convert percentage to decimal
        return min(result, 1.0)
    except ZeroDivisionError:
        return 0.0

def calculate_excellence_performance(actual_value):
    if actual_value is None: 
        return 0.0
    try:
        result = actual_value / 100.0  # Convert percentage to decimal
        return min(result, 1.0)
    except ZeroDivisionError:
        return 0.0

def calculate_behavioural_performance(actual_value):
    if actual_value is None: 
        return 0.0
    try:
        result = actual_value / 5.0  # Scale out of 5
        return min(result, 1.0)
    except ZeroDivisionError:
        return 0.0

def calculate_final_performance(kpi_results):
    # Get the weighted performances according to DAX
    # Operational metrics (50% total weighting)
    sales_perf = kpi_results.get("Sales", 0) * 0.30
    wastage_perf = kpi_results.get("Wastage", 0) * 0.30
    opex_perf = kpi_results.get("OPEX", 0) * 0.20
    turnover_perf = kpi_results.get("Turnover", 0) * 0.20
    
    # Customer experience metrics (direct contribution)
    excellence_perf = kpi_results.get("Excellence check", 0) * 0.20
    mystery_shopper_perf = kpi_results.get("Mystery shopper", 0) * 0.20
    behavioural_perf = kpi_results.get("Behaviour", 0) * 0.10
    
    # Final calculation as per DAX formula
    # ((operations metrics) * 0.5) + customer experience metrics
    final_score = ((sales_perf + wastage_perf + opex_perf + turnover_perf) * 0.5) + \
                  excellence_perf + mystery_shopper_perf + behavioural_perf
    
    return final_score

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Performance Calculator")

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    /* Center the main block */
    .main .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 2rem;
        margin: auto;
    }
    /* Style the metric card */
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        border: 1px solid #dde2eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .metric-card .stMetric {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        text-align: center;
    }
    /* Make metric label larger */
    .metric-card .stMetric > label {
        font-size: 1.1em !important;
        font-weight: 600 !important;
        color: #4f4f4f !important;
    }
    /* Make metric value larger and bolder */
    .metric-card .stMetric > div[data-testid="stMetricValue"] {
        font-size: 2.5em !important;
        font-weight: 700 !important;
        color: #1c4e80;
        justify-content: center;
    }
    /* Style table headers */
    .table-header {
        font-weight: bold;
        color: #1c4e80;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #dde2eb;
        margin-bottom: 0.5rem;
    }
    /* Style table rows */
    .table-row {
        border-bottom: 1px solid #dde2eb;
        padding-top: 0.6rem;
        padding-bottom: 0.6rem;
        display: flex;
        align-items: center;
    }
    /* Style the total row */
    .total-row {
        font-weight: bold;
        padding-top: 1rem;
        margin-top: 0.5rem;
        border-top: 2px solid #dde2eb;
        display: flex;
        align-items: center;
    }
    /* Style number input fields */
    div[data-testid="stNumberInput"] input {
        text-align: right;
        padding-right: 5px !important;
    }
    div[data-testid="stNumberInput"] label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Definition and Initial Values ---
kpis = {
    "Sales": {"target": 0, "actual": 0, "unit": "K", "weight": 0.30, "explanation_az": "Hədəflənmiş satışlarla müqayisədə faktiki əldə edilən satış həcmini ölçür. Hədəfə yaxınlaşmaq və ya onu keçmək nəticəni yaxşılaşdırır (maksimum 100% ilə məhdudlaşır)."},
    "Wastage": {"target": 0, "actual": 0, "unit": "%", "weight": 0.30, "explanation_az": "Hədəf tullantı məbləği ilə müqayisədə faktiki tullantı məhsullarının dəyərini ölçür. Tullantının az olması daha yaxşıdır. Tullantı hədəfin 120%-ni keçərsə, nəticə əhəmiyyətli dərəcədə azalır."},
    "OPEX": {"target": 0, "actual": 0, "unit": "K", "weight": 0.20,  "explanation_az": "Satışlara nisbətdə hədəf OPEX məbləği ilə müqayisədə faktiki əməliyyat xərclərini (OPEX) ölçür. OPEX-in aşağı olması daha yaxşıdır. OPEX hədəf faizinin 120%-ni keçərsə, nəticə əhəmiyyətli dərəcədə azalır."},
    "Turnover": {"target": 0, "actual": 0, "unit": "Count", "weight": 0.20, "explanation_az": "Hədəf rəqəmlə müqayisədə könüllü olaraq işdən ayrılan işçilərin sayını (axıcılıq) ölçür. İşdən ayrılmaların sayının az olması daha yaxşı nəticə deməkdir. Ayrılmalar hədəfin 120%-ni keçərsə, nəticə əhəmiyyətli dərəcədə azalır."},
    "Mystery shopper": {"target": 100, "actual": 0, "unit": "%", "weight": 0.20, "explanation_az": "Müştəri xidməti və mağaza standartlarını qiymətləndirən gizli müştəri ziyarətlərindən alınan xalı əks etdirir. Yüksək xallar daha yaxşıdır (maksimum 100% ilə məhdudlaşır)."},
    "Excellence check": {"target": 100, "actual": 0, "unit": "%", "weight": 0.20,  "explanation_az": "Əməliyyat mükəmməlliyi və standartları üzrə daxili yoxlamalardan (məsələn, CEO checklist) alınan xalı təmsil edir. Yüksək xallar daha yaxşıdır (maksimum 100% ilə məhdudlaşır)."},
    "Behaviour": {"target": 5, "actual": 0, "unit": "/ 5", "weight": 0.10, "explanation_az": "Şirkət dəyərləri və standartlarına uyğun olaraq müşahidə edilən davranışları qiymətləndirir (adətən 1-5 şkalası ilə). Yüksək xallar daha yaxşı uyğunluğu göstərir."}, 
}

# --- Store Input State ---
if 'kpi_inputs' not in st.session_state:
    st.session_state.kpi_inputs = {
        k: {'target': v['target'], 'actual': v['actual']}
        for k, v in kpis.items()
    }

# --- Initialize Performance Results ---
perf_results = {}

# --- Input and Calculation Section ---
st.subheader("Performance Metrics")
st.caption("Enter Target and Actual values")

# Table Header
header_cols = st.columns([3, 3, 3, 2])
with header_cols[0]: st.markdown("<div class='table-header'>KPIs</div>", unsafe_allow_html=True)
with header_cols[1]: st.markdown("<div class='table-header' style='text-align:right;'>Target</div>", unsafe_allow_html=True)
with header_cols[2]: st.markdown("<div class='table-header' style='text-align:right;'>Actual</div>", unsafe_allow_html=True)
with header_cols[3]: st.markdown("<div class='table-header' style='text-align:right;'>Result</div>", unsafe_allow_html=True)

    # Table Rows (Inputs and Results)
for kpi_name, kpi_data in kpis.items():
    row_cols = st.columns([3, 3, 3, 2])

    with row_cols[0]:
        st.markdown(f"{kpi_name} ({kpi_data['unit']}) - {int(kpi_data['weight']*100)}%", unsafe_allow_html=True)

    with row_cols[1]:
        # Target Input - Set appropriate step values based on KPI type
        if kpi_name == "Sales" or kpi_name == "OPEX":
            step = 1000  # Step by 1K for Sales and OPEX
        elif kpi_name == "Turnover":
            step = 1  # Whole numbers for Turnover
        elif kpi_name == "Behaviour":
            step = 0.5  # Half-point steps for Behaviour (0-5 scale)
        elif kpi_name in ["Mystery shopper", "Excellence check", "Wastage"]:
            step = 0.1  # Small steps for percentage values
        else:
            step = 0.01  # Default small step
            
        st.session_state.kpi_inputs[kpi_name]['target'] = st.number_input(
            f"Target {kpi_name}",
            value=float(st.session_state.kpi_inputs[kpi_name]['target']),  # Ensure value is float
            key=f"target_{kpi_name}",
            step=float(step),  # Ensure step is float
            label_visibility="collapsed",
        )

    with row_cols[2]:
        # Actual Input - Same step logic as above
        if kpi_name == "Sales" or kpi_name == "OPEX":
            step = 1000  # Step by 1K for Sales and OPEX
        elif kpi_name == "Turnover":
            step = 1  # Whole numbers for Turnover
        elif kpi_name == "Behaviour":
            step = 0.5  # Half-point steps for Behaviour (0-5 scale)
        elif kpi_name in ["Mystery shopper", "Excellence check", "Wastage"]:
            step = 0.1  # Small steps for percentage values
        else:
            step = 0.01  # Default small step
            
        st.session_state.kpi_inputs[kpi_name]['actual'] = st.number_input(
            f"Actual {kpi_name}",
            value=float(st.session_state.kpi_inputs[kpi_name]['actual']),  # Ensure value is float
            key=f"actual_{kpi_name}",
            step=float(step),  # Ensure step is float
            label_visibility="collapsed",
        )

    # Calculate performance metrics based on KPI
    target_input = st.session_state.kpi_inputs[kpi_name]['target']
    actual_input = st.session_state.kpi_inputs[kpi_name]['actual']
    
    # Skip calculation if inputs are invalid
    if target_input is None or actual_input is None:
        perf_results[kpi_name] = None
        continue
        
    try:
        # Calculate performance based on KPI type
        if kpi_name == "Sales":
            perf_results[kpi_name] = calculate_sales_performance(actual_input, target_input)
        elif kpi_name == "Wastage":
            # For Wastage, we need to get Sales actual as well
            sales_actual = st.session_state.kpi_inputs["Sales"]['actual']
            # Assuming wastage is a percentage, convert to amount
            wastage_amount = actual_input * sales_actual if sales_actual and sales_actual != 0 else 0
            target_amount = target_input * sales_actual if sales_actual and sales_actual != 0 else 0
            perf_results[kpi_name] = calculate_wastage_performance(wastage_amount, sales_actual, target_amount)
        elif kpi_name == "OPEX":
            sales_actual = st.session_state.kpi_inputs["Sales"]['actual']
            perf_results[kpi_name] = calculate_opex_performance(actual_input, target_input, sales_actual)
        elif kpi_name == "Turnover":
            perf_results[kpi_name] = calculate_turnover_performance(actual_input, target_input)
        elif kpi_name == "Mystery shopper":
            perf_results[kpi_name] = calculate_mystery_shopper_performance(actual_input)
        elif kpi_name == "Excellence check":
            perf_results[kpi_name] = calculate_excellence_performance(actual_input)
        elif kpi_name == "Behaviour":
            perf_results[kpi_name] = calculate_behavioural_performance(actual_input)
        else:
            # Fallback to simple calculation for any unhandled KPIs
            perf_results[kpi_name] = actual_input / target_input if target_input and target_input != 0 else 0.0
    except Exception as e:
        # Handle any unexpected errors
        perf_results[kpi_name] = 0.0

    with row_cols[3]:
        # Display Result (formatted percentage)
        result_val = perf_results[kpi_name]
        formatted_result = format_percent(result_val, 1) if result_val is not None else "N/A"
        st.markdown(f"<div style='text-align: right;'>{formatted_result}</div>", unsafe_allow_html=True)

# Calculate Final Performance with correct weights
final_perf_score = calculate_final_performance(perf_results)

# --- Final Performance Card ---
st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

# Determine card color based on score
card_color = "#e6f7e6" if final_perf_score >= 0.8 else "#ffebeb"  # Green if ≥80%, red otherwise
border_color = "#b8e0b8" if final_perf_score >= 0.8 else "#ffcccc"  # Darker green/red for border

card_cols = st.columns([1, 2, 1])
with card_cols[1]:
    with st.container():
        st.markdown(f"""
        <div class='metric-card' style='background-color: {card_color}; border-color: {border_color};'>
            <div style='font-size: 1.1em; font-weight: 600; color: #4f4f4f; margin-bottom: 10px;'>
                Final Performance Score
            </div>
            <div style='font-size: 2.5em; font-weight: 700; color: #1c4e80;'>
                {format_percent(final_perf_score, 1)}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- İzah Bölməsi (Azərbaycan dilində) ---
with st.expander("Performans Hesablanması Haqqında (Sadələşdirilmiş İzah)", expanded=False):
    st.markdown("Aşağıda hər bir performans metrikasının sadə izahı verilmişdir:")
    for i, (kpi_name, kpi_data) in enumerate(kpis.items()):
        st.markdown(f"**{kpi_name}**")
        st.markdown(f"<p>{kpi_data['explanation_az']}</p>", unsafe_allow_html=True)
        if i < len(kpis) - 1: st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("**Final Performance**")
    st.markdown(f"<p>Yekun hesablama: ((Satış*30% + Tullantı*30% + OPEX*20% + Dövriyyə*20%)*50%) + (Keyfiyyət yoxlaması*20% + Müştəri qiymətləndirməsi*20% + Davranış*10%)</p>", unsafe_allow_html=True)
# --- Add Total Row to Table ---
# Removed the total row section