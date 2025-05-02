import json
import logging
import preswald
import pandas as pd
import plotly.express as px

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

preswald.text("# Welcome to Shaking Lens!")
preswald.text("This project analyzes and visualizes projected wildfire risks across regions in Los Angeles " \
              "using climate model data under different timeframes and scenarios (2020, 2050, and 2080). " \
              "By leveraging geospatial data and predictive indicators like annual hectares burned, " \
              "it presents interactive visualizations, including geospatial maps, bar charts, scatter plots, "
              "and histograms, to highlight how wildfire risk is tackled over time. These insights can help policymakers, " \
              "researchers, and the public better understand regional risk patterns and prepare for climate-driven " \
              "fire hazards in the coming decades.")

# Adding a sidebar
preswald.sidebar(defaultopen=True)

# Loading the Data
preswald.connect()
df_name = 'wildfire_rcp_dataset'
df = preswald.get_df(df_name)

# Visualizing the Data
preswald.text("## Data Visualization")

with open("data/Wildfire_RCP_Dataset.geojson") as f:
    geojson_data = json.load(f)

def classify_risk(val):
    if val > 30:
        return "High"
    elif val > 10:
        return "Moderate"
    else:
        return "Low"

color_map = {
    "High": "darkred",
    "Moderate": "orange",
    "Low": "green"
}

workflow = preswald.Workflow()

@workflow.atom()
def select_year():
    logger.info("Selecting year")
    
    year = preswald.slider("Select an Year", min_val=2020, max_val=2080, default=2050, step=30)
    preswald.text("Please allow a few seconds for the graphs to reload.")
    
    return year

@workflow.atom(dependencies=['select_year'])
def update_df(select_year):
    logger.info(f"Showing map for year: {select_year}")

    # Preprocessing the Data
    df_new = df.copy()
    df_new = df_new.dropna()
    df_new = df_new.drop_duplicates()
    year_col = f"F_{select_year}" if select_year != 2020 else "Baseline"
    df_new[year_col] = pd.to_numeric(df_new[year_col], errors='coerce')
    df_new = df_new.dropna(subset=[year_col]) # Drop rows with NaN in the year column
    df_new["Risk_Level"] = df_new[year_col].apply(classify_risk)
    
    return df_new

@workflow.atom(dependencies=['update_df', 'select_year'], force_recompute=True)
def plot_map(update_df, select_year):
    logger.info("Plotting map")
    
    if update_df is None or len(update_df) == 0:
        return preswald.spinner("Loading wildfire risk map...", variant="card")
    
    preswald.text("### Geospatial Map Plot")

    # Plotting the map
    fig = px.choropleth(
        data_frame=update_df,
        geojson=geojson_data,
        locations="Geo_UID",
        featureidkey="properties.Geo_UID",
        color="Risk_Level",
        color_discrete_map=color_map,
        title=f"Projected Wildfire Risk in Los Angeles ({select_year})",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    preswald.plotly(fig)

    preswald.text("#### While the projected wildfire risk decreases geographically across many regions between 2020 and 2080, there is still scope for improvement in several remaining areas that require further planning to become low-risk zones.")
    
    return 

@workflow.atom(dependencies=['update_df', 'select_year'])
def plot_bar(update_df, select_year):
    logger.info("Plotting bar chart")

    if update_df is None or len(update_df) == 0:
        return preswald.spinner("Loading wildfire risk data...", variant="card")
    
    year_col = f"F_{select_year}" if select_year != 2020 else "Baseline"
    
    df_bar = df[["Geo_UID", year_col]].dropna()
    df_bar = df_bar.rename(columns={year_col: "Annual_Hectares_Burned"})
    
    preswald.text("### Bar Plot")

    # Creating the bar plot
    fig = px.bar(
        df_bar,
        x="Geo_UID",
        y="Annual_Hectares_Burned",
        title=f"Wildfire Risk by Region in {select_year}",
        labels={"Annual_Hectares_Burned": "Hectares Burned"},
    )
    
    preswald.plotly(fig)
    
    preswald.text("#### Regions with higher wildfire risk levels show significantly larger average hectares burned annually, especially under future projections.")
    
    return 


@workflow.atom(dependencies=['update_df', 'select_year'])
def plot_scatter(update_df, select_year):
    logger.info("Plotting scatter plot")
    
    if update_df is None or len(update_df) == 0:
        return preswald.spinner("Loading wildfire risk data...", variant="card")
    
    year_col = f"F_{select_year}" if select_year != 2020 else "Baseline"
    df_scatter = df[["longitude", "latitude", year_col]].dropna()
    df_scatter = df_scatter.rename(columns={year_col: "Annual_Hectares_Burned"})
    df_scatter["Annual_Hectares_Burned"] = pd.to_numeric(df_scatter["Annual_Hectares_Burned"], errors='coerce')
    df_scatter = df_scatter.dropna(subset=["Annual_Hectares_Burned"]) # Drop rows with NaN in the Annual_Hectares_Burned column

    df_scatter["Size"] = df_scatter["Annual_Hectares_Burned"].clip(lower=0)

    preswald.text("### Scatter Plot")

    # Creating scatter plot
    fig = px.scatter(
        df_scatter,
        x="longitude",
        y="latitude",
        size="Size",
        color="Annual_Hectares_Burned",
        title=f"Spatial Distribution of Wildfire Risk in {select_year}",
        labels={"Annual_Hectares_Burned": "Hectares Burned"},
    )

    preswald.plotly(fig)
    
    preswald.text("#### There's a visible downward trend in annual hectares burned from Baseline to 2080, particularly in regions with medium to high risk indicating that higher priority regions were targetted for balance.")

    return 

@workflow.atom(dependencies=['update_df'])
def plot_histogram(update_df):
    logger.info("Plotting histogram")
    
    if update_df is None or len(update_df) == 0:
        return preswald.spinner("Loading wildfire risk data...", variant="card")
    
    df_hist = df[["Baseline", "F_2050", "F_2080"]].dropna()
    df_hist = df_hist.melt(var_name="Year", value_name="Risk")
    
    preswald.text("### Histogram Plot")
    
    # Creating histogram
    fig = px.histogram(
        df_hist,
        x="Risk",
        color="Year",
        barmode="overlay",
        nbins=50,
        title="Wildfire Risk Distribution Across Years",
        labels={"Risk": "Hectares Burned"},
    )

    preswald.plotly(fig)

    preswald.text('#### The distribution of hectares burned becomes more left-skewed over time, indicating more regions with extreme fire sizes in 2020 as opposed to 2050 and 2080.')

    return

# Run the workflow
workflow.execute()