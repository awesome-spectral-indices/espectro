import json

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from PIL import Image

image = Image.open("_static/logo_white.png")

st.set_page_config(page_title="Espectro", layout="wide")
st.image(image, width=300)
st.markdown(
    """
    The **Awesome Spectral Indices Streamlit App**.
    Created by [David Montero Loaiza](https://github.com/davemlz).
    Powered by [Awesome Spectral Indices](https://github.com/awesome-spectral-indices/awesome-spectral-indices).
    """
)

CSV = "https://raw.githubusercontent.com/awesome-spectral-indices/awesome-spectral-indices/main/output/spectral-indices-table.csv"

with open("data/bands.json", "r") as f:
    bands = json.load(f)

bandsPerPlatform = []
for key in bands.keys():
    keyList = list(bands[key].keys())
    keyList.remove("short_name")
    keyList.remove("long_name")
    for platform in keyList:
        dictToAdd = bands[key][platform]
        dictToAdd["standard"] = key
        bandsPerPlatform.append(dictToAdd)

BANDS = pd.DataFrame(bandsPerPlatform).rename(
    columns={
        "platform": "Platform",
        "band": "Band",
        "name": "Name",
        "wavelength": "Wavelength (nm)",
        "bandwidth": "Bandwidth (nm)",
    }
)

BANDS["Bandwidth (nm)"] = BANDS["Bandwidth (nm)"] / 2.0

def toMath(x):
    """Convert the expression to a math-latex readable expression."""

    x = x.replace(" ", "")
    x = x.replace("**", "^")
    x = x.replace("^2.0", "^{2.0}")
    x = x.replace("^0.5", "^{0.5}")
    x = x.replace("^nexp", "^{n}")
    x = x.replace("^cexp", "^{c}")
    x = x.replace("gamma", "\\gamma ")
    x = x.replace("alpha", "\\alpha ")
    x = x.replace("omega", "\\omega ")
    x = x.replace("lambdaN", "\\lambda_{N} ")
    x = x.replace("lambdaR", "\\lambda_{R} ")
    x = x.replace("lambdaG", "\\lambda_{G} ")
    x = x.replace("*", "\\times ")
    return x


A, B, C = st.columns(3)

E, F = st.columns(2)

with A:
    indexTypes = st.multiselect(
        label="Filter by index type:",
        options=(
            "All",
            "Vegetation",
            "Burn",
            "Water",
            "Snow",
            "Urban",
            "Kernel",
            "RADAR",
        ),
        default=None,
    )

with B:
    bandsOptions = st.multiselect(
        label="Filter by bands:",
        options=(
            "All",
            "A: Aerosols",
            "B: Blue",
            "G: Green",
            "R: Red",
            "RE1: Red Edge 1",
            "RE2: Red Edge 2",
            "RE3: Red Edge 3",
            "RE4: Near-Infrared (NIR) 2 (Red Edge 4 in Google Earth Engine)",
            "N: Near-Infrared (NIR)",
            "S1: Short-wave Infrared (SWIR) 1",
            "S2: Short-wave Infrared (SWIR) 2",
            "T1: Thermal Infrared 1",
            "T2: Thermal Infrared 2",
            "HH: Backscattering Coefficient HH",
            "HV: Backscattering Coefficient HV",
            "VV: Backscattering Coefficient VV",
            "VH: Backscattering Coefficient VH",
        ),
        default=None,
    )


def getBands(x):
    """Get the bands from the list-string."""

    return (
        x.replace('"', "")
        .replace("'", "")
        .replace(" ", "")
        .replace("[", "")
        .replace("]", "")
        .split(",")
    )


def checkBands(x):
    """Check if selected bands are available for an index."""

    x = getBands(x)
    
    return all(i in x for i in [option.split(":")[0] for option in bandsOptions])


with E:
    spectral = pd.read_csv(CSV)
    if len(indexTypes) == 0:
        indexTypes = "All"
    if "All" in indexTypes:
        filtered = spectral
    else:
        filtered = spectral[spectral.application_domain.isin([x.lower() for x in indexTypes])]
    if "All" not in bandsOptions:
        filtered["checkBands"] = filtered.bands.apply(checkBands)
        filtered = filtered[filtered.checkBands == True]
        filtered = filtered.drop("checkBands", 1)
    st.download_button(
        label="Download Indices as CSV",
        data=filtered.to_csv(index=False),
        file_name="awesome-spectral-indices.csv",
        mime="text/csv",
    )
    st.caption("Filtered Spectral Indices:")
    st.dataframe(filtered, height=500)

with C:
    idx = st.selectbox("Select Spectral Index:", filtered.short_name.unique())

if len(filtered.loc[filtered.short_name == idx, "long_name"].values) > 0:

    idxData = filtered[filtered.short_name == idx]

    with F:
        st.caption("Spectral Index info:")
        st.metric(
            label=idxData["long_name"].values[0],
            value=idxData["short_name"].values[0],
        )
        st.latex(toMath(idxData["formula"].values[0]))
        st.markdown(
            f"""
            Reference: [{idxData["reference"].values[0]}]({idxData["reference"].values[0]}).
            Contributed by [{idxData["contributor"].values[0].split('/')[-1]}]({idxData["contributor"].values[0]}) on {idxData["date_of_addition"].values[0]}
            """
        )

        bandsToPlot = getBands(idxData["bands"].values[0])
        fig = px.scatter(
            BANDS[BANDS.standard.isin(bandsToPlot)],
            x="Wavelength (nm)",
            y="Platform",
            template="simple_white",
            error_x="Bandwidth (nm)",
            color="Name",
            color_discrete_map={
                "Aersols": "#B983FF",
                "Blue": "#548CFF",
                "Green": "#06FF00",
                "Red": "#FF1700",
                "Red Edge 1": "#FFF323",
                "Red Edge 2": "#FFCA03",
                "Red Edge 3": "#FF5403",
                "Near-Infrared (NIR) 2 (Red Edge 4 in Google Earth Engine)": "#D22779",
                "Near-Infrared (NIR)": "#FF008E",
                "Short-wave Infrared (SWIR) 1": "#612897",
                "Short-wave Infrared (SWIR) 2": "#0C1E7F",
                "Thermal Infrared 1": "#8D448B",
                "Thermal Infrared 2": "#5026A7",
            },
            hover_name="Platform",
            log_x=True,
            height=400,
            title="Required Bands by Platform:",
        )
        st.plotly_chart(fig, use_container_width=True)
