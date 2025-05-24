import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import plotly.express as px
from plotly.subplots import make_subplots
from pycountry import countries


# ---------------------- Step 1: Prepare occupancy and ADR files if not exist ----------------------
def prepare_occupancy_files():
    occ_files = ["data/occupancy_Resort_Hotel.csv", "data/occupancy_City_Hotel.csv"]

    if not all(os.path.exists(f) for f in occ_files):
        df = pd.read_csv("data/hotel_booking_cleaned.csv")
        df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'])

        df = df[df['is_canceled'] == 0]
        df['total_guests'] = df['adults'] + df['children'].fillna(0) + df['babies']
        df['check_in'] = df['reservation_status_date']
        df['nights'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
        df['check_out'] = df['check_in'] + pd.to_timedelta(df['nights'], unit='D')

        if 'adr' in df.columns:
            df = df[df['adr'].between(0, 1000)]

        os.makedirs("data", exist_ok=True)

        for hotel_type in df['hotel'].unique():
            hotel_df = df[df['hotel'] == hotel_type]
            occupancy = []

            for _, row in hotel_df.iterrows():
                for day in pd.date_range(start=row['check_in'], end=row['check_out'] - pd.Timedelta(days=1)):
                    occupancy.append((day, row['total_guests'], row.get('adr', 0)))

            occ_df = pd.DataFrame(occupancy, columns=['date', 'guests', 'adr'])
            occ_summary = occ_df.groupby('date').agg({'guests': 'sum', 'adr': 'mean'}).reset_index()
            occ_summary['hotel'] = hotel_type
            occ_summary.to_csv(f"data/occupancy_{hotel_type.replace(' ', '_')}.csv", index=False)

# ---------------------- Step 2: App configuration ----------------------
st.set_page_config(layout="wide")

st.title("🏨 Hotel Performance Dashboard")

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 100% !important;
    background-color: white;
}
.stApp {
    background-color: white;
}
h1, h2, h3, h4 {
    font-size: unset !important;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

.element-container {
    margin-bottom: 0.2rem;
}

div[data-testid="stVerticalBlock"] > div:first-of-type {
    margin-bottom: 0rem;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.5rem;
}

.stSelectbox {
    margin-bottom: 0.2rem;
}

.kpi-box {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    text-align: left;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}
.kpi-label {
    font-size: 0.9rem;
    color: #0f172a;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: #0f172a;
    margin-bottom: 0.5rem;
}
.kpi-delta {
    font-size: 0.9rem;
    font-weight: 500;
    margin-top: auto;
    display: flex;
    align-items: center;
    gap: 0.25rem;
}

.kpi-column {
    border-radius: 15px;
    padding: 1.2rem;
    display: flex;
    flex-direction: column;
    min-height: 100%;
}


.data-sources {
    font-size: 0.7rem;
    color: #94a3b8;
    text-align: center;
    line-height: 1.4;
}

.data-sources a {
    color: #7b2cbf;
    text-decoration: none;
}

.data-sources a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

# ------------------ KPI Section ------------------
FAKE_TODAY = pd.Timestamp("2016-09-21")

prepare_occupancy_files()
HOTEL_THRESHOLDS = {"Resort Hotel": 600, "City Hotel": 500}

@st.cache_data
def load_occupancy_data(hotel):
    df = pd.read_csv(f"data/occupancy_{hotel.replace(' ', '_')}.csv")
    df['date'] = pd.to_datetime(df['date'])
    df['hotel'] = hotel
    return df

@st.cache_data
def load_raw_data():
    df = pd.read_csv("data/hotel_booking_cleaned.csv")
    df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'])
    df['lead_time'] = df['lead_time'].fillna(0)
    return df

selected_hotels = ["Resort Hotel", "City Hotel"]
all_data = pd.concat([load_occupancy_data(h) for h in selected_hotels])

# Years for KPI section
available_years = sorted(all_data['date'].dt.year.unique())
available_years = [year for year in available_years if year > 2015]  # Hide 2015 from selector

raw_df = load_raw_data()

# Replace 3-letter country codes with full country names
# Convert 3-letter country codes to full names
code_to_name = {c.alpha_3: c.name for c in countries}
raw_df["country"] = raw_df["country"].map(code_to_name).fillna(raw_df["country"])

# Add derived columns
def enrich_data(df):
    df = df.copy()
    df["guest_type"] = df.apply(
        lambda row: "Solo Traveler" if row["adults"] == 1 and row["children"] + row["babies"] == 0
        else "Couple" if row["adults"] == 2 and row["children"] + row["babies"] == 0
        else "Trio" if row["adults"] == 3 and row["children"] + row["babies"] == 0
        else "Family" if row["children"] + row["babies"] > 0
        else "Other",
        axis=1
    )
    df["season"] = df["arrival_date_month"].map({
        'December': 'Winter', 'January': 'Winter', 'February': 'Winter',
        'March': 'Spring', 'April': 'Spring', 'May': 'Spring',
        'June': 'Summer', 'July': 'Summer', 'August': 'Summer',
        'September': 'Autumn', 'October': 'Autumn', 'November': 'Autumn'
    })
    return df

raw_df = enrich_data(raw_df)

# Prepare country data
top_10_countries = raw_df["country"].value_counts().head(10).index.tolist()
top_5_countries = raw_df["country"].value_counts().head(5).index.tolist()
all_countries_sorted = sorted(set(raw_df["country"].dropna()) - set(top_10_countries))
countries = ["Worldwide", "Top 10 Countries", "Top 5 Countries"] + top_10_countries + all_countries_sorted

# Get all available years for guest profile section (excluding 2014)
profile_available_years = sorted([year for year in raw_df['reservation_status_date'].dt.year.unique() if year > 2014])

# Create main layout with KPIs on left
kpi_col, charts_col = st.columns([1, 4], gap="small")

# KPI section in left column
with kpi_col:
    st.markdown('<div class="kpi-column">', unsafe_allow_html=True)
    
    # Year selection for KPIs
    selected_year = st.selectbox("Select Year", available_years, index=available_years.index(FAKE_TODAY.year))
    this_year = selected_year
    last_year = this_year - 1

    kpi_df = all_data.copy()
    kpi_df['year'] = kpi_df['date'].dt.year

    # Calculate KPI values
    adr_this_year = kpi_df[kpi_df['year'] == this_year]['adr'].mean()
    adr_last_year = kpi_df[kpi_df['year'] == last_year]['adr'].mean()
    adr_delta = adr_this_year - adr_last_year
    adr_delta_pct = (adr_delta / adr_last_year) * 100 if adr_last_year else 0

    st.markdown(f"""
    <div class='kpi-box'>
        <div class='kpi-label'>Average ADR ({this_year})</div>
        <div class='kpi-value'>${adr_this_year:.1f}</div>
        <div class='kpi-delta' style='color: {"#16a34a" if adr_delta >= 0 else "#dc2626"}'>
            {adr_delta:+.1f} ({adr_delta_pct:+.1f}%) vs {last_year}
        </div>
    </div>
    """, unsafe_allow_html=True)

    for hotel in selected_hotels:
        current_df = kpi_df[(kpi_df['hotel'] == hotel) & (kpi_df['year'] == this_year)]
        previous_df = kpi_df[(kpi_df['hotel'] == hotel) & (kpi_df['year'] == last_year)]

        total_possible_now = len(current_df) * HOTEL_THRESHOLDS[hotel]
        total_possible_last = len(previous_df) * HOTEL_THRESHOLDS[hotel]

        occ_now = current_df['guests'].sum() / total_possible_now * 100 if total_possible_now else 0
        occ_last = previous_df['guests'].sum() / total_possible_last * 100 if total_possible_last else 0
        occ_delta = occ_now - occ_last

        delta_color_occ = '#16a34a' if occ_delta > 0 else '#dc2626'

        st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-label'>{hotel} Avg Occupancy ({this_year})</div>
            <div class='kpi-value'>{occ_now:.1f}%</div>
            <div class='kpi-delta' style='color: {delta_color_occ}'>
                {occ_delta:+.1f}% vs {last_year}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Calculate reservation and cancellation rates
    reservations_this_year = raw_df[raw_df['reservation_status_date'].dt.year == this_year].shape[0]
    reservations_last_year = raw_df[raw_df['reservation_status_date'].dt.year == last_year].shape[0]
    reservations_delta_pct = ((reservations_this_year - reservations_last_year) / reservations_last_year * 100) if reservations_last_year else 0

    cancellations_this_year = raw_df[(raw_df['reservation_status_date'].dt.year == this_year) & (raw_df['is_canceled'] == 1)].shape[0]
    cancellations_last_year = raw_df[(raw_df['reservation_status_date'].dt.year == last_year) & (raw_df['is_canceled'] == 1)].shape[0]
    
    cancel_rate_this_year = (cancellations_this_year / reservations_this_year * 100) if reservations_this_year else 0
    cancel_rate_last_year = (cancellations_last_year / reservations_last_year * 100) if reservations_last_year else 0
    cancel_rate_delta = cancel_rate_this_year - cancel_rate_last_year

    st.markdown(f"""
    <div class='kpi-box'>
        <div class='kpi-label'>Reservation Volume ({this_year})</div>
        <div class='kpi-value'>{reservations_this_year:,}</div>
        <div class='kpi-delta' style='color: {"#16a34a" if reservations_delta_pct >= 0 else "#dc2626"}'>
            {reservations_delta_pct:+.1f}% vs {last_year}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='kpi-box'>
        <div class='kpi-label'>Cancellation Rate ({this_year})</div>
        <div class='kpi-value'>{cancel_rate_this_year:.1f}%</div>
        <div class='kpi-delta' style='color: {"#dc2626" if cancel_rate_delta > 0 else "#16a34a"}'>
            {cancel_rate_delta:+.1f}% vs {last_year}
        </div>
    </div>

    <div style='
        text-align: center;
        margin-top: 2rem;
        width: 100%;
    '>
    """, unsafe_allow_html=True)
    
    # Create columns with more space in the middle
    col1, col2, col3 = st.columns([1,4,2])
    with col2:
       
        # Center the data sources text
        st.markdown("""
            <div style='
                font-size: 0.75rem;
                color: #94a3b8;
                text-align: center;
                line-height: 1.2;
                margin-top: 7rem;
            '>
                Data Sources:
                <br>
                <a href="https://www.kaggle.com/datasets/mojtaba142/hotel-booking/data" target="_blank" style='color: #7b2cbf; text-decoration: none;'>Hotel Booking Dataset</a> 
                <br>
                <a href="https://www.kaggle.com/datasets/liewyousheng/geolocation" target="_blank" style='color: #7b2cbf; text-decoration: none;'>Geolocation Dataset</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Create initial date range centered around FAKE_TODAY
initial_range = [FAKE_TODAY - pd.Timedelta(days=15), FAKE_TODAY + pd.Timedelta(days=15)]

# Charts section on the right
with charts_col:
    # Add Occupancy and ADR charts side by side
    top_charts_cols = st.columns(2, gap="small")
    with top_charts_cols[0]:
        st.subheader("Optimize Occupancy for Campaign")

        fig = make_subplots(
            rows=len(selected_hotels),
            cols=1,
            shared_xaxes=True,
            subplot_titles=selected_hotels,
            vertical_spacing=0.15
        )

        def get_color(val, threshold):
            return '#E74C3C' if val > threshold else '#2ECC71' if val >= 0.75 * threshold else '#F1C40F'

        for i, hotel in enumerate(selected_hotels):
            df = all_data[all_data['hotel'] == hotel].copy()
            threshold = HOTEL_THRESHOLDS[hotel]
            df['color'] = df['guests'].apply(lambda x: get_color(x, threshold))

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['guests'],
                mode='lines+markers',
                marker=dict(color=df['color'], size=6),
                line=dict(color='lightgray'),
                hovertemplate='Date: %{x}<br>Guests: %{y}<extra></extra>',
                showlegend=False
            ), row=i+1, col=1)

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=[threshold] * len(df),
                mode='lines',
                line=dict(color='black', dash='dash'),
                showlegend=False
            ), row=i+1, col=1)

        fig.add_vline(x=FAKE_TODAY, line_dash='dash', line_color='black')
        fig.add_annotation(x=FAKE_TODAY, y=max(HOTEL_THRESHOLDS.values()), text="Today", showarrow=True, arrowhead=1, ax=20, ay=-40)

        # Occupancy Chart
        fig.update_layout(
            height=400,  # Reduced from 500
            margin=dict(t=50, b=30, l=40, r=20),
            hovermode='x unified',
            dragmode='pan',
            legend_title_text="Color Legend",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                itemsizing='constant',
                traceorder='normal'
            )
        )

        for i in range(1, len(selected_hotels) + 1):
            fig.update_xaxes(
                row=i,
                col=1,
                type="date",
                range=initial_range,
                showspikes=True,
                rangeslider=dict(visible=(i == len(selected_hotels))),
                fixedrange=False
            )

            fig.update_yaxes(
                row=i,
                col=1,
                title_text="Number of Guests"
            )

        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', marker=dict(size=10, color='#2ECC71'), name='Balanced (75%-100%)'
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', marker=dict(size=10, color='#F1C40F'), name='Underloaded (<75%)'
        ))
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers', marker=dict(size=10, color='#E74C3C'), name='Over Capacity (>100%)'
        ))

        st.plotly_chart(fig, use_container_width=True)

    with top_charts_cols[1]:
        st.subheader("Optimize Prise for Campaign")
        adr_fig = go.Figure()
        for hotel in selected_hotels:
            df = all_data[all_data['hotel'] == hotel].copy()
            adr_fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['adr'],
                mode='lines',
                name=hotel,
                line=dict(width=2)
            ))

        adr_fig.add_vline(x=FAKE_TODAY, line_dash='dash', line_color='black')
        adr_fig.add_annotation(x=FAKE_TODAY, y=all_data['adr'].max(), text="Today", showarrow=True, arrowhead=1)

        adr_fig.update_layout(
            height=400,
            margin=dict(t=50, b=30, l=40, r=20),
            hovermode='x unified',
            dragmode='pan',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5
            ),
            yaxis_title="Average Daily Rate ($)",
            xaxis_rangeslider_visible=True,
            xaxis_range=initial_range
        )

        st.plotly_chart(adr_fig, use_container_width=True)

    # Add break line after charts but before filters
    st.markdown("<hr style='margin: 2em 0; border-top: 1px solid #ccc'>", unsafe_allow_html=True)
    
    # Add country and year selection under the charts
    filter_cols = st.columns([1, 3], gap="small")
    with filter_cols[0]:
        selected_country = st.selectbox("Select Country", countries, index=0, key="country_select")
    with filter_cols[1]:
        selected_years = st.multiselect("Select Year(s)", options=profile_available_years, default=profile_available_years, key="year_select")

    # Fallback if no years are selected
    if not selected_years:
        selected_years = profile_available_years

    # Filter data based on selection
    if selected_country == "Worldwide":
        filtered_df = raw_df.copy()
    elif selected_country == "Top 10 Countries":
        filtered_df = raw_df[raw_df["country"].isin(top_10_countries)]
    elif selected_country == "Top 5 Countries":
        filtered_df = raw_df[raw_df["country"].isin(top_5_countries)]
    else:
        filtered_df = raw_df[raw_df['country'] == selected_country]

    filtered_df = filtered_df[filtered_df['reservation_status_date'].dt.year.isin(selected_years)]

    # Profile breakdown title
    st.markdown(f"# :violet[{selected_country}] Guest Profile Breakdown")
    
    # Create columns with more space in the middle
    chart_cols = st.columns([1, 1, 2], gap="small")
    
    # First column: Lead Time and Guest Composition
    with chart_cols[0]:
        st.subheader("How Far in Advance Do Guests Book?")
        # Fix lead time aggregation
        if selected_country in ["Top 10 Countries", "Top 5 Countries"]:
            lead_counts = filtered_df.groupby("lead_time").size().reset_index(name="count")
            lead_counts.columns = ["lead_time", "count"]
        else:
            lead_counts = filtered_df["lead_time"].value_counts().sort_index().reset_index()
            lead_counts.columns = ["lead_time", "count"]

        lead_fig = px.scatter(
            lead_counts,
            x="lead_time",
            y="count",
            labels={"lead_time": "Lead Time (Days)", "count": "# of Reservations"},
            height=220,
            template="simple_white"
        )
        lead_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(lead_fig, use_container_width=True)

        st.subheader("Guest Group Composition")
        guest_fig = px.pie(
            filtered_df, 
            names="guest_type", 
            height=220, 
            template="simple_white"
        )
        guest_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10))
        st.plotly_chart(guest_fig, use_container_width=True)
    
    # Second column: Season and Market
    with chart_cols[1]:
        st.subheader("Most Popular Season")
        SEASON_ORDER = ["Winter", "Spring", "Summer", "Autumn"]

        # Fix season aggregation
        season_counts = filtered_df["season"].value_counts().reset_index()
        season_counts.columns = ["season", "count"]

        # Ensure all seasons are present and in correct order
        all_seasons = pd.DataFrame({"season": SEASON_ORDER})
        season_counts = all_seasons.merge(season_counts, on="season", how="left").fillna(0)
        season_counts = season_counts.sort_values("season", key=lambda x: pd.Categorical(x, categories=SEASON_ORDER, ordered=True))

        # Add color column for highlighting
        season_counts['color'] = '#7b2cbf'  # Default purple color
        max_count_idx = season_counts['count'].idxmax()
        season_counts.loc[max_count_idx, 'color'] = '#e76f51'  # Highlight color (coral)

        season_fig = px.bar(
            season_counts,
            x="season",
            y="count",
            labels={"season": "Season", "count": "# of Reservations"},
            height=220,
            template="simple_white",
            color='color',
            color_discrete_map="identity",
            category_orders={"season": SEASON_ORDER}
        )
        season_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(season_fig, use_container_width=True)

        st.subheader("Market Segment Distribution")
        MARKET_SEGMENT_ORDER = ["Direct", "Corporate", "Online TA", "Offline TA/TO", "Groups", "Aviation", "Complementary"]

        # Fix market segment aggregation
        market_counts = filtered_df[filtered_df["market_segment"] != "Undefined"]["market_segment"].value_counts().reset_index()
        market_counts.columns = ["segment", "count"]

        # Ensure all segments are present and in correct order
        all_segments = pd.DataFrame({"segment": MARKET_SEGMENT_ORDER})
        market_counts = all_segments.merge(market_counts, on="segment", how="left").fillna(0)
        market_counts = market_counts.sort_values("segment", key=lambda x: pd.Categorical(x, categories=MARKET_SEGMENT_ORDER, ordered=True))

        market_fig = px.scatter(
            market_counts,
            x="segment",
            y="count",
            size="count",
            size_max=50,
            labels={"segment": "Market Segment", "count": "# of Guests"},
            height=220,
            template="simple_white",
            color_discrete_sequence=["#7b2cbf"],
            category_orders={"segment": MARKET_SEGMENT_ORDER}
        )
        market_fig.update_layout(margin=dict(t=20, b=10, l=10, r=10), xaxis_tickangle=45)
        st.plotly_chart(market_fig, use_container_width=True)
    
    # Third column: Map
    with chart_cols[2]:
        st.subheader("Reservations by Country")
        coords_path = "data/latitude_and_longitude_values.csv"
        country_coords = pd.read_csv(coords_path)
        country_coords = country_coords.rename(columns={"country": "country", "latitude": "lat", "longitude": "lon"})
        country_coords = country_coords.dropna(subset=["lat", "lon"])

        # Aggregate from all data to preserve gray countries
        map_df = raw_df[raw_df['reservation_status_date'].dt.year.isin(selected_years)]
        map_data = map_df.groupby("country").agg(
            total_reservations=("hotel", "count"),
            cancellations=("is_canceled", "mean")
        ).reset_index()

        map_data = map_data.merge(country_coords[["country", "lat", "lon"]], on="country", how="left")
        map_data["show_up"] = 1 - map_data["cancellations"]
        map_data["total_reservations"] = map_data["total_reservations"].round(0).astype(int)
        map_data["show_up"] = (map_data["show_up"] * 100).round(0).astype(int)
        map_data["cancellations"] = (map_data["cancellations"] * 100).round(0).astype(int)
        map_data = map_data.dropna(subset=["lat", "lon"])

        if selected_country == "Top 10 Countries":
            highlight_countries = top_10_countries
        elif selected_country == "Top 5 Countries":
            highlight_countries = top_5_countries
        elif selected_country == "Worldwide":
            highlight_countries = map_data["country"].tolist()
        else:
            highlight_countries = [selected_country]

        map_data["highlight"] = map_data["country"].isin(highlight_countries)
        map_data["color"] = map_data["highlight"].map(lambda x: "#7b2cbf" if x else "#d3d3d3")
        map_fig = px.scatter_geo(
            map_data,
            lat="lat",
            lon="lon",
            size="total_reservations",
            color="color",
            color_discrete_map="identity",
            custom_data=["country", "total_reservations", "show_up", "cancellations"],
            projection="natural earth",
            center={"lat": 54, "lon": 15},
            scope="europe",
            template="plotly_white",
            height=460
        )

        map_fig.update_traces(
            marker=dict(
                opacity=0.8,
                sizemode="area",
                sizeref=2.*max(map_data["total_reservations"])/(40.**2),
                sizemin=4
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                          "Total Reservations: %{customdata[1]}<br>" +
                          "Show-up Rate: %{customdata[2]}%<br>" +
                          "Cancellation Rate: %{customdata[3]}%<extra></extra>"
        )

        map_fig.update_layout(showlegend=False)
        map_fig.update_geos(
            lataxis_range=[35, 65],
            lonaxis_range=[-15, 40],
            showcoastlines=True,
            coastlinecolor="gray",
            showcountries=True,
            countrycolor="black",
            showland=True,
            landcolor="#f0f0f0",
            showocean=True,
            oceancolor="#cce6ff",
            showlakes=True,
            lakecolor="#cce6ff",
            framecolor="gray"
        )

        st.plotly_chart(map_fig, use_container_width=True)

