import streamlit as st
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json

st.beta_set_page_config(layout="centered")

st.title("Let's analyze Airbnb in Berlin")

@st.cache  # add caching so we load the data only once
def load_data():
    # Load the penguin data from https://github.com/allisonhorst/palmerpenguins.
    # penguins_url = "https://raw.githubusercontent.com/allisonhorst/palmerpenguins/v0.1.0/inst/extdata/penguins.csv"
    # return pd.read_csv(penguins_url)
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

    dfs = [df_price_listings, df_price_superhost, df_price_beds, 
           df_price_neighborhood, df_price_roomtype,
           df_price_availability, df_price_review, df_availability90, wc_review_above_85,
           wc_avail_above_60, wc_avail_below_20, wc_price_above_100, wc_price_below_80,
           wc_review_below_85]
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

    st.write(field_availability_chart & scatterplot)

def plot_word_cloud(wc, msg):
    st.image(wc.to_array())
    st.write(msg)
    # fig = plt.imshow(wc, interpolation='bilinear')
    # plt.axis("off")
    # # plt.show()
    # st.pyplot(fig)


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

st.write("**Price**")
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

st.write("**Availability**")

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

st.write("**What Customers Say**")

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
    














