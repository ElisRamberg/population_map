import streamlit as st
import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import base64
from rasterio.enums import Resampling
from rasterio.transform import Affine
from rasterio.transform import array_bounds
from streamlit_folium import st_folium

# Set the page configuration
st.set_page_config(layout="wide")

st.title("Population Density Map")

# File path for the population density raster (start with a smaller file)
density_raster_file = 'gpw_v4_population_density_rev11_2020_30_sec.tif'

# Open the density raster for visualization
with rasterio.open(density_raster_file) as density_raster:
    out_height = 360  # Adjust as needed for smaller size
    out_width = 720   # Adjust as needed for smaller size

    # Read the density data and resample
    density_data = density_raster.read(
        1,
        out_shape=(
            out_height,
            out_width
        ),
        resampling=Resampling.bilinear
    )
    density_data = np.nan_to_num(density_data, nan=0)

    # Compute the new transform
    new_transform = density_raster.transform * Affine.scale(
        (density_raster.width / out_width),
        (density_raster.height / out_height)
    )

    # Normalize the data for visualization
    data_min = np.min(density_data)
    data_max = np.max(density_data)
    if data_max == data_min:
        data_norm = np.zeros_like(density_data)
    else:
        data_norm = (density_data - data_min) / (data_max - data_min)

    # Apply a color map
    colormap = plt.cm.viridis
    density_colored = colormap(data_norm)

    # Convert to uint8
    density_colored = (density_colored * 255).astype(np.uint8)

    # Create an image from the array
    image = Image.fromarray(density_colored, mode='RGBA')

    # Convert the image to base64
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Get the bounds
    bounds = array_bounds(out_height, out_width, new_transform)
    xmin, ymin, xmax, ymax = bounds

    # Create a base map
    m = folium.Map(location=[0, 0], zoom_start=2)

    # Overlay the image on the map
    img_url = 'data:image/png;base64,' + img_str

    img_overlay = folium.raster_layers.ImageOverlay(
        image=img_url,
        bounds=[[ymin, xmin], [ymax, xmax]],
        opacity=0.6,
        interactive=False,
        cross_origin=False,
        zindex=1,
    )

    img_overlay.add_to(m)

    # Display the map
    st_folium(m, width=1000, height=600)
