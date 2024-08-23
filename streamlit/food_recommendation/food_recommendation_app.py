import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.distance import distance
import math

# Custom CSS to make the app more beautiful and modern
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    .reportview-container {
        background: linear-gradient(rgba(255,255,255,0.8), rgba(255,255,255,0.8)), 
                    url('https://i.imgur.com/YAQriU6.jpg');
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Poppins', sans-serif;
    }
    .big-font {
        font-size: 64px !important;
        font-weight: 700;
        color: #ff4e50;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .subtitle {
        font-size: 32px !important;
        font-weight: 600;
        color: #ff4e50;
        text-align: center;
        margin-bottom: 30px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .medium-font {
        font-size: 32px !important;
        font-weight: 600;
        color: #ff4e50;
        margin-top: 40px;
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .stExpander {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .stButton>button {
        margin: 0 5px;
        border-radius: 20px;
        font-weight: 600;
    }
    .caveats {
        background-color: rgba(248, 249, 250, 0.9);
        border: 1px solid #e9ecef;
        padding: 20px;
        margin-top: 50px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .caveats-title {
        font-size: 24px;
        font-weight: 600;
        color: #495057;
        margin-bottom: 10px;
    }
    .caveats-content {
        font-size: 16px;
        color: #6c757d;
    }
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.95);
        font-size: 18px;
        color: #495057;
        border: 2px solid #ced4da;
        border-radius: 10px;
        padding: 10px 15px;
    }
    .stSlider>div>div>div>div {
        background-color: #ff4e50;
    }
</style>
""", unsafe_allow_html=True)

def get_user_location():
    geolocator = Nominatim(user_agent="food_recommendation_app")
    location = geolocator.geocode(st.session_state.location_input)
    return location.latitude, location.longitude

def get_nearby_food_options(lat, lon, radius=5000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="restaurant"](around:{radius},{lat},{lon});
      way["amenity"="restaurant"](around:{radius},{lat},{lon});
      relation["amenity"="restaurant"](around:{radius},{lat},{lon});
    );
    out center;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    return data['elements']

def create_map(lat, lon, food_options, view_radius):
    m = folium.Map(location=[lat, lon], zoom_start=16)
    folium.Marker([lat, lon], popup="Your Location", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
    
    # Add a circle to represent the view radius
    folium.Circle(
        [lat, lon],
        radius=view_radius,
        color="blue",
        fill=True,
        fillColor="blue",
        fillOpacity=0.1
    ).add_to(m)
    
    for food_option in food_options:
        if 'center' in food_option:
            food_lat, food_lon = food_option['center']['lat'], food_option['center']['lon']
        else:
            food_lat, food_lon = food_option['lat'], food_option['lon']
        
        dist = distance((lat, lon), (food_lat, food_lon)).m
        if dist <= view_radius:
            folium.Marker(
                [food_lat, food_lon],
                popup=food_option['tags'].get('name', 'Unknown'),
                icon=folium.Icon(color="green", icon="cutlery", prefix='fa')
            ).add_to(m)
    
    return m

def main():
    st.markdown('<p class="big-font">Foodie Finder SG</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Helping clueless people find inspiration for food all around you!</p>', unsafe_allow_html=True)

    if 'location_input' not in st.session_state:
        st.session_state.location_input = ""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'food_option_distances' not in st.session_state:
        st.session_state.food_option_distances = []
    if 'map' not in st.session_state:
        st.session_state.map = None
    if 'view_radius' not in st.session_state:
        st.session_state.view_radius = 1000

    location_input = st.text_input("Enter your location:", value=st.session_state.location_input, 
                                   help="Enter a city, address, or landmark")
    st.session_state.location_input = location_input

    if st.button("Find Food Options", key="get_recommendations"):
        try:
            lat, lon = get_user_location()
            food_options = get_nearby_food_options(lat, lon, radius=5000)  # 5km radius
            
            if not food_options:
                st.warning("No food options found within 5km. Try a different location.")
                st.session_state.map = None
                st.session_state.food_option_distances = []
            else:
                st.session_state.map = create_map(lat, lon, food_options, st.session_state.view_radius)

                # Calculate distances and sort food options
                st.session_state.food_option_distances = []
                for food_option in food_options:
                    if 'center' in food_option:
                        food_lat, food_lon = food_option['center']['lat'], food_option['center']['lon']
                    else:
                        food_lat, food_lon = food_option['lat'], food_option['lon']
                    
                    dist = distance((lat, lon), (food_lat, food_lon)).km
                    if dist <= 5:  # 5km max radius
                        st.session_state.food_option_distances.append((dist, food_option))
                
                st.session_state.food_option_distances.sort(key=lambda x: x[0])
                st.session_state.current_page = 1

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.map = None
            st.session_state.food_option_distances = []

    # Display the map if it exists
    if st.session_state.map:
        st.markdown('<p class="medium-font">Map of Nearby Food Options</p>', unsafe_allow_html=True)
        
        # Add a slider for adjusting the view radius
        st.session_state.view_radius = st.slider("Adjust view radius (meters)", 100, 5000, st.session_state.view_radius, 100)
        
        # Update the map with the new radius
        lat, lon = get_user_location()
        food_options = get_nearby_food_options(lat, lon, radius=5000)
        st.session_state.map = create_map(lat, lon, food_options, st.session_state.view_radius)
        
        folium_static(st.session_state.map)

    if st.session_state.food_option_distances:
        st.markdown('<p class="medium-font">List of Nearby Food Options (within 5km)</p>', unsafe_allow_html=True)
        
        # Pagination
        items_per_page = 15
        total_pages = math.ceil(len(st.session_state.food_option_distances) / items_per_page)
        
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        for dist, food_option in st.session_state.food_option_distances[start_idx:end_idx]:
            name = food_option['tags'].get('name', 'Unknown')
            
            with st.expander(f"{name} - Distance: {dist:.2f} km"):
                st.write(f"Cuisine: {food_option['tags'].get('cuisine', 'N/A')}")
                st.write(f"Address: {food_option['tags'].get('addr:street', 'N/A')} {food_option['tags'].get('addr:housenumber', '')}")
                st.write(f"Phone: {food_option['tags'].get('phone', 'N/A')}")
                st.write(f"Website: {food_option['tags'].get('website', 'N/A')}")
                st.write(f"Opening Hours: {food_option['tags'].get('opening_hours', 'N/A')}")

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.current_page > 1:
                if st.button("Previous", key="prev_page"):
                    st.session_state.current_page -= 1

        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")

        with col3:
            if st.session_state.current_page < total_pages:
                if st.button("Next", key="next_page"):
                    st.session_state.current_page += 1

    # Caveats section
    st.markdown("""
    <div class="caveats">
        <p class="caveats-title">Note on Data and Limitations</p>
        <div class="caveats-content">
            <p>Foodie Finder uses OpenStreetMap data, which is community-driven. While we strive for accuracy, the information provided may not always be complete or up-to-date. The app has certain limitations, including a maximum fetch of 100 food options within 5km and "as the crow flies" distance calculations. Please use this tool as a helpful guide rather than a definitive source for food option information.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

# test comment