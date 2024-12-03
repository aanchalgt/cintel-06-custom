from faicons import icon_svg
import faicons as fa
import plotly.express as px
from shinywidgets import render_plotly, render_widget, output_widget
import random
from shiny import reactive, render
from datetime import datetime
import pandas as pd
from shiny import reactive, render, req
from shiny.express import input, ui, render
from collections import deque
from scipy import stats
from statsmodels.api import OLS, add_constant
from pathlib import Path  

UPDATE_INTERVAL_SECS: int = 10
DEQUE_SIZE: int = 10
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# Import icons from faicons ----------------------------------------------------------------------
ICONS = {
    "credit-card": fa.icon_svg("money-bill"),   # Changed to money-bill
    "person": fa.icon_svg("user"),               # Changed to user
    "currency-dollar": fa.icon_svg("coins"),     # Changed to coins
}

# Corrected file path
#infile = Path(""C:\Users\heath\OneDrive\Desktop\Anny\MS-DA\cintel-06-custom\dashboard\tips.csv"")

# Read the CSV file
#tips = pd.read_csv(infile)

tips = px.data.tips()  # Load tipping dataset

ui.HTML("<h1 style='font-size: 3em; color: darkblue; font-weight: bold; text-align: center;background-color: yellow;'>Restaurant Tips Analysis</h1>")

# Sidebar with Inputs ----------------------------------------------------------------------------
with ui.sidebar(open="open"):
    ui.h5("Custom Filters and Options")

    # Filter for day of the week
    ui.input_checkbox_group(
        "selected_day", 
        label="Select Day", 
        choices=["Thur", "Fri", "Sat", "Sun"], 
        selected=["Thur", "Fri", "Sat", "Sun"], 
        inline=True
    )
    
    # Filter for gender
    ui.input_checkbox_group(
        "selected_gender", 
        label="Select Gender", 
        choices=["Male", "Female"], 
        selected=["Male", "Female"], 
        inline=True
    )

    # Filter for smoker
    ui.input_checkbox_group(
        "selected_smoker", 
        label="Smoker", 
        choices=["No", "Yes"], 
        selected=["No", "Yes"], 
        inline=True
    )

    # Filter for dining time
    ui.input_radio_buttons(
        "selected_time",
        "Select Dining Time",
        choices=["Dinner", "Lunch"],
        selected="Dinner",
        inline=True
    )

    # Range slider for total bill
    ui.input_slider("total_bill_range", "Total Bill Range ($)", 0, 50, (10, 30))

# Live data
with ui.layout_columns(fill=False):
    with ui.value_box(
        showcase=ICONS["person"],
        theme="bg-gradient-blue-red", height=200
    ):
        "Total Persons"
        @render.text
        def total_persons():
            filtered = filtered_data()  # Using the filtered data function based on user inputs
            total_count = len(filtered)  # This counts the rows in the filtered dataset
            return f"{total_count} Persons"
       

    # Total revenue (updated value box to show total revenue)
    with ui.value_box(
        showcase=ICONS["currency-dollar"],
        theme="bg-gradient-green-blue", height=200
    ):
        "Total Revenue"
        @render.text
        def total_revenue():
            # Calculate total revenue from the filtered data
            total_revenue_value = filtered_data()["total_bill"].sum()  # Sum of total bills
            return f"${total_revenue_value:.2f}"

    # Total tips for girls
    with ui.value_box(
        showcase=ICONS["credit-card"],
        theme="bg-gradient-orange-red", height=200
    ):
        "Girls' Tips"
        @render.text
        def display_gtip():
            _, df, _ = reactive_tips_combined()
            return f"${df['girlamnt'].sum():.2f}"

    # Total tips for boys
    with ui.value_box(
        showcase=ICONS["currency-dollar"],
        theme="bg-gradient-green-blue", height=200
    ):
        "Boys' Tips"
        @render.text
        def display_btip():
            _, df, _ = reactive_tips_combined()
            return f"${df['boyamnt'].sum():.2f}"        

# Data Table and Visualizations ------------------------------------------------------------------
with ui.layout_columns(fill=False):
    # Data Table
    with ui.card():
        "Filtered Tipping Data"
        @render.data_frame
        def tipping_df():
            return render.DataTable(filtered_data(), selection_mode='row')

    # Scatterplot with regression line
    with ui.card(full_screen=True):
        ui.card_header("Scatterplot: Total Bill vs Tip")
        @render_plotly
        def scatterplot_with_regression():
            filtered = filtered_data()
            fig = px.scatter(
                filtered,
                x="total_bill",
                y="tip",
                color="sex",  # Using the 'sex' column, can be replaced with another column
                labels={"total_bill": "Total Amount ($)", "tip": "Gratuity ($)"},  # Modified labels
                title="Scatterplot: Total Amount vs Gratuity"  # Modified title
            )
            return fig

    with ui.card(full_screen=True):
        ui.card_header("Bar chart: Group by day vs Tip")
        @render_plotly
        def barchart():
            filtered = filtered_data()
            day_tips = filtered.groupby("day")["tip"].sum().reset_index()
            fig = px.bar(
                day_tips,
                x="day",
                y="tip",
                labels={"day": "Day", "tip": "Total Tips ($)"},
                title="Total Tips by Day of the Week"
            )
            return fig

# Reactive Functions -----------------------------------------------------------------------------
@reactive.calc
def filtered_data():
    req(input.selected_day(), input.selected_gender(), input.selected_smoker, input.selected_time)
    
    # Filter the dataset based on the user inputs, removing the 'region' filter
    filtered_tips = tips[
        (tips["day"].isin(input.selected_day())) &
        (tips["sex"].isin(input.selected_gender())) &
        (tips["smoker"].isin(input.selected_smoker())) &
        (tips["time"] == input.selected_time()) &
        (tips["total_bill"].between(*input.total_bill_range()))
    ]
    return filtered_tips

def reactive_tips_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)
    tip_value_girls = round(random.uniform(1, 50), 1)
    tip_value_boys = round(random.uniform(1, 50), 1)
    timestamp_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = {"girlamnt": tip_value_girls, "boyamnt": tip_value_boys, "timestamp": timestamp_value}
    reactive_value_wrapper.get().append(new_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)
    return deque_snapshot, df, new_entry
