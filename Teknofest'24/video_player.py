import sys
import vlc
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtCore import QTimer

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # VLC player oluşturuluyor
        self.instance = vlc.Instance()
        self.mediaPlayer = self.instance.media_player_new()

        # Buton oluşturuluyor ve olay sinyali bağlanıyor
        self.playButton = QPushButton('Play Video')
        self.playButton.clicked.connect(self.playVideo)

        # Layout oluşturuluyor ve bileşenler ekleniyor
        layout = QVBoxLayout()
        layout.addWidget(self.playButton)

        self.videoFrame = QFrame()
        layout.addWidget(self.videoFrame)

        self.setLayout(layout)

        # Pencere başlığı ayarlanıyor
        self.setWindowTitle('VLC Video Player')
        self.resize(800, 600)

        # Video frame'ini VLC player'a bağlamak için timer oluşturuluyor
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updateFrame)

    def playVideo(self):
        # Video dosyasının yolu
        video_path = 'video.mp4'

        # Media oluşturuluyor ve oynatıcıya atanıyor
        self.media = self.instance.media_new(video_path)
        self.mediaPlayer.set_media(self.media)

        # Video frame'i VLC player'a bağlanıyor
        self.mediaPlayer.set_hwnd(int(self.videoFrame.winId()))

        # Video oynatılıyor
        self.mediaPlayer.play()
        self.timer.start()

    def updateFrame(self):
        # Frame güncelleniyor
        if self.mediaPlayer.is_playing():
            self.mediaPlayer.video_set_mouse_input(False)
            self.mediaPlayer.video_set_key_input(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
