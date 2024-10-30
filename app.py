import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.figure_factory as ff

# --- Page Configuration --- #
st.set_page_config(
    page_title='Store',
    page_icon=':bar_chart:',
    layout='wide'
)

# --- Main Page --- #
st.title(':bar_chart: Store')
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# --- Gets the Data to be used --- #
@st.cache_data
def get_data_from_excel():
    df = pd.read_excel(
        io="Sample - Superstore.xls",
        engine='xlrd'
    )
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    return df


df = get_data_from_excel()

# --- Sidebar Page --- #

st.sidebar.header('Filters: ')

# -- Select the start and end date -- #
startDate = pd.to_datetime(df["Order Date"]).min()
endDate = pd.to_datetime(df["Order Date"]).max()

start_date = pd.to_datetime(st.sidebar.date_input('Start Date', startDate))
end_date = pd.to_datetime(st.sidebar.date_input('End Date', endDate))

# -- Modifies the elements according to the selected dates --- #
df = df[(df['Order Date'] >= start_date) & (df['Order Date'] <= end_date)].copy()

# -- Select the region of your interest -- #
region = st.sidebar.multiselect(
    'Choose the region',
    df['Region'].unique()
)
if not region:
    df2 = df.copy()
else:
    df2 = df[df['Region'].isin(region)]

# -- Select the state of your interest -- #
state = st.sidebar.multiselect(
    'Choose the state',
    df2['State'].unique()
)
if not state:
    df3 = df2.copy()
else:
    df3 = df2[df2["State"].isin(state)]

# -- Select the City of your interest -- #
city = st.sidebar.multiselect(
    'Choose the City',
    df3['City'].unique()
)

# Filter the data based on Region, State and City
if not region and not state and not city:
    filtered_df = df
elif not state and not city:
    filtered_df = df[df["Region"].isin(region)]
elif not region and not city:
    filtered_df = df[df["State"].isin(state)]
elif state and city:
    filtered_df = df3[df["State"].isin(state) & df3["City"].isin(city)]
elif region and city:
    filtered_df = df3[df["Region"].isin(region) & df3["City"].isin(city)]
elif region and state:
    filtered_df = df3[df["Region"].isin(region) & df3["State"].isin(state)]
elif city:
    filtered_df = df3[df3["City"].isin(city)]
else:
    filtered_df = df3[df3["Region"].isin(region) & df3["State"].isin(state) & df3["City"].isin(city)]

# --- Analysis here --- #

# Select the category and group with the sum of the sales of each category
category_df = filtered_df.groupby(by=['Category'],as_index=False)['Sales'].sum()

# -- Create columns -- #
left_col, right_col, = st.columns(2)

with left_col:
    st.subheader('Category wise Sales')
    fig_category_sales = px.bar(
        data_frame=category_df,
        x='Category',
        y='Sales',
        text=['${:,.2f}'.format(x) for x in category_df['Sales']],
        template='seaborn'
    )
    st.plotly_chart(fig_category_sales,use_container_width=True)

with right_col:
    st.subheader('Region wise Sales')
    fig_region_sales = px.pie(
        data_frame=filtered_df,
        values='Sales',
        names='Region'
    )
    fig_region_sales.update_traces(
        text = filtered_df['Region'],
        textposition = 'inside'
    )
    st.plotly_chart(fig_region_sales, use_container_width=True)

st.markdown('---')

st.subheader('Year-month sales')

# --- Select period by year-month --- #
filtered_df['month_year'] = filtered_df['Order Date'].dt.to_period('M')

# --- Make a dataframe grouped by year and month by the sum of sales --- #
linechart = pd.DataFrame(
    filtered_df.groupby(by=filtered_df['month_year'].dt.strftime('%Y : %b'))['Sales'].sum()
).reset_index()

fig_times_series = px.line(
    data_frame=linechart,
    x='month_year',
    y='Sales',
    labels={'Sales': 'Amount', 'month_year': 'year-month'},
    template='gridon'
)
st.plotly_chart(fig_times_series, use_container_width=True)

st.markdown('---')


left_col,right_col = st.columns(2)


# -- Groups total sales and profit by segment -- #
revenue_by_segment = filtered_df.groupby(by=['Segment'])[['Sales','Profit']].sum().reset_index()
# -- Calculates the cost per segment -- #
revenue_by_segment['Cost'] = revenue_by_segment['Sales'] - revenue_by_segment['Profit']

# -- Melt the DataFrame to make it easier to create the graph -- #
melted_df = revenue_by_segment.melt(id_vars='Segment', value_vars=['Sales', 'Cost', 'Profit'], 
                                    var_name='Metric', value_name='Amount')

with left_col:
    st.subheader('Financial situation by segment')
    fig_segment_situation = px.bar(
        melted_df,
        x='Segment',
        y='Amount',
        color='Metric',
        labels={'Segment': 'Segment', 'Amount': 'Amounts'},
        barmode='group'
    )
    st.plotly_chart(fig_segment_situation, use_container_width=True)

# -- Groups total sales by region and segment and counting the number of orders -- #
reg_seg_ticket = filtered_df.groupby(by=['Segment','Region']).agg(
    Total_Sales=('Sales','sum'),
    Order_Count=('Order ID', 'nunique')
).reset_index()

# -- Calculate the average ticket -- #
reg_seg_ticket['Average_Ticket'] = reg_seg_ticket['Total_Sales'] / reg_seg_ticket['Order_Count']

with right_col:
    st.subheader('Average sales')
    fig_average_sales_reg_seg = px.bar(
        reg_seg_ticket, 
        x='Region', 
        y='Average_Ticket', 
        color='Segment', 
        barmode='group',  # Place grouped bars
        text='Average_Ticket'  # Add the average ticket values to the bars
    )
    # Layout adjustments to improve visualization
    fig_average_sales_reg_seg.update_traces(texttemplate='%{text:.2f}', textposition='outside')  # Format the text and place it outside the bar
    fig_average_sales_reg_seg.update_layout(
        xaxis_title='Region',
        yaxis_title='Average Ticket ($)',
        legend_title='Segment',
        yaxis=dict(showgrid=True, gridcolor='LightGray'),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_average_sales_reg_seg, use_container_width=True)

st.markdown('---')


left_col,right_col = st.columns(2)

# -- Makes a group of customers grouped by purchases and id -- #
frequency_of_purchase = filtered_df.groupby(by=['Customer ID', 'Customer Name']).agg({
    'Order ID': 'nunique',
    'Sales': 'sum'
}).rename(columns={'Order ID': 'Purchase Frequency', 'Sales': 'Total Sales'}).reset_index()

with left_col:
    st.subheader('Frequency of customer purchases')
    customer_purchase_frequency = px.histogram(
        data_frame=frequency_of_purchase,
        x='Purchase Frequency'
    )
    # Ajustar transparência e layout
    customer_purchase_frequency.update_traces(opacity=0.8)  # Ajustar a transparência
    customer_purchase_frequency.update_layout(
        xaxis_title='Purchase Frequency',
        yaxis_title='Number of Clients',
        xaxis=dict(tickmode='linear'),  # Mostrar cada valor de frequência
        plot_bgcolor='rgba(0,0,0,0)',  # Remover fundo cinza
        yaxis=dict(showgrid=True, gridcolor='LightGray')  # Grid leve para guiar a visualização
    )
    st.plotly_chart(customer_purchase_frequency, use_container_width=True)

# -- Calculate the average ticket -- #
frequency_of_purchase['Average Ticket'] = frequency_of_purchase['Total Sales'] / frequency_of_purchase['Purchase Frequency']
with right_col:
    st.subheader('Top clients')
    fig_top_clients = px.bar(frequency_of_purchase.sort_values(by='Average Ticket', ascending=False).head(5),
                        x='Customer Name', y='Average Ticket',
    )
    st.plotly_chart(fig_top_clients,use_container_width=True)
# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """

st.markdown(hide_st_style, unsafe_allow_html=True)