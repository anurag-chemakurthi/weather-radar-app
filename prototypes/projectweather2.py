import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pyart
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

# NEXRAD 스테이션 정보 (스테이션 이름과 위도, 경도)
STATIONS = {
    "KFWS": (32.5728, -97.3037),
    "KTLX": (35.3331, -97.2775),
    "KAMX": (25.6116, -80.4130),
    "KABR": (45.4564, -98.4130),
    "KAKQ": (36.9836, -77.0071),
    "KAMA": (35.2333, -101.7111),
    "KARX": (43.8225, -91.1919),
}

class RadarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXRAD Station Viewer")
        self.root.geometry("1200x800")

        # 지도 그리기
        self.figure = Figure(figsize=(12, 6))
        self.ax = self.figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.ax.set_global()
        self.ax.coastlines()
        self.ax.add_feature(cfeature.BORDERS, linestyle=":")
        self.ax.add_feature(cfeature.STATES, linestyle=":")
        self.ax.set_extent([-130, -60, 20, 55], ccrs.PlateCarree())  # 미국 지도 경계 설정

        # 스테이션 점 그리기
        for station, (lat, lon) in STATIONS.items():
            self.ax.plot(lon, lat, 'ro', markersize=8, transform=ccrs.PlateCarree())
            self.ax.text(lon + 0.5, lat, station, transform=ccrs.PlateCarree())

        # Tkinter용 Matplotlib 캔버스
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_map_click)

    def on_map_click(self, event):
        """지도에서 클릭 이벤트 처리"""
        if event.xdata is None or event.ydata is None:
            return

        clicked_lon, clicked_lat = event.xdata, event.ydata
        nearest_station = self.get_nearest_station(clicked_lat, clicked_lon)

        if nearest_station:
            self.open_time_input_window(nearest_station)

    def get_nearest_station(self, lat, lon):
        """클릭한 지점에서 가장 가까운 스테이션 반환"""
        nearest_station = None
        min_distance = float("inf")
        for station, (s_lat, s_lon) in STATIONS.items():
            distance = ((lat - s_lat)**2 + (lon - s_lon)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        return nearest_station

    def open_time_input_window(self, station):
        """시간 입력 창 열기"""
        time_window = tk.Toplevel(self.root)
        time_window.title(f"Enter Time for {station}")
        time_window.geometry("400x800")

        tk.Label(time_window, text=f"Selected Station: {station}").pack(pady=10)
        tk.Label(time_window, text="Enter Date and Time (Start and End Time)").pack(pady=5)

        # 날짜 입력
        tk.Label(time_window, text="Year (YYYY):").pack(pady=2)
        year_entry = tk.Entry(time_window)
        year_entry.pack()

        tk.Label(time_window, text="Month (MM):").pack(pady=2)
        month_entry = tk.Entry(time_window)
        month_entry.pack()

        tk.Label(time_window, text="Day (DD):").pack(pady=2)
        day_entry = tk.Entry(time_window)
        day_entry.pack()

        tk.Label(time_window, text="Start Time (HHMMSS):").pack(pady=2)
        start_time_entry = tk.Entry(time_window)
        start_time_entry.pack()

        tk.Label(time_window, text="End Time (HHMMSS):").pack(pady=2)
        end_time_entry = tk.Entry(time_window)
        end_time_entry.pack()

        # 버튼
        def fetch_data():
            year = year_entry.get()
            month = month_entry.get()
            day = day_entry.get()
            start_time = start_time_entry.get()
            end_time = end_time_entry.get()

            if not (year.isdigit() and month.isdigit() and day.isdigit()):
                messagebox.showerror("Input Error", "Year, Month, and Day must be numeric.")
                return

            if len(year) != 4 or len(month) != 2 or len(day) != 2:
                messagebox.showerror("Input Error", "Invalid date format.")
                return

            # 시간 입력 검증
            if len(start_time) != 6 or len(end_time) != 6:
                messagebox.showerror("Input Error", "Start and End Time must be in HHMMSS format.")
                return

            try:
                times = self.generate_time_range(start_time, end_time)
                for time in times:
                    aws_s3_path = f"s3://noaa-nexrad-level2/{year}/{month}/{day}/{station}/{station}{year}{month}{day}_{time}_V06"
                    try:
                        radar = pyart.io.read_nexrad_archive(aws_s3_path)
                        self.plot_radar_data(radar, station, time)
                    except Exception as e:
                        print(f"Data not found for {time}, skipping. Error: {e}")
                        continue  # 데이터가 없으면 스킵하고 다음 시간으로 넘어감

                time_window.destroy()

            except ValueError:
                messagebox.showerror("Input Error", "Invalid time range format. Use HHMMSS-HHMMSS.")

        tk.Button(time_window, text="Download and Plot", command=fetch_data).pack(pady=20)

    def generate_time_range(self, start, end):
        """시간 범위 생성기 (1초 간격으로 생성), 시작 시간 포함"""
        start_hour = int(start[:2])
        start_minute = int(start[2:4])
        start_second = int(start[4:])

        end_hour = int(end[:2])
        end_minute = int(end[2:4])
        end_second = int(end[4:])

        current_time = start_hour * 3600 + start_minute * 60 + start_second
        end_time = end_hour * 3600 + end_minute * 60 + end_second

        times = []
        while current_time <= end_time:
            hour = str(current_time // 3600).zfill(2)
            minute = str((current_time % 3600) // 60).zfill(2)
            second = str(current_time % 60).zfill(2)
            times.append(hour + minute + second)
            current_time += 1  # 1초 간격으로 생성

        return times

    def plot_radar_data(self, radar, station, time):
        """레이더 데이터 시각화"""
        figure = plt.figure(figsize=(12, 6))
        display = pyart.graph.RadarMapDisplay(radar)
        ax = figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        display.plot_ppi_map(
            "reflectivity", sweep=0, ax=ax,
            title=f"Reflectivity (dBZ) for {station} at {time}", colorbar_label="Reflectivity",
            vmin=-20, vmax=60
        )
        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, linestyle=":")
        ax.add_feature(cfeature.STATES, linestyle=":")

        # 새로운 창에 캔버스 표시
        new_window = tk.Toplevel(self.root)
        new_window.title(f"Radar Data for {station} at {time}")
        canvas = FigureCanvasTkAgg(figure, master=new_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = RadarApp(root)
    root.mainloop()
