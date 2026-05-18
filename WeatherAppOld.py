import sys
from datetime import datetime
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
    QComboBox, QLabel, QDateEdit, QCheckBox, QMessageBox
)
from PyQt5.QtCore import QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.patches as mpatches
import pyart
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class InteractiveUSMap(QMainWindow):
   def __init__(self):
      super().__init__()
      self.setWindowTitle("Interactive US Map with Radar Data and Toggleable Layers")

      # Array to store radar maps for animation
      self.radar_frames = []  # List of tuples: [(figure, time), ...]

      # Selected radar station and zoom state
      self.selected_station = None
      self.zoomed_in = False  # Tracks if map is zoomed into a state

      # Central widget
      self.central_widget = QWidget()
      self.setCentralWidget(self.central_widget)
      main_layout = QHBoxLayout(self.central_widget)

      # Left side: Map layout
      left_layout = QVBoxLayout()
      main_layout.addLayout(left_layout, stretch=5)

      # Map figure
      self.figure = Figure(figsize=(12, 8))
      self.ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
      self.ax.set_extent([-130, -60, 20, 55], ccrs.PlateCarree())
      self.ax.coastlines()
      self.ax.add_feature(cfeature.BORDERS, linestyle=":")
      self.ax.add_feature(cfeature.STATES, linestyle=":")

      # Matplotlib canvas
      self.canvas = FigureCanvas(self.figure)
      left_layout.addWidget(self.canvas)

      # Back button
      self.back_button = QPushButton("Back to Full US Map")
      self.back_button.setStyleSheet("""
         QPushButton {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px 20px;
         }
         QPushButton:hover {
            background-color: #45a049;
         }
      """)
      self.back_button.clicked.connect(self.reset_map)
      left_layout.addWidget(self.back_button)

      # Right side: Controls layout
      right_widget = QWidget()
      right_widget.setFixedWidth(290)
      main_layout.addWidget(right_widget)

      right_layout = QVBoxLayout(right_widget)
      right_layout.setContentsMargins(10, 10, 10, 10)

      # Date selection
      right_layout.addWidget(QLabel("Date:"))
      self.date_picker = QDateEdit()
      self.date_picker.setCalendarPopup(True)
      self.date_picker.setDate(QDate.currentDate())
      right_layout.addWidget(self.date_picker)

      # Time selection
      right_layout.addWidget(QLabel("Time (Start-End):"))
      time_layout = QHBoxLayout()
      self.start_time = QComboBox()
      self.start_time.addItems([f"{i:02d}:00:00" for i in range(24)])
      time_layout.addWidget(self.start_time)
      self.end_time = QComboBox()
      self.end_time.addItems([f"{i:02d}:59:59" for i in range(24)])
      time_layout.addWidget(self.end_time)
      right_layout.addLayout(time_layout)

      # Layer toggles
      self.timezone_checkbox = QCheckBox("Show Time Zones")
      self.timezone_checkbox.setChecked(True)
      self.timezone_checkbox.stateChanged.connect(self.plot_full_map)
      right_layout.addWidget(self.timezone_checkbox)

      self.radar_checkbox = QCheckBox("Show Radar Towers")
      self.radar_checkbox.setChecked(True)
      self.radar_checkbox.stateChanged.connect(self.plot_full_map)
      right_layout.addWidget(self.radar_checkbox)

      self.cities_checkbox = QCheckBox("Show Cities")
      self.cities_checkbox.setChecked(False)
      self.cities_checkbox.stateChanged.connect(self.plot_full_map)
      right_layout.addWidget(self.cities_checkbox)

      self.show_counties_checkbox = QCheckBox("Show Counties in \nZoomed-Out View")
      self.show_counties_checkbox.setChecked(False)
      self.show_counties_checkbox.stateChanged.connect(self.plot_full_map)
      right_layout.addWidget(self.show_counties_checkbox)

      fetch_button = QPushButton("Fetch and Plot Radar Data")
      fetch_button.clicked.connect(self.fetch_radar_data)
      right_layout.addWidget(fetch_button)

      right_layout.addStretch()

      # Load data
      self.load_map_data()
      self.load_radar_data()
      self.load_city_data()
      self.load_county_data()
      self.plot_full_map()

      # Map events
      self.figure.canvas.mpl_connect("button_press_event", self.on_map_click)
      self.figure.canvas.mpl_connect("motion_notify_event", self.on_hover)

   def reset_map(self):
      """Reset to the full US map and disable radar selection."""
      self.zoomed_in = False
      self.plot_full_map()

   def load_map_data(self):
      shapefile_url = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_500k.zip"
      self.us_map = gpd.read_file(shapefile_url)
      self.us_map = self.us_map[~self.us_map['STUSPS'].isin(['AK', 'HI', 'AS', 'GU', 'MP', 'PR', 'VI'])]

   def load_radar_data(self):
      self.radar_data = pd.read_csv("Weather_Radar_Stations.csv")
      self.radar_data['geometry'] = self.radar_data.apply(lambda row: Point(row['X'], row['Y']), axis=1)
      self.radar_gdf = gpd.GeoDataFrame(self.radar_data, geometry='geometry', crs="EPSG:4326")

   def load_city_data(self):
      self.city_data = pd.read_csv("USCities.csv")
      self.city_data = self.city_data[['city', 'state_id', 'lat', 'lng', 'density']]
      density_threshold = self.city_data['density'].quantile(0.95)
      self.city_data = self.city_data[self.city_data['density'] >= density_threshold]

   def load_county_data(self):
      county_shapefile_url = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_500k.zip"
      self.county_data = gpd.read_file(county_shapefile_url)

   def plot_full_map(self):
      self.ax.clear()
      self.ax.set_extent([-125, -66, 24, 50], ccrs.PlateCarree())
      gl = self.ax.gridlines(draw_labels=True, crs=ccrs.PlateCarree(), linewidth=0.5, color="gray", alpha=0.5)
      gl.top_labels = False
      gl.right_labels = False
      gl.xlabel_style = {"size": 10, "color": "black"}
      gl.ylabel_style = {"size": 10, "color": "black"}

      if self.timezone_checkbox.isChecked():
         self.plot_time_zones()

      self.ax.coastlines()
      self.ax.add_feature(cfeature.BORDERS, linestyle=":")
      self.ax.add_feature(cfeature.STATES, linestyle=":")

      self.us_map.plot(ax=self.ax, color="lightblue", edgecolor="black")

      if self.show_counties_checkbox.isChecked():
         self.county_data.plot(ax=self.ax, color="none", edgecolor="gray", alpha=0.5)

      if self.radar_checkbox.isChecked():
         self.ax.scatter(
            self.radar_data["X"], self.radar_data["Y"],
            color="green", s=5, label="Radar Towers", transform=ccrs.PlateCarree()
         )

      if self.cities_checkbox.isChecked():
          self.ax.scatter(
              self.city_data["lng"], self.city_data["lat"],
              color="red", s=5, label="Cities", transform=ccrs.PlateCarree()
          )

      self.ax.legend(loc="upper right")
      self.canvas.draw()

   def plot_time_zones(self):
      time_zones = {
         "Eastern": {"bounds": (-81, -65), "color": "#add8e6"},
         "Central": {"bounds": (-97, -81), "color": "#ffcccb"},
         "Mountain": {"bounds": (-107, -97), "color": "#90ee90"},
         "Pacific": {"bounds": (-125, -107), "color": "#fffacd"},
      }
      for name, tz in time_zones.items():
         self.ax.add_patch(mpatches.Rectangle(
             (tz["bounds"][0], 24), tz["bounds"][1] - tz["bounds"][0], 26,
             color=tz["color"], alpha=0.5, label=f"{name} Time Zone")
         )

   def on_map_click(self, event):
      """Handle clicks to zoom into a state or fetch radar data."""
      if event.xdata is None or event.ydata is None:
         return

      clicked_lon, clicked_lat = event.xdata, event.ydata
      clicked_point = Point(clicked_lon, clicked_lat)

      if self.zoomed_in:
         # Allow radar tower selection only if zoomed in
         nearest_station = self.get_nearest_station(clicked_lat, clicked_lon)
         if nearest_station:
            self.selected_station = nearest_station
            QMessageBox.information(self, "Station Selected", f"You selected station: {nearest_station}")
            return
      else:
         # Check for state click to zoom
         for _, state_row in self.us_map.iterrows():
            if state_row.geometry.contains(clicked_point):
               self.zoom_into_state(state_row)
               return

   def zoom_into_state(self, state_row):
      """Zoom into a specific state and enable radar tower selection."""
      self.ax.clear()
      self.zoomed_in = True  # Enable radar selection when zoomed in

      minx, miny, maxx, maxy = state_row.geometry.bounds
      self.ax.set_extent([minx, maxx, miny, maxy], ccrs.PlateCarree())

      state_fips = state_row["STATEFP"]
      counties_in_state = self.county_data[self.county_data["STATEFP"] == state_fips]
      counties_in_state.plot(ax=self.ax, color="lightblue", edgecolor="black", alpha=0.7)

      radar_in_state = self.radar_gdf[self.radar_gdf.within(state_row.geometry)]
      if self.radar_checkbox.isChecked():
         self.ax.scatter(
            radar_in_state.geometry.x, radar_in_state.geometry.y,
            color="green", s=10, alpha=1, label="Radar Towers", transform=ccrs.PlateCarree()
         )
         for _, radar in radar_in_state.iterrows():
            self.ax.text(
               radar.geometry.x, radar.geometry.y, radar["siteID"],
               fontsize=8, ha="right", color="black", transform=ccrs.PlateCarree()
            )

      if self.cities_checkbox.isChecked():
         cities_in_state = self.city_data[
            (self.city_data["lng"] >= minx) & (self.city_data["lng"] <= maxx) &
            (self.city_data["lat"] >= miny) & (self.city_data["lat"] <= maxy)
         ]
         self.ax.scatter(
            cities_in_state["lng"], cities_in_state["lat"],
            color="red", s=5, alpha=1, label="Cities", transform=ccrs.PlateCarree()
         )
         for _, city in cities_in_state.iterrows():
            self.ax.text(
               city["lng"], city["lat"], city["city"],
               fontsize=8, ha="left", color="darkred", transform=ccrs.PlateCarree()
            )

      state_name = state_row["NAME"]
      self.ax.set_title(f"Zoomed into: {state_name}")
      self.ax.legend(loc="upper right")
      self.canvas.draw()

   def on_hover(self, event):
      """Handle hovering to show state names in the zoomed-out view
      and state + county names in the zoomed-in view."""
      if event.xdata is None or event.ydata is None:
         self.ax.set_title("")  # Clear the title when not hovering
         self.canvas.draw()
         return

      hovered_lon, hovered_lat = event.xdata, event.ydata
      hovered_point = Point(hovered_lon, hovered_lat)

      # Determine the current map limits
      xlim = self.ax.get_xlim()
      ylim = self.ax.get_ylim()

      # Default bounds for the full US map
      zoom_threshold = (-125, -66, 24, 50)

      if xlim == zoom_threshold[0:2] and ylim == zoom_threshold[2:4]:
         # Zoomed-out view: Show state names
         for _, state_row in self.us_map.iterrows():
            if state_row.geometry.contains(hovered_point):
               state_name = state_row['NAME']
               self.ax.set_title(f"State: {state_name}")
               self.canvas.draw()
               return
         # If no state is hovered over, reset the title
         self.ax.set_title("Continental US Map with Cities, Counties, and Toggleable Layers")
         self.canvas.draw()
      else:
         # Zoomed-in view: Show state and county names
         for _, county_row in self.county_data.iterrows():
            if county_row.geometry.contains(hovered_point):
               county_name = county_row['NAME']
               for _, state_row in self.us_map.iterrows():
                  if state_row.geometry.contains(hovered_point):
                     state_name = state_row['NAME']
                     self.ax.set_title(f"State: {state_name}, County: {county_name}")
                     self.canvas.draw()
                     return
         # If no county is hovered over, reset the title
         self.ax.set_title("")
         self.canvas.draw()

   def get_nearest_station(self, lat, lon):
      nearest_station = None
      min_distance = float("inf")
      for _, radar in self.radar_gdf.iterrows():
         distance = ((lat - radar.geometry.y) ** 2 + (lon - radar.geometry.x) ** 2) ** 0.5
         if distance < min_distance:
            min_distance = distance
            nearest_station = radar["siteID"]
      return nearest_station

   def fetch_radar_data(self):
      if not self.selected_station:
         QMessageBox.warning(self, "No Station Selected", "Please select a radar station on the map first.")
         return
      year = self.date_picker.date().year()
      month = self.date_picker.date().month()
      day = self.date_picker.date().day()
      start_time = self.start_time.currentText().replace(":", "")
      end_time = int(start_time) + 1030
      try:
         times = self.generate_time_range(start_time, end_time)
         for time in times:
            aws_s3_path = f"s3://noaa-nexrad-level2/{year}/{month:02}/{day:02}/{self.selected_station}/{self.selected_station}{year}{month:02}{day:02}_{time}_V06"
            try:
               radar = pyart.io.read_nexrad_archive(aws_s3_path)
               self.store_radar_frame(radar, time)
               print(f"Data found for {time}, Downloading.")
            except Exception as e:
               print(f"Data not found for {time}, skipping. Error: {e}")
               continue
      except Exception as e:
         QMessageBox.critical(self, "Error", f"Failed to fetch radar data: {e}")
      self.animate_radar_data()

   def generate_time_range(self, start, end):
      range = []
      index = int(start)
      while (index <= int(end)):
         range.append(index)
         index += 1
      return range

   def store_radar_frame(self, radar, time):
    """Store radar data frame for later animation."""
    figure = Figure(figsize=(12, 6))
    ax = figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    display = pyart.graph.RadarMapDisplay(radar)
    display.plot_ppi_map(
        "reflectivity",
        sweep=0,
        ax=ax,
        title=f"Reflectivity (dBZ) at {time}",
        colorbar_label="Reflectivity",
        vmin=-20,
        vmax=60
    )
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.add_feature(cfeature.STATES, linestyle=":")

    # Convert figure to canvas and store for animation
    canvas = FigureCanvas(figure)
    self.radar_frames.append((canvas, time))                              

   def animate_radar_data(self):
    """Animate the stored radar maps."""
    if not self.radar_frames:
        QMessageBox.warning(self, "No Data", "No radar data available for animation.")
        return

    fig, ax = plt.subplots(figsize=(12, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_title("Radar Animation")
    ax.set_axis_off()

    def update(frame):
        ax.clear()
        canvas, timestamp = self.radar_frames[frame]
        canvas.draw()
        ax.imshow(canvas.buffer_rgba(), extent=ax.get_extent(), transform=ccrs.PlateCarree())
        ax.set_title(f"Radar Time: {timestamp}")

    self.ani = FuncAnimation(fig, update, frames=len(self.radar_frames), interval=750, repeat=True)
    plt.show()

   def plot_radar_data(self, radar, time):
      figure = Figure(figsize=(10, 5))
      ax = figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
      display = pyart.graph.RadarMapDisplay(radar)
      display.plot_ppi_map(
         "reflectivity", sweep=0, ax=ax,
         title=f"Radar Data {time} - {self.selected_station}", colorbar_label="Reflectivity",
         vmin=-20, vmax=60
      )
      ax.coastlines()
      ax.add_feature(cfeature.BORDERS, linestyle=":")
      ax.add_feature(cfeature.STATES, linestyle=":")

      radar_window = QWidget()
      radar_window.setWindowTitle("Radar Visualization")
      radar_layout = QVBoxLayout(radar_window)
      canvas = FigureCanvas(figure)
      radar_layout.addWidget(canvas)
      radar_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = InteractiveUSMap()
    main_window.show()
    sys.exit(app.exec_())
