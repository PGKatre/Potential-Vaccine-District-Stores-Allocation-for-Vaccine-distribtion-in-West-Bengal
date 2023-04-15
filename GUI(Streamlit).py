import gurobipy as gp
from gurobipy import *
import math
import pandas as pd
import streamlit as st
import plotly.express as px
import time
import folium
from streamlit_folium import folium_static



# Load data
Distance_Matrix = pd.read_excel("C:/Users/Palak/OneDrive/Desktop/ISP_Dataset.xlsx", sheet_name="Distance Matrix")
VS_capacity = pd.read_excel("C:/Users/Palak/OneDrive/Desktop/ISP_Dataset.xlsx", sheet_name="Capacity of DVS")
DG_demand = pd.read_excel("C:/Users/Palak/OneDrive/Desktop/ISP_Dataset.xlsx", sheet_name="Demand of PHC")

# Set up the optimization model
def run_model(V, J, P, dij, Si, qj):
    # Create a new LP model
    M1 = gp.Model("min_travel_distance")
    # Add binary variables to the model
    xij = M1.addVars(V, J, vtype=GRB.BINARY, name='xij')
    Xi = M1.addVars(V, vtype=GRB.BINARY, name="Xi")
    # Set the objective function
    M1.setObjective(gp.quicksum((qj[j] * xij[i, j] * dij[i][j]) for j in range(J) for i in range(V))/sum(qj), GRB.MINIMIZE)
    # Every PHC must be fully served
    M1.addConstrs((gp.quicksum(xij[i, j] for i in range(V)) == 1) for j in range(J))
    # There is enough capacity of DVS to serve allocated PHC
    M1.addConstrs((gp.quicksum(xij[i, j] * qj[j] for j in range(J)) <= Si[i]) for i in range(V))
    # Allowable number of DVS are P.
    M1.addConstr((gp.quicksum(Xi[i] for i in range(V)) == P))
    # Assignment of DVS should not be made to a PHC until a warehouse is opened in that location
    M1.addConstrs((xij[i, j] <= Xi[i]) for i in range(V) for j in range(J))
    M1.update()
    # Optimize the model
    M1.optimize()
    # Return the solution
    return M1, xij



DVS = VS_capacity['District Vaccine Store'].tolist() 
PHC = DG_demand['Primary Health Centers'].tolist()
df  = pd.read_excel("C:/Users/Palak/OneDrive/Desktop/ISP_Dataset.xlsx",sheet_name='Coordinates')


# Define the Streamlit app
def app():
    # Set the page title
    st.set_page_config(page_title="Optimization Model", page_icon=":bar_chart:", layout="wide")

    # Set the app title and description
    st.markdown("<h1 style='text-align: center; color: #008080; font-size: 70px; font-family: Times New Roman, sans-serif;'>Vaccine Distribution Optimization Model</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size: 25px';>This app uses an optimization model to determine the optimal number of District Vaccine Stores for  distribution of vaccines to Primary Health Centers in West Bengal.</h1>", unsafe_allow_html=True)
    
    # Set up the sidebar
    st.sidebar.title("Inputs")
    st.sidebar.markdown("<style>h1{font-size: 60px;}</style>", unsafe_allow_html=True)
    V = st.sidebar.number_input("Number of DVS", min_value=1, max_value=20, value=20, step=1)
    st.sidebar.markdown(f"<h3 style=' font-size: 27px;'>Potential Number of District Vaccince Stores: {V}</h3>", unsafe_allow_html=True)
    J = st.sidebar.number_input("Number of PHC", min_value=1, max_value=280, value=280, step=1)
    st.sidebar.markdown(f"<h3 style=' font-size: 27px;'>Number of Primary Health Centers: {J}</h3>", unsafe_allow_html=True)
    P = st.sidebar.number_input("Number of DVS to be allocated", min_value=1, max_value=20, value=12, step=1)
    st.sidebar.markdown(f"<h3 style=' font-size: 27px;'>No. of District Vaccination Store to be Allocated: {P}</h3>", unsafe_allow_html=True)

    # Load the data
    dij = Distance_Matrix.iloc[:, 1:].values.tolist()
    Si = VS_capacity['Capacity'].tolist()
    qj = DG_demand['Demand'].tolist()

   # Run the optimization model
    solution, xij = run_model(V, J, P, dij, Si, qj)


    # Progress animation
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i+1)

    # Display the solution
    st.markdown("<h2 style=' color:yellow ; font-size: 35px; font-family: Arial, sans-serif;'>Objective function value:-</h1>", unsafe_allow_html=True)
    st.header(f"The average travel distance considering weighted demand is {solution.getAttr('ObjVal')} km.")

    # Create a dictionary of the allocation
   
    my_dict={}
    list3=[]
    for i in range(V):
        for j in range(J):
            if xij[i,j].X == 1:
                list3.append(PHC[j])
        if len(list3)!=0:
            my_dict[str(DVS[i])]=list3
            list3=[]
        else:
            continue


    my_dict

        # Create a map centered at the first location in your dataframe
    m = folium.Map(location=[df.loc[0,'Latitude'], df.loc[0,'Longitude']], zoom_start=8)

# Loop through your dictionary and add markers and polylines for each district and its corresponding PHCs
    for district, phcs in my_dict.items():

    # Get the latitude and longitude of the district
        district_lat = df[df['Locations']==district]['Latitude'].values[0]
        district_lon = df[df['Locations']==district]['Longitude'].values[0]

    # Add a marker for the district
        folium.Marker(
            location=[district_lat, district_lon],
            tooltip=district,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Loop through the PHCs for this district and add a marker and polyline for each one
        for phc in phcs:
            phc_lat = df[df['Locations']==phc]['Latitude'].values[0]
            phc_lon = df[df['Locations']==phc]['Longitude'].values[0]

        # Add a marker for the PHC
            folium.Marker(
                location=[phc_lat, phc_lon],
                tooltip=phc,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        # Add a polyline connecting the district and PHC
            folium.PolyLine(locations=[[district_lat,district_lon],[phc_lat,phc_lon]], color='green', weight=2).add_to(m)

# Display the map using streamlit_folium
    st.title("My Map")
    folium_static(m)
   
if __name__ == "__main__":
    app()
