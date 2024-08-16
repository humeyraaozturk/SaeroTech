from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from arayuz_python import Ui_MainWindow
from otonom_kod import saerotech
import sys
import threading
import time
import glob
import serial
#import vlc

class main(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.baglanti = False
        self.gorev_basladi = False
        self.baslat_basildi = False
        self.speed = 0
        self.yukseklik = 0
        self.dikey_hiz = 0
        self.home_lat = 0
        self.home_lon = 0
        self.latitude = 0
        self.longitude = 0
        self.heading = 0
        self.groundspeed = 0
        self.hedef_irtifa = 20
        self.yatis_acisi = 0
        self.batarya = 0
        self.ucus_sayisi = 0
        self.kalan_mesafe = 0
        self.mevcut_wp = 0
        # self.showFullScreen()
        self.showNormal()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(50)
        self.ui.btnConnect.clicked.connect(self.aracabaglan)
        self.ui.btnBaslat.clicked.connect(self.gorevbaslat)
        self.ui.btnRTL.clicked.connect(self.RTL)
        self.running = True
        self.mod_thread = threading.Thread(target=self.mod_dondur_loop)
        self.arm_edildi = False
        self.gorev_bitti = False
        self.populate_combobox()

        #self.instance = vlc.Instance()
        #self.mediaPlayer = self.instance.media_player_new()

        #self.ui.btnConnect.clicked.connect(self.playVideo)
        

    #def playVideo(self):
    #    # Video dosyasının yolu
    #    video_path = 'video.mp4'
    #
    #    # Media oluşturuluyor ve oynatıcıya atanıyor
    #    self.media = self.instance.media_new(video_path)
    #    self.mediaPlayer.set_media(self.media)
    #
    #    # Video frame'i VLC player'a bağlanıyor
    #    self.mediaPlayer.set_hwnd(int(self.ui.kamera_frame.winId()))
    #
    #    # Video oynatılıyor
    #    self.mediaPlayer.play()
    #    self.timer.start()


    def get_active_ports(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        result.append('tcp:127.0.0.1:5762')
        result.append('127.0.0.1:14550')
        return result
    
    def populate_combobox(self):
        ports = self.get_active_ports()
        self.ui.adress_combo.clear()
        for port in ports:
            self.ui.adress_combo.addItem(port)

    def mod_dondur_loop(self):
        while self.running:
            self.mod_calistir()
            time.sleep(1)

    def stop(self):
        self.running = False
        self.mod_thread.join()

    def mod_calistir(self):
        saerotech.mod_dondur(self)

    def mod_yazdir(self):
        if self.baglanti:
            self.aracmodu = saerotech.arac_modu_gonder(self)
            self.arm = saerotech.arm_durumu_gonder(self)
            self.ui.lblMOD.setText(self.aracmodu)
            if self.arm == 128 and self.arm_edildi == False and self.gorev_basladi == True:
                self.ui.lblDurum.setText("ARM Edildi")
                saerotech.start_mission(self)
                self.arm_edildi = True
            if self.arm == 128 and self.gorev_basladi == True and self.aracmodu == 'AUTO':
                self.ui.lblDurum.setText("Görev Başlatıldı")
            if self.arm == 0 and self.arm_edildi == True and self.gorev_basladi == True:
                self.arm_edildi = False
                self.gorev_basladi = False
                self.ui.lblDurum.setText("Görev Tamamlandı")
                saerotech.mode_change(self, "GUIDED")
                #saerotech.gorev_bitti(self)
                self.ui.lblDurum.setText("Görevler temizlendi")

    def RTL(self):
        saerotech.mode_change(self, "QRTL")
        
    def aracabaglan(self):
        baud_rate = self.ui.baud_combo.currentText()
        adress = self.ui.adress_combo.currentText()
        #adress = 'tcp:localhost:14550'
        vehicle_adress = adress
        try:
            baglanma_durumu = saerotech.baglan(self, vehicle_adress, baud_rate)
            if baglanma_durumu == "Connected Successfully.":
                self.ui.lblDurum.setText(baglanma_durumu)
                self.baglanti = True
                self.mod_thread.start()
                time.sleep(1)
                saerotech.mode_change(self, "GUIDED")
                saerotech.set_home_position(self)
                saerotech.goo(self,self.hedef_irtifa)
            else:
                raise Exception("Connection Failed.")
                
        except Exception as e:
            self.ui.lblDurum.setText("Bağlantı hatası: " + str(e))
            self.baglanti = False
            QMessageBox.critical(self, "Bağlantı Hatası", "Araca bağlanırken bir hata oluştu:\n" + str(e))

    def gorevbaslat(self):
        self.ui.lblDurum.setText("Görev Başlatılıyor.")
        saerotech.mode_change(self, "GUIDED")
        if self.baglanti:
            saerotech.arm(self)
            saerotech.mode_change(self, "AUTO")
            saerotech.start_mission(self)
            self.gorev_basladi = True

    def update_display(self):
        if self.baglanti:
            saerotech.veri_cek(self)
            self.mod_yazdir()
            self.yukseklik = saerotech.altitude_gonder(self)
            self.home_lat = saerotech.home_lat_gonder(self)
            self.home_lon = saerotech.home_lon_gonder(self)
            self.speed = saerotech.hava_hizi_gonder(self)
            self.dikey_hiz = saerotech.dikey_hiz_gonder(self)
            self.latitude = saerotech.latitude_gonder(self)
            self.longitude = saerotech.longitude_gonder(self)
            self.heading = saerotech.heading_gonder(self)
            self.groundspeed = saerotech.groundspeed_gonder(self)
            self.batarya = saerotech.battery_gonder(self)
            self.ui.lblBatarya.setText(str(self.batarya))
            self.kalan_mesafe = saerotech.wp_dist_gonder(self)
            self.ui.lblKalanMesafe.setText(str(self.kalan_mesafe) + ' m')
            self.mevcut_wp = saerotech.mevcut_wp_gonder(self)
            self.ui.lblMevcutWaypoint_2.setText(str(self.mevcut_wp))
            self.yatis_acisi = saerotech.yatis_acisi_gonder(self)
            self.ui.lblKalanMesafe.update()
            self.ui.lblMevcutWaypoint_2.update()
            self.ui.lblBatarya.update()
            self.ui.altimetre_widget.update()
            self.ui.yatay_hiz_widget.update()
            self.ui.groundspeed_widget.update()
            self.ui.dikey_hiz_widget.update()
            self.ui.pusula_widget.update()
            self.ui.ufuk_widget.update()
        elif self.baglanti == False:
            saerotech.veri_cekme(self)

    def keyPressEvent(self, event):
        pass

    def main_tasarim(self, painter):
        yukseklik = self.height()
        genislik = self.width()
        rect = QRectF(0, 0, genislik, yukseklik)  # Sol üst köşe (0, 0) ve boyutları pencerenin genişliği ve yüksekliği
        painter.setBrush(QBrush(QColor(16, 24, 45)))  
        painter.drawRect(rect)

        gorsel = QImage("contents/koyu_logo2.png")

        # Görsel boyutlarını elde et
        gorsel_genislik = gorsel.width()
        gorsel_yukseklik = gorsel.height()

        # Pencere boyutları için döngüler
        for y in range(0, yukseklik, gorsel_yukseklik):
            for x in range(0, genislik, gorsel_genislik):
                # Görseli her bir x ve y koordinatında çiz
                painter.drawImage(x, y, gorsel)

    def yatay_hiz_gostergesi_ciz(self, painter: QPainter):
        maks_yukseklik = 40
        dongu_sayisi = maks_yukseklik//5
        dondurme_acisi = 360/(maks_yukseklik/5)
        acimsi = 108-dondurme_acisi

        # Yazı Fontu Ayarları
        number_font = QFont("Consolas", 0, 0, True)
        number_font.setPixelSize(15)
        number_fm = QFontMetrics(number_font)
        number_rect = number_fm.boundingRect("000.000")
        painter.setFont(number_font)

        self.yatay_rect = QRectF(self.ui.yatay_hiz_widget.geometry())

        conicalGradient = QConicalGradient(QPointF(self.yatay_rect.width()/2, self.yatay_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        pusula_kabuk = self.yatay_rect.toRect()
        pusula_kabuk.setSize(QSizeF(self.yatay_rect.width()*0.975, self.yatay_rect.width()*0.975).toSize())
        pusula_kabuk.moveCenter(self.yatay_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(pusula_kabuk, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.yatay_rect)

        painter.save()
        gorsel = QImage("contents/neon5.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.yatay_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.yatay_rect, gorsel)
        painter.restore()

        # Sayıların ve Çizgilerin Çizimi
        center = self.yatay_rect.center()

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 5))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate((30-(360/30)))
        painter.translate(-center.x(), -center.y())

        for a in range(0, dongu_sayisi):
            painter.translate(center.x(), center.y())
            painter.rotate(360/8)
            painter.translate(-center.x(), -center.y())
            # spike
            spike_p1 = center+QPointF(0, self.yatay_rect.height()//2)
            spike_p2 = center+QPointF(0, self.yatay_rect.height()*0.45)
            painter.drawLine(spike_p1, spike_p2)
            # sayilar
            sayi_konum = spike_p2.toPoint()-QPoint(0, 12)
            painter.save()
            painter.translate(sayi_konum.x(), sayi_konum.y())
            painter.rotate(a*-dondurme_acisi-acimsi)
            painter.translate(-sayi_konum.x(), -sayi_konum.y())
            number_rect.moveCenter(sayi_konum)
            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str((a)*5))
            painter.restore()
        painter.restore()
        
        painter.save()
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 4):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.yatay_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.yatay_rect.height() * 0.45)
            painter.drawLine(spike_p1, spike_p2)
        

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 55)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 24):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.yatay_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.yatay_rect.height() * 0.45)
            if a != 4 and a != 9 and a != 14 and a != 19:
                painter.drawLine(spike_p1, spike_p2)
        
        
        painter.setPen(QPen(QGradient(QGradient.Preset.RedSalvation), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 52.5)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 9):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.yatay_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.yatay_rect.height() * 0.45)
            if a != 4:
                painter.drawLine(spike_p1, spike_p2)
        painter.restore()
        
        # Yuksekligin String Deger Olarak Yazilmasi
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 25))
        speed_font = QFont("Georgia", 0, 0, True)
        speed_font.setPixelSize(12)
        speed_fm = QFontMetrics(speed_font)

        # M Cinsinden Yukseklik
        speed_kmph_rect = speed_fm.boundingRect("000.000-m/s")
        painter.setFont(speed_font)
        speed_kmph_rect.moveCenter(center.toPoint())
        speed_kmph_rect.moveBottom(round(self.yatay_rect.bottom() - 40))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        painter.drawText(speed_kmph_rect, Qt.AlignmentFlag.AlignCenter, f'{self.speed} m/s')

        #Gosterge Ismi
        painter.drawText(round(self.yatay_rect.center().x() - 29), round(self.yatay_rect.top() + 50),  'Hava Hızı')
        painter.restore()

        # Gösterge Çubuğunun Çizilmesi
        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 0.3, cap=Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QGradient(QGradient.Preset.FebruaryInk)))
        hand_polygon = QPolygonF((center + QPoint(0, 5), center + QPoint(0, -5), center + QPoint(55, 0)))
        
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(152+(360/40)*self.speed)
        painter.translate(-center.x(), -center.y())
        painter.drawPolygon(hand_polygon)
        painter.restore()

        # İç Daireyi Oluşturma
        painter.setPen(QPen(QGradient(QGradient.Preset.CrystalRiver), 20, cap=Qt.PenCapStyle.RoundCap))
        painter.drawPoint(self.yatay_rect.center().toPoint())

    def ufuk_gostergesi_ciz(self, painter: QPainter):
        self.ufuk_rect = QRectF(self.ui.ufuk_widget.geometry())
        center = self.ufuk_rect.center()

        conicalGradient = QConicalGradient(QPointF(self.ufuk_rect.width()/2, self.ufuk_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        pusula_kabuk = self.ufuk_rect.toRect()
        pusula_kabuk.setSize(QSizeF(self.ufuk_rect.width()*0.975, self.ufuk_rect.width()*0.975).toSize())
        pusula_kabuk.moveCenter(self.ufuk_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(pusula_kabuk, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.ufuk_rect)

        # Dış Kabuk Oluşturma
        conicalGradient = QConicalGradient(QPointF(self.ufuk_rect.width()/2, self.ufuk_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        ufuk_kabuk = self.ufuk_rect.toRect()
        ufuk_kabuk.setSize(QSizeF(self.ufuk_rect.width()*0.975, self.ufuk_rect.width()*0.975).toSize())
        ufuk_kabuk.moveCenter(self.ufuk_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(10, 122, 150)))

        gorsel = QImage("contents/ufuk_neon-cropped.jpg")
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(self.yatis_acisi)
        painter.translate(-center.x(), -center.y())
        painter.drawImage(self.ufuk_rect, gorsel)
        painter.restore()

        painter.save()
        gorsel = QImage("contents/neon.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.ufuk_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.ufuk_rect, gorsel)
        painter.restore()

    def altimetre_ciz(self, painter: QPainter):
        maks_yukseklik = 120
        dongu_sayisi = maks_yukseklik//10
        dondurme_acisi = 360/(maks_yukseklik/10)
        acimsi = 120-dondurme_acisi

        # Yazı Fontu Ayarları
        number_font = QFont("Consolas", 0, 0, True)
        number_font.setPixelSize(15)
        number_fm = QFontMetrics(number_font)
        number_rect = number_fm.boundingRect("000.000")
        painter.setFont(number_font)

        self.alti_rect = QRectF(self.ui.altimetre_widget.geometry())

        conicalGradient = QConicalGradient(QPointF(self.alti_rect.width()/2, self.alti_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        pusula_kabuk = self.alti_rect.toRect()
        pusula_kabuk.setSize(QSizeF(self.alti_rect.width()*0.975, self.alti_rect.width()*0.975).toSize())
        pusula_kabuk.moveCenter(self.alti_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(pusula_kabuk, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.alti_rect)

        painter.save()
        gorsel = QImage("contents/neon5.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.alti_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.alti_rect, gorsel)
        painter.restore()

        # Sayıların ve Çizgilerin Çizimi
        center = self.alti_rect.center()

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 5))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(60)
        painter.translate(-center.x(), -center.y())
        for a in range(0, dongu_sayisi):
            painter.translate(center.x(), center.y())
            painter.rotate(360/12)
            painter.translate(-center.x(), -center.y())
            # spike
            spike_p1 = center+QPointF(0, self.alti_rect.height()//2)
            spike_p2 = center+QPointF(0, self.alti_rect.height()*0.45)
            painter.drawLine(spike_p1, spike_p2)
            # sayilar
            sayi_konum = spike_p2.toPoint()-QPoint(0, 12)
            painter.save()
            painter.translate(sayi_konum.x(), sayi_konum.y())
            painter.rotate(a*-dondurme_acisi-acimsi)
            painter.translate(-sayi_konum.x(), -sayi_konum.y())
            number_rect.moveCenter(sayi_konum)
            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str((a)*10))
            painter.restore()
        painter.restore()
        
        painter.save()
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 1))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 3)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 14):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.alti_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.alti_rect.height() * 0.45)
            painter.drawLine(spike_p1, spike_p2)
        

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 1))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 90)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 100):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.alti_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.alti_rect.height() * 0.45)
            if a != 4 and a != 9 and a != 14 and a != 19:
                painter.drawLine(spike_p1, spike_p2)
        
        
        painter.setPen(QPen(QGradient(QGradient.Preset.RedSalvation), 1))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 93)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 4):
            painter.translate(center.x(), center.y())
            painter.rotate(3)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.alti_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.alti_rect.height() * 0.45)
            if a != 4:
                painter.drawLine(spike_p1, spike_p2)
        painter.restore()
        
        # Yuksekligin String Deger Olarak Yazilmasi
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 25))
        speed_font = QFont("Georgia", 0, 0, True)
        speed_font.setPixelSize(12)
        speed_fm = QFontMetrics(speed_font)

        # M Cinsinden Yukseklik
        speed_kmph_rect = speed_fm.boundingRect("0000000-m")
        painter.setFont(speed_font)
        speed_kmph_rect.moveCenter(center.toPoint())
        speed_kmph_rect.moveBottom(round(self.alti_rect.bottom() - 40))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        painter.drawText(speed_kmph_rect, Qt.AlignmentFlag.AlignCenter, f'{self.yukseklik} m')

        #Gosterge Ismi
        painter.drawText(round(self.alti_rect.center().x() - 29), round(self.alti_rect.top() + 50),  'Yükseklik')
        painter.restore()

        # Gösterge Çubuğunun Çizilmesi
        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 0.3, cap=Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QGradient(QGradient.Preset.FebruaryInk)))
        hand_polygon = QPolygonF((center + QPoint(0, 5), center + QPoint(0, -5), center + QPoint(55, 0)))
        
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(180+(360/120)*self.yukseklik)
        painter.translate(-center.x(), -center.y())
        painter.drawPolygon(hand_polygon)
        painter.restore()

        # İç Daireyi Oluşturma
        painter.setPen(QPen(QGradient(QGradient.Preset.CrystalRiver), 20, cap=Qt.PenCapStyle.RoundCap))
        painter.drawPoint(self.alti_rect.center().toPoint())

    def dikey_hiz_gostergesi_ciz(self, painter: QPainter):
        # Yazı Fontu Ayarları
        number_font = QFont("Consolas", 0, 0, True)
        number_font.setPixelSize(15)
        number_fm = QFontMetrics(number_font)
        number_rect = number_fm.boundingRect("000.000")
        painter.setFont(number_font)
        self.dikey_rect = QRectF(self.ui.dikey_hiz_widget.geometry())

        conicalGradient = QConicalGradient(QPointF(self.dikey_rect.width()/2, self.dikey_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        dikey_kabuk = self.dikey_rect.toRect()
        dikey_kabuk.setSize(QSizeF(self.dikey_rect.width()*0.975, self.dikey_rect.width()*0.975).toSize())
        dikey_kabuk.moveCenter(self.dikey_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(dikey_kabuk, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.dikey_rect)

        painter.save()
        gorsel = QImage("contents/neon5.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.dikey_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.dikey_rect, gorsel)
        painter.restore()

        center = self.dikey_rect.center()

        # Sayıların ve Çizgilerin Çizimi
        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 5))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 9):
            painter.translate(center.x(), center.y())
            painter.rotate(45)
            painter.translate(-center.x(), -center.y())
            # spike
            spike_p1 = center + QPointF(0, self.dikey_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.dikey_rect.height() * 0.45)
            painter.drawLine(spike_p1, spike_p2)
        painter.restore()
        
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(45)  
        painter.translate(-center.x(), -center.y())
        for a in range(0, 5):
            painter.translate(center.x(), center.y())
            painter.rotate(45)  
            painter.translate(-center.x(), -center.y())
            sayi_konum = spike_p2.toPoint()-QPoint(0, 12)
            painter.save()
            painter.translate(sayi_konum.x(), sayi_konum.y())
            painter.rotate(-45*(a + 2))
            painter.translate(-sayi_konum.x(), -sayi_konum.y())
            number_rect.moveCenter(sayi_konum)
            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str((a)*3))
            painter.restore()
        painter.restore()

        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(90)  
        painter.translate(-center.x(), -center.y())
        for a in range(1, 4):
            painter.translate(center.x(), center.y())
            painter.rotate(-45)  
            painter.translate(-center.x(), -center.y())
            # sayilar
            sayi_konum = spike_p2.toPoint()-QPoint(0, 12)
            painter.save()
            painter.translate(sayi_konum.x(), sayi_konum.y())
            painter.rotate(45*(a-2))
            painter.translate(-sayi_konum.x(), -sayi_konum.y())
            number_rect.moveCenter(sayi_konum)
            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str((a)*3))
            painter.restore()
        painter.restore()

        painter.save()
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        for a in range(1, 41):
            if a != 9 and a != 18 and a !=27 and a !=36:
                painter.translate(center.x(), center.y())
                painter.rotate(5)
                painter.translate(-center.x(), -center.y())
                spike_p1 = center + QPointF(0, self.dikey_rect.height() // 2)
                spike_p2 = center + QPointF(0, self.dikey_rect.height() * 0.45)
                painter.drawLine(spike_p1, spike_p2)
        painter.restore()
        
        # Hizin String Deger Olarak Yazilmasi
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 25))
        speed_font = QFont("Georgia", 0, 0, True)
        speed_font.setPixelSize(12)
        speed_fm = QFontMetrics(speed_font)

        # m/s Cinsinden Dikey Hiz
        speed_kmph_rect = speed_fm.boundingRect("000.000-m/s")
        painter.setFont(speed_font)
        speed_kmph_rect.moveCenter(center.toPoint())
        speed_kmph_rect.moveBottom(round(self.dikey_rect.bottom() - 40))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        painter.drawText(speed_kmph_rect, Qt.AlignmentFlag.AlignCenter, f'{self.dikey_hiz} m/s')
        painter.restore()

        #Gosterge Ismi
        painter.save()
        painter.drawText(round(self.dikey_rect.center().x() - 29), round(self.dikey_rect.top() + 50),  'Dikey Hiz')
        painter.translate(center.x(), center.y())
        painter.rotate(180)
        painter.translate(-center.x(), -center.y())

        # Gösterge Çubuğunun Çizilmesi
        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 0.3, cap=Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QGradient(QGradient.Preset.FebruaryInk)))
        hand_polygon = QPolygonF((center + QPoint(0, 5), center + QPoint(0, -5), center + QPoint(55, 0)))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate((180/12)*self.dikey_hiz)
        painter.translate(-center.x(), -center.y())
        painter.drawPolygon(hand_polygon)
        painter.restore()
        painter.restore()

        # İç Daireyi Oluşturma
        painter.setPen(QPen(QGradient(QGradient.Preset.CrystalRiver), 20, cap=Qt.PenCapStyle.RoundCap))
        painter.drawPoint(self.dikey_rect.center().toPoint())

    def pusula_ciz(self, painter: QPainter):
        self.pusula_rect = QRectF(self.ui.pusula_widget.geometry())
        center = self.pusula_rect.center()

        # Dış Kabuk Oluşturma
        conicalGradient = QConicalGradient(QPointF(self.pusula_rect.width()/2, self.pusula_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(10, 122, 150)))

        conicalGradient = QConicalGradient(QPointF(self.pusula_rect.width()/2, self.pusula_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        pusula_kabuk = self.pusula_rect.toRect()
        pusula_kabuk.setSize(QSizeF(self.pusula_rect.width()*0.975, self.pusula_rect.width()*0.975).toSize())
        pusula_kabuk.moveCenter(self.pusula_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(pusula_kabuk, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.pusula_rect)

        painter.save()
        gorsel = QImage("contents/neon.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.pusula_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.pusula_rect, gorsel)
        painter.restore()

        painter.save()
        three_points = QPolygonF([
            QPointF(round(self.pusula_rect.x() + self.pusula_rect.width() / 2), round(self.pusula_rect.top())),
            QPointF(round(self.pusula_rect.x() + self.pusula_rect.width() / 2) - 3, round(self.pusula_rect.top() + 10)),
            QPointF(round(self.pusula_rect.x() + self.pusula_rect.width() / 2) + 3, round(self.pusula_rect.top() + 10)),
        ])

        painter.drawPolygon(three_points)

        gorsel = QImage("contents/pusula4.png")
        painter.translate(center.x(), center.y())
        painter.rotate(self.heading)
        painter.translate(-center.x(), -center.y())
        painter.drawImage(self.pusula_rect, gorsel)
        painter.restore()        

    def gps_hizi_ciz(self, painter: QPainter):
        maks_yukseklik = 40
        dongu_sayisi = maks_yukseklik//5
        dondurme_acisi = 360/(maks_yukseklik/5)
        acimsi = 108-dondurme_acisi

        # Yazı Fontu Ayarları
        number_font = QFont("Consolas", 0, 0, True)
        number_font.setPixelSize(15)
        number_fm = QFontMetrics(number_font)
        number_rect = number_fm.boundingRect("000.000")
        painter.setFont(number_font)

        # Dış Kabuk Oluşturma
        self.gps_rect = QRectF(self.ui.groundspeed_widget.geometry())

        conicalGradient = QConicalGradient(QPointF(self.gps_rect.width()/2, self.gps_rect.width()/2), -59*16)
        conicalGradient.setColorAt(0.2, QColor(0, 210, 253))
        gps_rect = self.gps_rect.toRect()
        gps_rect.setSize(QSizeF(self.gps_rect.width()*0.975, self.gps_rect.width()*0.975).toSize())
        gps_rect.moveCenter(self.gps_rect.center().toPoint())
        painter.setPen(QPen(conicalGradient, 5))
        painter.drawArc(gps_rect, 0 * 16, 360 * 16)
        painter.setPen(QPen(conicalGradient, 5))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(self.gps_rect)

        painter.save()
        gorsel = QImage("contents/neon5.png")
        painter_path = QPainterPath()
        painter_path.addEllipse(self.gps_rect)
        painter.setClipPath(painter_path)
        painter.drawImage(self.gps_rect, gorsel)
        painter.restore()

        # Sayıların ve Çizgilerin Çizimi
        center = self.gps_rect.center()

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 5))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate((30-(360/30)))
        painter.translate(-center.x(), -center.y())
        for a in range(0, dongu_sayisi):
            painter.translate(center.x(), center.y())
            painter.rotate(360/8)
            painter.translate(-center.x(), -center.y())
            # spike
            spike_p1 = center+QPointF(0, self.gps_rect.height()//2)
            spike_p2 = center+QPointF(0, self.gps_rect.height()*0.45)
            painter.drawLine(spike_p1, spike_p2)
            # sayilar
            sayi_konum = spike_p2.toPoint()-QPoint(0, 12)
            painter.save()
            painter.translate(sayi_konum.x(), sayi_konum.y())
            painter.rotate(a*-dondurme_acisi-acimsi)
            painter.translate(-sayi_konum.x(), -sayi_konum.y())
            number_rect.moveCenter(sayi_konum)
            painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str((a)*5))
            painter.restore()
        painter.restore()
        
        painter.save()
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 4):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.gps_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.gps_rect.height() * 0.45)
            painter.drawLine(spike_p1, spike_p2)
        

        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 55)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 24):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.gps_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.gps_rect.height() * 0.45)
            if a != 4 and a != 9 and a != 14 and a != 19:
                painter.drawLine(spike_p1, spike_p2)
        
        
        painter.setPen(QPen(QGradient(QGradient.Preset.RedSalvation), 2))
        painter.translate(center.x(), center.y())
        painter.rotate(acimsi - 52.5)
        painter.translate(-center.x(), -center.y())
        for a in range(0, 9):
            painter.translate(center.x(), center.y())
            painter.rotate(dondurme_acisi/5)  # Başlangıç açısını ve döndürme açısını kullanarak dönüş yap
            painter.translate(-center.x(), -center.y())
            spike_p1 = center + QPointF(0, self.gps_rect.height() // 2)
            spike_p2 = center + QPointF(0, self.gps_rect.height() * 0.45)
            if a != 4:
                painter.drawLine(spike_p1, spike_p2)
        painter.restore()

        
        # Yuksekligin String Deger Olarak Yazilmasi
        painter.setPen(QPen(QGradient(QGradient.Preset.PerfectWhite), 25))
        speed_font = QFont("Georgia", 0, 0, True)
        speed_font.setPixelSize(12)
        speed_fm = QFontMetrics(speed_font)

        # M Cinsinden Yukseklik
        speed_kmph_rect = speed_fm.boundingRect("000.000-m/s")
        painter.setFont(speed_font)
        speed_kmph_rect.moveCenter(center.toPoint())
        speed_kmph_rect.moveBottom(round(self.gps_rect.bottom() - 40))
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(0)
        painter.translate(-center.x(), -center.y())
        painter.drawText(speed_kmph_rect, Qt.AlignmentFlag.AlignCenter, f'{self.groundspeed} m/s')

        #Gosterge Ismi
        painter.drawText(round(self.alti_rect.center().x() - 29), round(self.gps_rect.top() + 50),  'GPS Hızı')
        painter.restore()

        # Gösterge Çubuğunun Çizilmesi
        painter.setPen(QPen(QGradient(QGradient.Preset.FebruaryInk), 0.3, cap=Qt.PenCapStyle.RoundCap))
        painter.setBrush(QBrush(QGradient(QGradient.Preset.FebruaryInk)))
        hand_polygon = QPolygonF((center + QPoint(0, 5), center + QPoint(0, -5), center + QPoint(55, 0)))
        
        painter.save()
        painter.translate(center.x(), center.y())
        painter.rotate(152+(360/40)*self.groundspeed)
        painter.translate(-center.x(), -center.y())
        painter.drawPolygon(hand_polygon)
        painter.restore()

        # İç Daireyi Oluşturma
        painter.setPen(QPen(QGradient(QGradient.Preset.CrystalRiver), 20, cap=Qt.PenCapStyle.RoundCap))
        painter.drawPoint(self.gps_rect.center().toPoint())
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Daha iyi görüntü için anti-aliasing ayarı
        self.main_tasarim(painter)
        self.yatay_hiz_gostergesi_ciz(painter)
        self.ufuk_gostergesi_ciz(painter)
        self.altimetre_ciz(painter)
        self.dikey_hiz_gostergesi_ciz(painter)
        self.pusula_ciz(painter)
        self.gps_hizi_ciz(painter)
        

anasayfa = QApplication(sys.argv)
pencere = main()

sys.exit(anasayfa.exec_())