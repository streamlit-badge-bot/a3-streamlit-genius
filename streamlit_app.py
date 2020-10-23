import streamlit as st
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
import numpy as np
import pydeck as pdk
import plotly.express as px

st.beta_set_page_config(layout="wide")

st.title("Let's analyze Airbnb in Berlin")

@st.cache  # add caching so we load the data only once
def load_data():
    df_price_listings = pd.read_csv('data/price_listings.csv')
    df_price_superhost = pd.read_csv('data/price_superhost.csv')
    df_price_beds = pd.read_csv('data/price_beds.csv')
    df_price_neighborhood = pd.read_csv('data/price_neighborhood.csv')
    df_price_roomtype = pd.read_csv('data/price_roomtype.csv')
    df_price_availability = pd.read_csv('data/price_availability.csv')
    df_price_review = pd.read_csv('data/price_review.csv')
    df_availability90 = pd.read_csv('data/availability90.csv')
    with open('data/review_above_85.json') as f:
        word_freq_review_above_85 = json.load(f)
    wc_review_above_85 = WordCloud(background_color="white").generate_from_frequencies(word_freq_review_above_85)
    with open('data/availability90_above_60.json') as f:
        word_freq_avail_above_60 = json.load(f)
    wc_avail_above_60 = WordCloud(background_color="white").generate_from_frequencies(word_freq_avail_above_60)
    with open('data/availability90_below_20.json') as f:
        word_freq_avail_below_20 = json.load(f)
    wc_avail_below_20 = WordCloud(background_color="white").generate_from_frequencies(word_freq_avail_below_20)
    with open('data/price_above_100.json') as f:
        word_freq_price_above_100 = json.load(f)
    wc_price_above_100 = WordCloud(background_color="white").generate_from_frequencies(word_freq_price_above_100)
    with open('data/price_below_80.json') as f:
        word_freq_price_below_80 = json.load(f)
    wc_price_below_80 = WordCloud(background_color="white").generate_from_frequencies(word_freq_price_below_80)
    with open('data/review_below_85.json') as f:
        word_freq_review_below_85 = json.load(f)
    wc_review_below_85 = WordCloud(background_color="white").generate_from_frequencies(word_freq_review_below_85)
    df = pd.read_csv("data/listings.csv")
    df = df[["longitude","latitude", "accommodates", "price", "neighbourhood_group_cleansed"]]
    df["price"] = df["price"].str.replace(",", '').str.replace('$', '').astype(float)

    dfs = [df_price_listings, df_price_superhost, df_price_beds, 
           df_price_neighborhood, df_price_roomtype,
           df_price_availability, df_price_review, df_availability90, wc_review_above_85,
           wc_avail_above_60, wc_avail_below_20, wc_price_above_100, wc_price_below_80,
           wc_review_below_85, df]
    return dfs

def draw_price_charts(field_name, field_type, rename, df):
    selection = alt.selection_multi(empty='all', fields=[field_name])
    price_field_chart = alt.Chart(df).mark_line().encode(
        x = alt.X("date", type="temporal"),
        y = alt.Y("price", type="quantitative"),
        color = alt.condition(selection,
                    alt.Color(field_name, 
                        legend=alt.Legend(title=rename),
                        type=field_type),
                    alt.value('lightgray')),
        tooltip = [alt.Tooltip('date:T'),
                   alt.Tooltip('price:Q', format='$.2f')]
    ).properties(
        width=600, height=400
    ).interactive(
    ).add_selection(
        selection
    )

    field_chart = alt.Chart(df_price_listings).mark_bar().encode(
        x = alt.X(field_name, aggregate="count"),
        y = alt.Y(field_name, type=field_type, title=rename),
        color = alt.Color(field_name, 
                        legend=alt.Legend(title=rename), type=field_type),
        tooltip = [alt.Tooltip(field_name, type=field_type, title=rename),
                   alt.Tooltip(field_name, aggregate="count")]
    ).properties(
        width=400, height=200
    )

    st.write("**Click on a line to grey out others.**")
    st.write(price_field_chart)
    st.write(field_chart)

def draw_availability90_categories(df, upper_category, upper_type, upper_rename):
    brush = alt.selection_interval(encodings=["x", "y"])
    field_availability_chart = alt.Chart(df).transform_filter(
        brush
    ).transform_density(
        'availability_90',
        as_=['availability_90', 'density'],
        groupby=[upper_category]
    ).mark_area(orient='horizontal').encode(
        y=alt.Y('availability_90:Q', title='Availability in 90 Days'),
        color=alt.Color(upper_category, type=upper_type, legend = alt.Legend(title=upper_rename)),
        x=alt.X(
            'density:Q',
            stack='center',
            impute=None,
            title=None,
            axis=alt.Axis(labels=False, values=[0], grid=False, ticks=True),
        ),
        column=alt.Column(
            upper_category,
            type=upper_type,
            header=alt.Header(
                titleOrient = 'bottom',
                labelOrient = 'bottom',
                labelPadding = 0,
                title = upper_rename
            )
        ),
        tooltip = [alt.Tooltip('availability_90:Q')]
    ).properties(
        width=200
    ).interactive()

    scatterplot = alt.Chart(df[df['price'] < 500]
    ).mark_circle(size=100).encode(
        alt.X("price"),
        alt.Y("review_scores_rating", scale=alt.Scale(zero=False), title='review score'),
        tooltip = [alt.Tooltip('price', format='$.2f'),
                   alt.Tooltip('review_scores_rating', title='Review Score')]
    ).add_selection(brush)

    st.write("**Brush through the lower scatterplot to filter the upper chart by review score and price.**")
    st.write(field_availability_chart & scatterplot)
    

def draw_availability90_quantitative(df, upper_quant, upper_type, upper_rename):
    brush = alt.selection_interval(encodings=["x", "y"])
    field_availability_chart = alt.Chart(df).transform_filter(
        brush
    ).mark_circle(size=60).encode(
        alt.X(upper_quant, title=upper_rename),
        alt.Y("availability_90", title="Availability in 90 Days"),
        tooltip=[alt.Tooltip(upper_quant, title=upper_rename),
                 alt.Tooltip("availability_90", title="Availability in 90 Days")]
    ).interactive()

    scatterplot = alt.Chart(df[df['price'] < 500]
    ).mark_circle(size=100).encode(
        alt.X("price"),
        alt.Y("review_scores_rating", scale=alt.Scale(zero=False), title='review score'),
        tooltip = [alt.Tooltip('price', format='$.2f'),
                   alt.Tooltip('review_scores_rating', title='Review Score')]
    ).add_selection(brush)

    st.write("**Brush through the lower scatterplot to filter the upper chart by review score and price.**")
    st.write(field_availability_chart & scatterplot)
    

def plot_word_cloud(wc, msg):
    st.image(wc.to_array())
    st.write(msg)

# Creating maps
def map(data, lat, lon, zoom):
    st.write(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state={
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "pitch": 45,
            "bearing": 0,
        },

        layers=[
            pdk.Layer(
                "GridLayer",
                data=data,
                get_position=["longitude", "latitude"],
                radius=100,
                elevation_scale=4,
                cell_size=300,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
                #
            ),
        ],
        tooltip={
            "html": "<b>Number of Airbnb:</b> {elevationValue}",
            "style": {
                "backgroundColor": "white",
                "color": "#B2C248"
            }}
    ))


dfs = load_data()
df_price_listings = dfs[0]
df_price_superhost = dfs[1]
df_price_beds = dfs[2]
df_price_neighborhood = dfs[3]
df_price_roomtype = dfs[4]
df_price_availability = dfs[5]
df_price_review = dfs[6]
df_availability90 = dfs[7]
wc_review_above_85 = dfs[8]
wc_avail_above_60 = dfs[9]
wc_avail_below_20 = dfs[10]
wc_price_above_100 = dfs[11]
wc_price_below_80 = dfs[12]
wc_review_below_85 = dfs[13]
df = dfs[14]

st.header("**Berlin Airbnb Geographic Distribution**")
st.subheader("Number of Airbnb based on accommodation size in the Berlin map")
st.markdown(
        "We would like to check the popularity of Airbnb in different districts in Berlin. Four specific areas we picked are Mitte, Charlottenburg, Kreuzberg, and Lichtenberg. By sliding the slider, you could see the number of Airbnb change based on the size of the accommondation."
    )
size_of_accommodation = st.slider("Size of accommodation (The number of people that could stay)", 1, 12, 3)
filter_accommodates = df[df["accommodates"] == size_of_accommodation]

# LAYING OUT THE MIDDLE SECTION OF THE APP WITH THE MAPS

# my_expander=st.beta_expander()
# my_expander.write(row2_1)

row2_1, row3_1, row3_2, row3_3, row3_4 = st.beta_columns((3, 1, 1, 1, 1))


# SETTING THE ZOOM LOCATIONS FOR THE AIRPORTS
Mitte = [52.54425, 13.39749]
Charlottenburg = [52.51968, 13.30209]
Friedrichshain_Kreuzberg = [52.49847, 13.44013]
Lichtenberg = [52.4766, 13.50838]
zoom_level = 12
midpoint = (np.average(df["latitude"]), np.average(df["longitude"]))

# size_of_accommodation = st.slider("Size of accommodation (The number of people that could stay)", 1, 12, 3)
# filter_accommodates = df[df["accommodates"] == size_of_accommodation]

with row2_1:
    st.write("All Berlin Airbnb")
    filter_accommodates = filter_accommodates[['longitude','latitude']]
    map(filter_accommodates, midpoint[0], midpoint[1], 11)

with row3_1:
    st.write("**Mitte**")
    map(filter_accommodates, Mitte[0], Mitte[1], zoom_level)

with row3_2:
    st.write("**Charlottenburg**")
    map(filter_accommodates, Charlottenburg[0], Charlottenburg[1], zoom_level)

with row3_3:
    st.write("**Friedrichshain_Kreuzberg**")
    map(filter_accommodates, Friedrichshain_Kreuzberg[0], Friedrichshain_Kreuzberg[1], zoom_level)

with row3_4:
    st.write("**Lichtenberg**")
    map(filter_accommodates, Lichtenberg[0], Lichtenberg[1], zoom_level)


# Histogram
accommodates_counts = df["accommodates"].value_counts().sort_index()[1:13]
bins = accommodates_counts.index

f = px.bar(x=bins, y=accommodates_counts, labels={'x':'Size of accommodation', 'y':'Number of Airbnb'},opacity=0.5)
st.markdown("We moved the 3D charts to 2D histograms to have a more direct view of the number of Airbnb based on accommodation size.")
st.plotly_chart(f)




# Violin plot -- relationship between neighborhood and its price
density_chart = alt.Chart(df).transform_density(
    "price",
    as_=["price","density"],
    extent=[0,200],
    groupby=["neighbourhood_group_cleansed"]
).mark_area(orient="horizontal").encode(
    # x="neighbourhood_group_cleansed:N",
    y=alt.Y("price:Q", title= "Price of Airbnb"),
    color="neighbourhood_group_cleansed:N",
    x=alt.X(
        'density:Q',
        stack='center',
        impute=None,
        title=None,
        axis=alt.Axis(labels=False, values=[0],grid=False, ticks=True),
    ),
    column=alt.Column(
        "neighbourhood_group_cleansed:N",
        header=alt.Header(
            titleOrient='bottom',
            labelOrient='bottom',
            labelPadding=0,
        ),
        title="Neighborhood"
    )
).properties(
    width=100
).interactive()

st.markdown("We also want to explore the price of Airbnb among different neighborhoods.")
st.altair_chart(density_chart)



st.header("**How to set the Price**")
price_dimensions = ["Superhost", "Neighborhood", "Number of Beds", "Roomtype",
                    "Room with Availability in 365 Days", "Review Score"]
price_dim = st.selectbox('Explore Price By ', price_dimensions)

if price_dim == "Superhost":
    draw_price_charts("host_is_superhost", "nominal", "Superhost", df_price_superhost)

elif price_dim == "Neighborhood":
    draw_price_charts("neighbourhood_group_cleansed", "nominal", "Neighborhood", df_price_neighborhood)

elif price_dim == "Number of Beds":
    draw_price_charts("beds", "nominal", "Number of Beds", df_price_beds)

elif price_dim == "Roomtype":
    draw_price_charts("room_type", "nominal", "Roomtype", df_price_roomtype)

elif price_dim == "Room with Availability in 365 Days":
    draw_price_charts("availability_365", "nominal", "Availability", df_price_availability)

elif price_dim == "Review Score":
    draw_price_charts("review_scores_rating", "nominal", "Review Scores", df_price_review)

st.header("**How to Decrease Availability in 90 Days**")

avail90_dimensions = ["Superhost", "Neighborhood", "Host Acceptance Rate", "Host Response Time",
                    "Host Identity Verified", "Number of Reviews",
                    "Instant Bookable", "Price", "Review Score"]
avail90_dim = st.selectbox('Explore Availability in 90 Days By ', avail90_dimensions)

if avail90_dim == "Superhost":
    draw_availability90_categories(df_availability90, "host_is_superhost", "nominal", "Superhost")
elif avail90_dim == "Neighborhood":
    draw_availability90_categories(df_availability90, "neighbourhood_group_cleansed", "nominal", "Neighborhood")
elif avail90_dim == "Host Acceptance Rate":
    draw_availability90_quantitative(df_availability90, "host_acceptance_rate", "Q", "Host Acceptance Rate")
elif avail90_dim == "Host Response Time":
    draw_availability90_categories(df_availability90[df_availability90["host_response_time"].notna()], "host_response_time", "nominal", "Host Response Time")
elif avail90_dim == "Host Identity Verified":
    draw_availability90_categories(df_availability90, "host_identity_verified", "nominal", "Host Identity Verified")
elif avail90_dim == "Number of Reviews":
    draw_availability90_quantitative(df_availability90, "number_of_reviews", "Q", "Number of Reviews")
elif avail90_dim == "Instant Bookable":
    draw_availability90_categories(df_availability90, "instant_bookable", "nominal", "Instant Bookable")
elif avail90_dim == "Price":
    draw_availability90_quantitative(df_availability90, "price", "Q", "Price")
elif avail90_dim == "Review Score":
    draw_availability90_quantitative(df_availability90, "review_scores_rating", "Q", "Review Score")

st.header("**What Customers Say**")

cmt_dimensions = ["Review Score", "Availability in 90 Days", "Price"]
cmt_dim = st.selectbox('Look at What Customers Say for Airbnb By Room\'s ', cmt_dimensions)

if cmt_dim == "Review Score":
    plot_word_cloud(wc_review_above_85, "Airbnb with Review >= 85")
    plot_word_cloud(wc_review_below_85, "Airbnb with Review < 85")
elif cmt_dim == "Availability in 90 Days":
    plot_word_cloud(wc_avail_above_60, "Airbnb with Availability >= 60")
    plot_word_cloud(wc_avail_below_20, "Airbnb with Availability <= 20")
elif cmt_dim == "Price":
    plot_word_cloud(wc_price_above_100, "Airbnb with Price >= 100")
    plot_word_cloud(wc_price_below_80, 'Airbnb with Price <= 80')
    














