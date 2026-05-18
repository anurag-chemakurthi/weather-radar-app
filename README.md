# Weather Radar App

An interactive Python desktop application for visualizing U.S. weather radar data using NOAA NEXRAD Level II radar files, geospatial mapping, and radar animation tools.

## Overview

This project was built to explore weather radar visualization, geospatial data processing, and interactive desktop application development in Python. The final version allows users to view a map of the continental United States, toggle map layers, zoom into states, select radar stations, retrieve NOAA NEXRAD radar files, and display radar reflectivity data.

## Main File

The main application file is:

```bash
WeatherApp.py
```

Earlier development versions and prototypes are stored in the `prototypes/` folder.

## Features

- Interactive U.S. map visualization
- State zoom functionality
- Radar station selection
- NOAA NEXRAD Level II radar retrieval
- Radar reflectivity visualization
- Radar animation playback
- Toggleable map layers:
  - Time zones
  - Radar towers
  - Major cities
  - Counties
- Automatic dataset downloading when required
- PyQt5 graphical user interface

## Technologies Used

- Python
- PyQt5
- Matplotlib
- Cartopy
- GeoPandas
- Pandas
- Py-ART
- Shapely
- AWS S3
- Boto3
- NOAA NEXRAD Level II data

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/weather-radar-app.git
cd weather-radar-app
```

Install required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python WeatherApp.py
```

## How It Works

1. The application loads state, county, city, and radar station data.
2. Users select a date and time range.
3. Users click on a state to zoom in.
4. Users select a radar station.
5. NOAA NEXRAD Level II radar data is retrieved from AWS public storage.
6. Radar data is processed using Py-ART.
7. Reflectivity frames are displayed and animated.

## Development History

This project evolved through multiple development stages.

Initial versions used:

- Tkinter for the user interface
- Hardcoded radar stations
- Simpler map interactions

The final implementation added:

- PyQt5 interface
- Interactive map controls
- Dynamic radar station selection
- NOAA data retrieval
- Layer controls
- Radar animation support

Earlier development files are preserved in the `prototypes/` folder.

## Repository Structure

```text
weather-radar-app/
│
├── README.md
├── requirements.txt
├── .gitignore
├── WeatherApp.py
│
├── prototypes/
│   ├── projectweather2.py
│   ├── WeatherAppOld.py
│   ├── interactive_us_map.py
│   └── test.py
│
├── data/
│   ├── USCities.csv
│   └── Weather_Radar_Stations.csv
│
├── assets/
│   └── USGS_13_n25w081_20220406.tif
│
└── media/
    └── demo.mp4
```

## Demo

A demonstration video is included:

```text
media/demo.mp4
```

## Notes

This application uses publicly available NOAA NEXRAD Level II weather radar data hosted through AWS public datasets.

Some geospatial libraries, particularly Cartopy, GeoPandas, and Py-ART, may require additional setup depending on the operating system.
