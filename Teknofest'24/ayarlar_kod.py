from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget
from ayarlar import Ui_Ayarlar
import sys
import subprocess
import csv
import os
import platform
import folium
from geopy.distance import geodesic
from geopy.point import Point
import pyproj
import math
from math import sqrt

class main(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.ayarlar = Ui_Ayarlar()
        self.ayarlar.setupUi(self)
        self.ayarlar.btnKaydet.clicked.connect(self.calculate_waypoints)
        self.ayarlar.btnVarsaylan.clicked.connect(self.varsayilanDevam)

    def donusYaricapi(self):
        #v = saerotech.hava_hizi_gonder(self)
        #tetha = math.radians(saerotech.yatis_acisi_gonder(self))
        g = 9.81
        v = 20
        tetha = 30.0
        tetha_radian = math.radians(tetha)
        
        yaricap = v**2/(g*math.tan(tetha_radian))
        
        return yaricap
        
    def polygon(self):
        
        """
        Cografi kordinatlarin giris siralamasi
            1   2
            4   3
        """
        
        lat1 = float(self.ayarlar.kose1lat.text())
        lon1 = float(self.ayarlar.kose1lon.text())
        lat2 = float(self.ayarlar.kose2lat.text())
        lon2 = float(self.ayarlar.kose2lon.text())
        lat3 = float(self.ayarlar.kose3lat.text())
        lon3 = float(self.ayarlar.kose3lon.text())
        lat4 = float(self.ayarlar.kose4lat.text())
        lon4 = float(self.ayarlar.kose4lon.text())
        self.main_alt = self.ayarlar.altitude.text()
        
        koordinatlar = [
            (lat1, lon1, self.main_alt),
            (lat2, lon2, self.main_alt),
            (lat3, lon3, self.main_alt),
            (lat4, lon4, self.main_alt)
        ]
        
        # Kullanıcıdan alınan koordinatlar dosyaya kaydedilir.
        os.remove('koordinatlar.csv')
        with open('koordinatlar.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Latitude', 'Longitude', 'Altitude'])
            writer.writerows(koordinatlar)
        self.close()
        
        # Harita oluşturma
        self.m = folium.Map(location=[40.8002637, 30.2914095], zoom_start=17)
        coordinates1 = [
            (lat1, lon1),
            (lat2, lon2),
            (lat3, lon3),           
            (lat4, lon4),
            (lat1, lon1)
            # Poligonun kapanması için ilk koordinat tekrar eklenir
        ]
            
        # Poligon ekleme
        folium.Polygon(
            locations=coordinates1,
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(self.m)    
            
        """
        Sol-Üst -> (upperLimit, leftLimit)
        Sol-Alt -> (lowerLimit, leftLimit)
        Sağ-Üst -> (upperLimit, rightLimit)
        Sağ-Alt -> (lowerLimit, rightLimit)
        """
        
        # Sınırlar belirlenir
        if lat1>lat2:
            upperLimit = lat1
        else:
            upperLimit = lat2
            
        if lon1<lon4:
            leftLimit = lon1
        else:
            leftLimit = lon4
            
        if lon3>lon2:
            rightLimit = lon3
        else:
            rightLimit = lon2
            
        if lat4<lat3:
            lowerLimit = lat4
        else:
            lowerLimit = lat3
            
        coordinates2 = [
            (upperLimit, leftLimit),
            (upperLimit, rightLimit),
            (lowerLimit, rightLimit),
            (lowerLimit, leftLimit),
            (upperLimit, leftLimit)
            # Poligonun kapanması için ilk koordinat tekrar eklenir.
        ]

        # Yeni sınırlarla poligon tekrar çizilir.
        folium.Polygon(
            locations=coordinates2,
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(self.m)
        
        self.m.save('map.html')
        
        return upperLimit, leftLimit, lowerLimit, rightLimit

    def calculate_waypoints(self):
        self.upperLimit, self.leftLimit, self.lowerLimit, self.rightLimit = self.polygon()
        interval = self.donusYaricapi()
        horizontal = geodesic((self.upperLimit, self.leftLimit), (self.upperLimit, self.rightLimit)).meters
        vertical = geodesic((self.upperLimit, self.leftLimit), (self.lowerLimit, self.leftLimit)).meters

        if horizontal >= vertical:
            distance = vertical
            start_end_points = [
                (self.lowerLimit, self.rightLimit, self.upperLimit, self.rightLimit),
                (self.lowerLimit, self.leftLimit, self.upperLimit, self.leftLimit)
            ]
        else:
            distance = horizontal
            start_end_points = [
                (self.upperLimit, self.leftLimit, self.upperLimit, self.rightLimit),
                (self.lowerLimit, self.leftLimit, self.lowerLimit, self.rightLimit)
            ]
            
        self.waypoints = []

        if distance < interval:
            print("Alan donus yapmak icin uygun degil")
            return self.waypoints
        else:
            if distance%interval == 0:
                num_intervals = (distance / interval)       #Tam bolunuyorsa bolum sonucu kenar uzerindeki wp sayisini verir
            else:
                divisor = int(distance // interval)         #Bolumun tam kismi alinir
                interval = distance // divisor
                num_intervals = int(distance // interval)

        geod = pyproj.Geod(ellps='WGS84')
        if distance == horizontal:
            for i in range(num_intervals-1):
                for j, (start_lat, start_lon, end_lat, end_lon) in enumerate(start_end_points):
                    if j == 0:
                        segment_distance = interval
                        fwd_azimuth, _, _ = geod.inv(start_lon, start_lat, end_lon, end_lat)
                        first_lon1, first_lat1, _ = geod.fwd(start_lon, start_lat, fwd_azimuth, segment_distance)
                        left_lon1, left_lat1, _ = geod.fwd(first_lon1, first_lat1, 225, interval*sqrt(2))
                        right_lon1, right_lat1, _ = geod.fwd(first_lon1, first_lat1, 135, interval*sqrt(2))
                        
                        # Sağ kaydırma
                        if i > 0:
                            first_lon1, first_lat1, _ = geod.fwd(first_lon1, first_lat1, 90, interval * i)
                            left_lon1, left_lat1, _ = geod.fwd(left_lon1, left_lat1, 90, interval * i)
                            right_lon1, right_lat1, _ = geod.fwd(right_lon1, right_lat1, 90, interval * i)
                
                        self.waypoints.append((round(left_lat1, 7), round(left_lon1, 7), self.main_alt))
                        self.waypoints.append((round(first_lat1, 7), round(first_lon1, 7), self.main_alt))
                        self.waypoints.append((round(right_lat1, 7), round(right_lon1, 7), self.main_alt))                             

                    elif j == 1:
                        segment_distance = (interval) - (interval/2)
                        fwd_azimuth, _, _ = geod.inv(start_lon, start_lat, end_lon, end_lat)
                        first_lon2, first_lat2, _ = geod.fwd(start_lon, start_lat, fwd_azimuth, segment_distance)
                        left_lon2, left_lat2, _ = geod.fwd(first_lon2, first_lat2, 0, interval)
                        down_lon2, down_lat2, _ = geod.fwd(first_lon2, first_lat2, 90, interval)
                        fw_lon, fw_lat, _ = geod.fwd(down_lon2, down_lat2, 90, interval)
                        right_lon2, right_lat2, _ = geod.fwd(fw_lon, fw_lat, 0, interval)
                        
                        # Sağ kaydırma
                        if i > 0:
                            first_lon2, first_lat2, _ = geod.fwd(first_lon2, first_lat2, 90, interval * i)
                            left_lon2, left_lat2, _ = geod.fwd(left_lon2, left_lat2, 90, interval * i)
                            down_lon2, down_lat2, _ = geod.fwd(down_lon2, down_lat2, 90, interval * i)
                            fw_lon, fw_lat, _ = geod.fwd(fw_lon, fw_lat, 90, interval * i)
                            right_lon2, right_lat2, _ = geod.fwd(right_lon2, right_lat2, 90, interval * i)

                        self.waypoints.append((round(right_lat2, 7), round(right_lon2, 7), self.main_alt))
                        self.waypoints.append((round(down_lat2, 7), round(down_lon2, 7), self.main_alt))
                        self.waypoints.append((round(left_lat2, 7), round(left_lon2, 7), self.main_alt))      
                        
                        

        elif distance == vertical:
            for i in range(num_intervals-1):
                for j, (start_lat, start_lon, end_lat, end_lon) in enumerate(start_end_points):
                    if j == 0:
                        segment_distance = interval
                        fwd_azimuth, _, _ = geod.inv(start_lon, start_lat, end_lon, end_lat)
                        first_lon1, first_lat1, _ = geod.fwd(start_lon, start_lat, fwd_azimuth, segment_distance)
                        left_lon1, left_lat1, _ = geod.fwd(first_lon1, first_lat1, 225, interval*sqrt(2))
                        right_lon1, right_lat1, _ = geod.fwd(first_lon1, first_lat1, 315, interval*sqrt(2))
                        
                        # Yukarı kaydırma
                        if i > 0:
                            first_lon1, first_lat1, _ = geod.fwd(first_lon1, first_lat1, 0, interval * i)
                            left_lon1, left_lat1, _ = geod.fwd(left_lon1, left_lat1, 0, interval * i)
                            right_lon1, right_lat1, _ = geod.fwd(right_lon1, right_lat1, 0, interval * i)
                

                        self.waypoints.append((round(left_lat1, 7), round(left_lon1, 7), self.main_alt))
                        self.waypoints.append((round(first_lat1, 7), round(first_lon1, 7), self.main_alt))
                        self.waypoints.append((round(right_lat1, 7), round(right_lon1, 7), self.main_alt))                                   

                    elif j == 1:
                        segment_distance = (interval) - (interval/2)
                        fwd_azimuth, _, _ = geod.inv(start_lon, start_lat, end_lon, end_lat)
                        first_lon2, first_lat2, _ = geod.fwd(start_lon, start_lat, fwd_azimuth, segment_distance)
                        upp1_lon2, upp1_lat2, _ = geod.fwd(first_lon2, first_lat2, 0, interval)
                        upp2_lon2, upp2_lat2, _ = geod.fwd(upp1_lon2, upp1_lat2, 45, interval*sqrt(2))
                        down_lon2, down_lat2, _ = geod.fwd(upp1_lon2, upp1_lat2, 135, interval*sqrt(2))


                        # Yukarı kaydırma
                        if i > 0:
                            first_lon2, first_lat2, _ = geod.fwd(first_lon2, first_lat2, 0, interval * i)
                            upp1_lon2, upp1_lat2, _ = geod.fwd(upp1_lon2, upp1_lat2, 0, interval * i)
                            upp2_lon2, upp2_lat2, _ = geod.fwd(upp2_lon2, upp2_lat2, 0, interval * i)
                            down_lon2, down_lat2, _ = geod.fwd(down_lon2, down_lat2, 0, interval * i)
                        
                        self.waypoints.append((round(upp2_lat2, 7), round(upp2_lon2, 7), self.main_alt))
                        self.waypoints.append((round(upp1_lat2, 7), round(upp1_lon2, 7), self.main_alt))
                        self.waypoints.append((round(down_lat2, 7), round(down_lon2, 7), self.main_alt))


        for i, waypoint in enumerate(self.waypoints):
            #print(f"Waypoint {i + 1}: {waypoint}")
            folium.Marker(
                location=[waypoint[0],waypoint[1]],
                popup=f'Waypoint {i + 1}',
                icon=folium.Icon(color='blue')
            ).add_to(self.m)
        folium.PolyLine([(waypoint[0], waypoint[1]) for waypoint in self.waypoints], color="orange").add_to(self.m)
        self.m.save('map.html')
        
        # Kullanıcıdan alınan koordinatlar dosyaya kaydedilir.
        os.remove('waypoints.csv')
        with open('waypoints.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Latitude', 'Longitude', 'Altitude'])
            writer.writerows(self.waypoints)
        self.run_terminal_command()
        self.close()

    def varsayilanDevam(self):
        main_alt = self.ayarlar.altitude.text()
        self.koordinatlar = [
            (-35.35929465, 149.16130371, main_alt),
            (-35.35896261, 149.16783542, main_alt),
            (-35.36088830, 149.16932726, main_alt),
            (-35.36187063, 149.16072341, main_alt)
        ]
        os.remove('koordinatlar.csv')
        with open('koordinatlar.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Latitude', 'Longitude', 'Altitude'])
            writer.writerows(self.koordinatlar)
        self.run_terminal_command()
        self.close()

    def run_terminal_command(self):
        system = platform.system()
        if system == "Linux":
            try:
                subprocess.run(['gnome-terminal', '--', 'python', 'arayuz_kod.py'], check=True)
                subprocess.run(['gnome-terminal', '--', 'python', 'harita_kod.py'], check=True)
            except FileNotFoundError:
                subprocess.run(['x-terminal-emulator', '-e', 'python arayuz_kod.py'], check=True)
                subprocess.run(['x-terminal-emulator', '-e', 'python harita_kod.py'], check=True)
        elif system == "Windows":
            subprocess.run(['cmd', '/c', 'start', 'cmd', '/k', 'python arayuz_kod.py'], check=True)
            subprocess.run(['cmd', '/c', 'start', 'cmd', '/k', 'python harita_kod.py'], check=True)
        else:
            print(f"Unsupported operating system: {system}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main()
    window.show()
    sys.exit(app.exec_()) 