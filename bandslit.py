import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

# ----------------- Streamlit Page Config -----------------
st.set_page_config(page_title="Wireless Technologies", layout="wide")

# ----------------- Tabs -----------------
tab1, tab2 = st.tabs(["📡 Technology Bands", "🔗 Technology Interfaces"])

# ----------------- Frequency Dashboard -----------------
with tab1:
    st.title("📡 Wireless Technologies Frequency Bands")
    st.write("Explore frequency allocations for 2G, 3G, 4G, and 5G technologies — with NTN band highlighting.")

    @st.cache_data
    def load_main_data():
        df = pd.read_csv("Frequency Bands for 2G 3G 4G and 5G.csv")

        def expand_frequencies(row):
            f = row['F(MHz)']
            if isinstance(f, str) and '/' in f:
                return [{**row, 'F(MHz)': float(val)} for val in f.split('/')]
            else:
                return [{**row, 'F(MHz)': float(f)}]

        expanded_rows = []
        for _, row in df.iterrows():
            expanded_rows.extend(expand_frequencies(row))
        expanded_df = pd.DataFrame(expanded_rows)
        expanded_df = expanded_df.dropna(subset=['F(MHz)'])
        return expanded_df

    @st.cache_data
    def load_ntn_bands():
        return pd.read_csv("NR NTN Bands.csv")

    @st.cache_data
    def load_country_data():
        return pd.read_csv("wireless_network_technologies_bands_per_country.csv")

    df = load_main_data()
    ntn_df = load_ntn_bands()
    country_df = load_country_data()

    ntn_bands = ntn_df['Band'].dropna().unique()
    df['Is NTN Band'] = df['Band'].isin(ntn_bands)

    st.sidebar.header("🔍 Filter Options")
    tech_options = df['Tech'].dropna().unique()
    selected_tech = st.sidebar.multiselect("Select Technology", tech_options, default=tech_options)

    # Filter band options based on selected technologies
    filtered_band_options = df[df['Tech'].isin(selected_tech)]['Band'].dropna().unique()
    selected_band = st.sidebar.multiselect("Select Band", filtered_band_options, default=filtered_band_options)

    show_only_ntn = st.sidebar.checkbox("Show only NTN bands", value=False)

    if 'F(MHz)' in df.columns:
        f_min = int(df['F(MHz)'].min())
        f_max = int(df['F(MHz)'].max())
        selected_f_range = st.sidebar.slider(
            "Select Frequency Range (F(MHz))",
            min_value=f_min,
            max_value=f_max,
            value=(f_min, f_max),
            step=1
        )
    else:
        st.sidebar.error("Column 'F(MHz)' not found.")
        selected_f_range = (0, 0)

    filtered_df = df[
        (df['Tech'].isin(selected_tech)) &
        (df['Band'].isin(selected_band)) &
        (df['F(MHz)'] >= selected_f_range[0]) &
        (df['F(MHz)'] <= selected_f_range[1])
    ]

    if show_only_ntn:
        filtered_df = filtered_df[filtered_df['Is NTN Band']]

    def highlight_ntn(val):
        return 'background-color: #ffd700' if val else ''

    st.subheader("📄 Filtered Frequency Data")
    st.dataframe(filtered_df.style.applymap(highlight_ntn, subset=['Is NTN Band']), use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 Download Filtered Data as CSV",
        data=filtered_df.to_csv(index=False),
        file_name="filtered_frequency_data.csv",
        mime="text/csv"
    )

    # Map of band counts
    st.subheader("🗺️ Band Counts by Country")
    band_counts = (
        country_df.groupby(['Country', 'Latitude', 'Longitude'])
        .agg({'Band': 'nunique'})
        .reset_index()
        .rename(columns={'Band': 'Band Count'})
    )

    m = folium.Map(location=[20, 0], zoom_start=2)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in band_counts.iterrows():
        folium.Marker(
            [row['Latitude'], row['Longitude']],
            icon=folium.DivIcon(
                html=f"""<div style="font-size: 12px; color: white; background-color: #0073e6;
                         border-radius: 50%; width: 30px; height: 30px; text-align: center;
                         line-height: 30px;">{row['Band Count']}</div>"""
            ),
            tooltip=f"{row['Country']}: {row['Band Count']} bands"
        ).add_to(marker_cluster)

    components.html(m._repr_html_(), height=600, scrolling=False)

# ----------------- Technology Interfaces Tab -----------------
with tab2:
    st.title("🔗 Technology Interfaces")
    st.write("Interfaces flows between technology parts.")

    @st.cache_data
    def load_interface_data():
        df = pd.read_csv("Technology Interfaces.csv")
        df['Tech'] = df['Tech'].astype(str).str.strip()
        return df

    interface_df = load_interface_data()
    st.dataframe(interface_df, use_container_width=True)

    st.subheader("🔁 Interfaces")

    all_techs = sorted(interface_df['Tech'].dropna().unique())
    selected_tech = st.selectbox("Select Technology to View Interfaces", all_techs)

    tech_filtered_df = interface_df[interface_df['Tech'] == selected_tech]

    if tech_filtered_df.empty:
        st.info("No interfaces available for the selected technology.")
    else:
        fig, ax = plt.subplots(figsize=(10, max(4, len(tech_filtered_df) + 2)))

        ax.set_ylim(0, len(tech_filtered_df) + 1)
        ax.set_xlim(0, 10)

        for idx, row in tech_filtered_df.iterrows():
            y = list(tech_filtered_df.index).index(idx) + 1
            ax.plot([3, 7], [y, y], color='blue', lw=2)
            ax.text(5, y + 0.2, row['Interface'], fontsize=12, ha='center', va='bottom', color='red')
            ax.text(1, y, row['Part1'], fontsize=12, ha='center', color='black')
            ax.text(9, y, row['Part2'], fontsize=12, ha='center', color='black')

        ax.set_title(f"Interface Connections for {selected_tech}")
        ax.axis('off')
        st.pyplot(fig)

# ----------------- Data Sources -----------------
st.markdown("---")
st.markdown("#### 📚 Data Sources")
st.markdown("""
- [Frequency Bands for 2G, 3G, 4G and 5G](https://www.kaggle.com/datasets/yousefalf/frequency-bands-for-2g-3g-4g-and-5g)
- [Cellular Wireless Technologies Bands per Country](https://www.kaggle.com/datasets/yousefalf/cellular-wireless-technologies-bands)
- [NR NTN Bands](https://www.kaggle.com/datasets/yousefalf/nr-ntn-bands)
""")
