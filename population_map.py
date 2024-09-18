import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape
import geopandas as gpd
import numpy as np
import os

# Set the page configuration
st.set_page_config(layout="wide")

st.title("Interactive World Population Map")

# Load the population raster data
raster_file = 'gpw_v4_population_count_rev11_2020_2pt5_min.tif'  # Update this with the correct file path

if not os.path.exists(raster_file):
    st.warning(f"Population raster file '{raster_file}' not found. Please download and place it in the same directory.")
else:
    raster = rasterio.open(raster_file)

    # Get raster CRS
    raster_crs = raster.crs

    # Create a base map
    m = folium.Map(location=[20, 0], zoom_start=2)

    # Add the Draw plugin for freehand drawing (lasso tool)
    draw = Draw(export=True, filename='drawn_shape.geojson', position='topleft', draw_options={
        'polyline': False,
        'rectangle': False,
        'circle': False,
        'marker': False,
        'circlemarker': False,
        'polygon': True
    })
    draw.add_to(m)

    # Display the map
    output = st_folium(m, width=1000, height=600)

    # Process the drawn polygon
    if output['all_drawings']:
        # Get the last drawn feature
        last_feature = output['all_drawings'][-1]
        geom = last_feature['geometry']

        # Create a GeoDataFrame in WGS84
        polygon_gdf = gpd.GeoDataFrame(index=[0], crs="EPSG:4326", geometry=[shape(geom)])

        # Reproject the polygon to raster CRS
        polygon_proj = polygon_gdf.to_crs(raster.crs)

        # Mask the raster with the transformed polygon
        try:
            out_image, out_transform = mask(raster, polygon_proj.geometry, crop=True)
            out_image = out_image[0]  # Get the first band

            # Debugging: Print shape and type of out_image
            # st.write(f"Shape of out_image: {out_image.shape}")
            # st.write(f"Data type of out_image: {out_image.dtype}")

            # Handle no-data values and convert to float64 to avoid overflow
            out_image = np.nan_to_num(out_image, nan=0).astype(np.float64)

            # Debugging: Check for any max/min values in the array
            max_value = np.max(out_image)
            min_value = np.min(out_image)
            # st.write(f"Max value in the selected area: {max_value}")
            # st.write(f"Min value in the selected area: {min_value}")

            # Clip the array to ensure no invalid values (just a safeguard)
            out_image = np.clip(out_image, 0, np.inf)

            # Sum the population values using float64 to prevent overflow
            total_population = np.sum(out_image)

            # Output the total population
            st.write(f"### Total population in the selected area: {int(total_population):,}")
        except Exception as e:
            st.error(f"Error processing the polygon: {e}")