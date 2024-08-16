from pymavlink import mavutil
import sys
import time
from PyQt5.QtCore import *
import csv
from PyQt5.QtWidgets import QMessageBox
from pymavlink import mavwp
import os

class saerotech():
    def baglan(self, adres, baudrate):
        self.vehicle = mavutil.mavlink_connection(adres, baud=baudrate)
        msgbaglandi = "Connected Successfully."
        msgbaglanamadi = "Connection Failed."

        if self.vehicle.wait_heartbeat():
            self.previous_wp = 0
            self.previous_wp_kalan_mesafe = 0
            self.previous_yatıs_acisi = 0
            self.previous_altitude = 0
            self.previous_latitude = 0
            self.previous_longitude = 0
            self.previous_hava_hizi = 0
            self.previous_dikey_hiz = 0
            self.previous_heading = 0
            self.previous_groundspeed = 0
            self.previous_batarya = 0
            return msgbaglandi
        else:
            return msgbaglanamadi
            
    def baglanma_durumu_gonder(self):
        return self.baglanti_durumu
    
    def mode_change(self, mode):
        # Check if mode is available
        if mode not in self.vehicle.mode_mapping():
            print('Unknown mode : {}'.format(mode))
            print('Try:', list(self.vehicle.mode_mapping().keys()))
            sys.exit(1)

        # Get mode ID
        mode_id = self.vehicle.mode_mapping()[mode]
        self.vehicle.mav.set_mode_send(
            self.vehicle.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id)
        print(f"Vehicle mode setted {mode}")

    def veri_cek(self):
        msg_GLOBAL_POSITION_INT = self.vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
        msg_VFR_HUD = self.vehicle.recv_match(type='VFR_HUD', blocking=False)
        msg_BATTERY = self.vehicle.recv_match(type='SYS_STATUS', blocking=False)
        msg_NAV_CONTROLLER_OUTPUT = self.vehicle.recv_match(type='NAV_CONTROLLER_OUTPUT', blocking=False)
        msg_MISSION_CURRENT = self.vehicle.recv_match(type='MISSION_CURRENT', blocking=False)

        if msg_MISSION_CURRENT is not None:
            self.mevcut_wp = msg_MISSION_CURRENT.seq
            self.previous_wp = self.mevcut_wp
        else:
            self.mevcut_wp = self.previous_wp

        if msg_NAV_CONTROLLER_OUTPUT is not None:
            self.wp_kalan_mesafe = msg_NAV_CONTROLLER_OUTPUT.wp_dist
            self.yatıs_acisi = msg_NAV_CONTROLLER_OUTPUT.nav_roll
            self.previous_wp_kalan_mesafe = self.wp_kalan_mesafe
            self.previous_yatıs_acisi = self.yatıs_acisi
        else:
            self.wp_kalan_mesafe = self.previous_wp_kalan_mesafe
            self.yatıs_acisi = self.previous_yatıs_acisi

        if msg_GLOBAL_POSITION_INT is not None:
            self.altitude = msg_GLOBAL_POSITION_INT.relative_alt / 1000
            self.latitude = msg_GLOBAL_POSITION_INT.lat / 1e7
            self.longitude = msg_GLOBAL_POSITION_INT.lon / 1e7
            self.previous_altitude = self.altitude
            self.previous_latitude = self.latitude
            self.previous_longitude = self.longitude

        else:
            self.altitude = self.previous_altitude
            self.latitude = self.previous_latitude
            self.longitude = self.previous_longitude

        if msg_VFR_HUD is not None:
            self.hava_hizi = msg_VFR_HUD.airspeed
            self.dikey_hiz = msg_VFR_HUD.climb
            self.heading = msg_VFR_HUD.heading
            self.groundspeed = msg_VFR_HUD.groundspeed
            self.previous_hava_hizi = self.hava_hizi
            self.previous_dikey_hiz = self.dikey_hiz
            self.previous_heading = self.heading
            self.previous_groundspeed = self.groundspeed
        else:
            self.hava_hizi = self.previous_hava_hizi
            self.dikey_hiz = self.previous_dikey_hiz
            self.heading = self.previous_heading
            self.groundspeed = self.previous_groundspeed

        if msg_BATTERY is not None:
            self.batarya = msg_BATTERY.battery_remaining
            self.previous_batarya = self.batarya
        else:
            self.batarya = self.previous_batarya

    def mevcut_wp_gonder(self):
        return self.mevcut_wp

    def wp_dist_gonder(self):
        return self.wp_kalan_mesafe

    def veri_cekme(self):
        self.mevcut_wp = 0
        self.wp_kalan_mesafe = 0
        self.yatıs_acisi = 0
        self.altitude = 0
        self.latitude = 0
        self.longitude = 0
        self.hava_hizi = 0
        self.dikey_hiz = 0
        self.heading = 0
        self.groundspeed = 0
        self.batarya = 0

    def mod_dondur(self):
        msg_HEARTBEAT = None
        while msg_HEARTBEAT is None:
            msg_HEARTBEAT = self.vehicle.recv_match(type='HEARTBEAT', blocking=False)
            if msg_HEARTBEAT is None:
                time.sleep(0.1)
        self.arac_modu = mavutil.mode_string_v10(msg_HEARTBEAT)
        self.armed = msg_HEARTBEAT.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        
    def arm_durumu_gonder(self):
        return self.armed

    def arac_modu_gonder(self):
        return self.arac_modu
    
    def yatis_acisi_gonder(self):
        return self.yatıs_acisi

    def altitude_gonder(self):
        return self.altitude
    
    def hava_hizi_gonder(self):
        return round(self.hava_hizi, 3)
    
    def dikey_hiz_gonder(self):
        return round(self.dikey_hiz, 3)
    
    def latitude_gonder(self):
        return self.latitude
    
    def longitude_gonder(self):
        return self.longitude
    
    def home_lat_gonder(self):
        return self.home_lat
    
    def home_lon_gonder(self):
        return self.home_lon

    def heading_gonder(self):
        return self.heading
    
    def groundspeed_gonder(self):
        return (round(self.groundspeed, 3))

    def battery_gonder(self):
        return self.batarya

    def set_home_position(self):
        msg = self.vehicle.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        if msg:
            latitude = msg.lat/ 1e7
            longitude = msg.lon/ 1e7
            altitude = msg.alt/ 1e3
            
            msg_home = self.vehicle.mav.command_long_encode(
                self.vehicle.target_system, self.vehicle.target_component, 
                mavutil.mavlink.MAV_CMD_DO_SET_HOME ,  
                0,  
                0, 0, 0, 0,  
                latitude,  
                longitude,  
                altitude)  
            time.sleep(2)
            self.vehicle.mav.send(msg_home)
            msgbasarili = "Ev konumu ",msg_home.param5, msg_home.param6, msg_home.param7, "noktasına ayarlandı."
            return msgbasarili

    def arm(self):
        self.vehicle.mav.command_long_send(
            self.vehicle.target_system,
            self.vehicle.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,
            1, # 1 = arm, 0 = disarm
            0, 0, 0, 0, 0, 0
        )

    def goo(self,main_alt):
        msg = self.vehicle.mav.command_long_encode(
        self.vehicle.target_system, self.vehicle.target_component, 
        mavutil.mavlink.MAV_CMD_GET_HOME_POSITION,  
        0, 0, 0, 0, 0, 0, 0, 0  
        )
        time.sleep(2)
        self.vehicle.mav.send(msg)
        
        msg1 = self.vehicle.recv_match(type='HOME_POSITION', blocking=True)  
        
        self.home_lat = msg1.latitude / 1e7
        self.home_lon = msg1.longitude / 1e7

        waypoints = [
            (self.home_lat, self.home_lon, 0),
            (self.home_lat, self.home_lon, main_alt)
        ]
        
        koordinatlar = []
        with open('waypoints.csv', 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Başlık satırını atla
            for row in reader:
                koordinatlar.append((float(row[0]), float(row[1]), float(row[2])))

        loop1 = int(len(koordinatlar))
        for i, (lat, lon, alt) in enumerate(koordinatlar):
            waypoints.append((lat, lon, alt))  # Koordinatları ekleyin
            if i == loop1 - 1:  # Son koordinat ise
                waypoints.append((self.home_lat, self.home_lon, 0))  # Ev koordinatını ekleyin

        print(waypoints)

        target_system = self.vehicle.target_system
        target_component = self.vehicle.target_component

        wp = mavwp.MAVWPLoader()
        loop2 = wp.count() - 1

        for i, (lat, lon, alt) in enumerate(waypoints):
            if i == 1:
                # İlk waypoint takeoff için
                seq = i
                frame = mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT  # Görev çerçevesi
                command = mavutil.mavlink.MAV_CMD_NAV_VTOL_TAKEOFF  # Görev komutu
                current = 1  # Mevcut görev işareti
                autocontinue = 1  # Otomatik devam et
                param1 = 0  # Parametre 1
                param2 = 0  # Parametre 2
                param3 = 0  # Parametre 3
                param4 = 0  # Parametre 4
                x = int(lat * 1e7)  # Enlem (latitude)
                y = int(lon * 1e7)  # Boylam (longitude)
                z = int(alt)  # İrtifa (metre cinsinden)
                mission_type = mavutil.mavlink.MAV_MISSION_TYPE_MISSION  # Görev türü

                # MISSION_ITEM_INT mesajı
                msg2 = mavutil.mavlink.MAVLink_mission_item_int_message(
                    target_system, target_component, seq, frame, command, current,
                    autocontinue, param1, param2, param3, param4, x, y, z, mission_type
                )
                print("Takeoff waypoint", i+1, "sent to vehicle")
                self.vehicle.mav.send(msg2)

            elif i == loop2:
                # Son waypoint vtol land
                seq = i
                frame = mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT  # Görev çerçevesi
                command = mavutil.mavlink.MAV_CMD_NAV_VTOL_LAND  # Görev komutu
                current = 1  # Mevcut görev işareti
                autocontinue = 1  # Otomatik devam et
                param1 = 0  # Parametre 1
                param2 = 0  # Parametre 2
                param3 = 0  # Parametre 3
                param4 = 0  # Parametre 4
                x = int(lat * 1e7)  # Enlem (latitude)
                y = int(lon * 1e7)  # Boylam (longitude)
                z = int(alt)  # İrtifa (metre cinsinden)
                mission_type = mavutil.mavlink.MAV_MISSION_TYPE_MISSION  # Görev türü

                # MISSION_ITEM_INT mesajı
                msg2 = mavutil.mavlink.MAVLink_mission_item_int_message(
                    target_system, target_component, seq, frame, command, current,
                    autocontinue, param1, param2, param3, param4, x, y, z, mission_type
                )
                print("Land waypoint", i+1, "sent to vehicle")
                self.vehicle.mav.send(msg2)

            elif i != 1 and i != loop2:
                # Diğer waypoint'ler normal görev olarak
                seq = i
                frame = mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT  # Görev çerçevesi
                command = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT  # Görev komutu
                current = 0  # Mevcut görev işareti
                autocontinue = 1  # Otomatik devam et
                param1 = 0  # Parametre 1
                param2 = 10  # Parametre 2
                param3 = 0  # Parametre 3
                param4 = 0  # Parametre 4
                x = int(lat * 1e7)  # Enlem (latitude)
                y = int(lon * 1e7)  # Boylam (longitude)
                z = int(alt)  # İrtifa (metre cinsinden)
                mission_type = mavutil.mavlink.MAV_MISSION_TYPE_MISSION  # Görev türü

                # MISSION_ITEM_INT mesajı
                msg2 = mavutil.mavlink.MAVLink_mission_item_int_message(
                    target_system, target_component, seq, frame, command, current,
                    autocontinue, param1, param2, param3, param4, x, y, z, mission_type
                )

                if msg2:
                    self.vehicle.mav.send(msg2)
                    print("Waypoint", i+1 ,"VTOL aracınıza gönderildi.")
                else:
                    print(msg2)
                    print("\nWaypoint mesajı oluşturulamadı.")
                    
            wp.add(msg2)

        # Waypoints'leri gönderme
        self.vehicle.waypoint_clear_all_send()
        self.vehicle.waypoint_count_send(wp.count())
        print("Mission count sent",wp.count())

        for i in range(wp.count()):
            msg = self.vehicle.recv_match(type=['MISSION_REQUEST'], blocking=True)
            self.vehicle.mav.send(wp.wp(msg.seq))

    def start_mission(self):
        
        # Aracı otomatik moda geçir
        msg = self.vehicle.mav.command_long_encode(
            self.vehicle.target_system,
            self.vehicle.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,
            mavutil.mavlink.MAV_MODE_AUTO_ARMED,
            0, 0, 0, 0, 0, 0
        )
        self.vehicle.mav.send(msg)
    
        # Otomatik moda geçene kadar bekle
        while True:
            ack_msg = self.vehicle.recv_match(type='COMMAND_ACK', blocking=False)
            if ack_msg and ack_msg.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE and ack_msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print("Vehicle is now in AUTO mode.")
                break
            
        msg1 = self.vehicle.mav.command_long_encode(
            0,                                          
            0,                                          
            mavutil.mavlink.MAV_CMD_MISSION_START,     
            0,                                          
            0,                                          
            0,                                          
            0,                                          
            0,                                          
            0,                                          
            0,                                          
            0                                           
        )

        if msg1:
            self.vehicle.mav.send(msg1)
            print("Mission Started.")
        else:
            print("Cannot create Mission start message.")

        self.mission_started = True

    def gorev_bitti(self):
        target_system = self.vehicle.target_system
        target_component = self.vehicle.target_component
        mission_type = mavutil.mavlink.MAV_MISSION_TYPE_MISSION

        # MISSION_CLEAR_ALL mesajını gönder
        self.vehicle.mav.mission_clear_all_send(target_system, target_component, mission_type)
        self.mission_started = False
