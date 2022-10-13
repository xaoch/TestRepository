import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("School Data")

schoolData = pd.read_csv("data/schoolData.csv")
frpl = pd.read_csv("data/frpl.csv")

# Cleaning Data
# Keeping only totals
mask = schoolData["school_group"].isnull()
schoolData = schoolData[mask]

# Remove some columns
schoolData = schoolData.drop(columns=["school_group", "grade", "pi_pct", "blank_col"])

# Remove Grand Total
mask = schoolData["school_name"] != "Grand Total"
schoolData = schoolData[mask]

#schoolData =schoolData.drop(schoolData.tail(1).index)

# Remove Total from names
schoolData["school_name"]= schoolData["school_name"].str.replace("Total","")

# Remove trailing spaces
schoolData["school_name"]= schoolData["school_name"].str.strip()

# Remove percentage teo
def convertToNumber(column):
    column=column.str.replace("%","")
    column=pd.to_numeric(column)
    return column

schoolData["aa_pct"]=convertToNumber(schoolData["aa_pct"])
schoolData["na_pct"]=convertToNumber(schoolData["na_pct"])
schoolData["as_pct"]=convertToNumber(schoolData["as_pct"])
schoolData["hi_pct"]=convertToNumber(schoolData["hi_pct"])
schoolData["wh_pct"]=convertToNumber(schoolData["wh_pct"])

# FRPL dataset

# Remove NA from name
mask = ~frpl["school_name"].isnull()
frpl = frpl[mask]

frpl["frpl_pct"]=convertToNumber(frpl["frpl_pct"])

## Data Wrangling

# Joining datasets

joinedDataset = schoolData.merge(frpl,on="school_name",how="left")

# Calculate high_poverty
joinedDataset = joinedDataset.assign(high_poverty = lambda x: x.frpl_pct>75)

## Interface

st.sidebar.title("Controls")

visualization=st.sidebar.radio("Select the visualization",
                 options=["General Population","Percentage of Poverty","Race/Ethnicity and Poverty","Histogram of Percentages"])

sizeRange=st.sidebar.slider("Select the size of the schools:",
                            min_value=int(joinedDataset["tot"].min()),
                            max_value=int(joinedDataset["tot"].max()),
                            value=(int(joinedDataset["tot"].min()),int(joinedDataset["tot"].max())))


#Filter Dataset

mask=joinedDataset["tot"].between(sizeRange[0],sizeRange[1])
joinedDataset=joinedDataset[mask]

## Select Schools
selectedSchools=st.sidebar.multiselect("Select the schools to be included:",
                                       options=joinedDataset["school_name"].unique(),
                                       default=joinedDataset["school_name"].unique())

# Filter Data
mask=joinedDataset["school_name"].isin(selectedSchools)
joinedDataset=joinedDataset[mask]

# Wrangle the DAta for populations
SchoolData_population = joinedDataset.melt(
    id_vars=['school_name', 'high_poverty'], # column that uniquely identifies a row (can be multiple)
    value_vars=['na_num','aa_num','as_num','hi_num','wh_num'],
    var_name='race_ethnicity', # name for the new column created by melting
    value_name='population' # name for new column containing values from melted columns
)

SchoolData_population["race_ethnicity"]= SchoolData_population["race_ethnicity"].replace("na_num","Native American")
SchoolData_population["race_ethnicity"]= SchoolData_population["race_ethnicity"].replace("aa_num","African American")
SchoolData_population["race_ethnicity"]= SchoolData_population["race_ethnicity"].replace("as_num","Asian American")
SchoolData_population["race_ethnicity"]= SchoolData_population["race_ethnicity"].replace("hi_num","Hispanic")
SchoolData_population["race_ethnicity"]= SchoolData_population["race_ethnicity"].replace("wh_num","White")

population_summary = SchoolData_population.groupby("race_ethnicity").sum()



#Visualization "General Pop"
if visualization=="General Population":
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(SchoolData_population, values='population', names='race_ethnicity',
                     title='Population Percentage per Race')
        st.plotly_chart(fig)

    with col2:
        fig2 = px.bar(population_summary, x=population_summary.index, y='population')
        st.plotly_chart(fig2)
    
if visualization=="Percentage of Poverty":
    fig = px.pie(joinedDataset, names='high_poverty')
    st.plotly_chart(fig)

if visualization=="Race/Ethnicity and Poverty":
    st.write(SchoolData_population)
    fig = px.pie(SchoolData_population, values='population', names='race_ethnicity', facet_col="high_poverty",
                 title='Population Percentage per Race')
    st.plotly_chart(fig)

if visualization=="Histogram of Percentages":
    st.write(joinedDataset)
    fig = px.histogram(joinedDataset, x="aa_pct", color="high_poverty", marginal="rug",
                       title="African American Percentage", width=1200)
    # Overlay both histograms
    fig.update_layout(barmode='overlay')
    # Reduce opacity to see both histograms
    fig.update_traces(opacity=0.75)
    st.plotly_chart(fig)
