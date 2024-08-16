import sys
from PyQt5.QtWidgets import QWidget, QApplication
from Harita_python import Ui_harita
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import http.server
import socketserver
import threading

class LocalServer:
    def __init__(self, host='127.0.0.1', port=8080) -> None:
        self.host = host
        self.port = port
        self.server = socketserver.TCPServer((self.host, self.port), http.server.SimpleHTTPRequestHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        
    def start(self):
        print(f"Local server started at http://{self.host}:{self.port}")
        self.server_thread.start()

    def stop(self):
        print("Stopping local server...")
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        print("Local server stopped.")

class HaritaKod(QWidget):
    def __init__(self):
        super().__init__()
        self.harita = Ui_harita()
        self.harita.setupUi(self)
        self.harita_rect = QRectF(self.harita.harita_frame.geometry())

        layout = QVBoxLayout(self.harita.harita_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        self.harita_webview = QWebEngineView(self)
        layout.addWidget(self.harita_webview)

        self.harita_webview.setGeometry(self.harita.harita_frame.rect())

        self.local_server = LocalServer()
        self.local_server_thread = None
        self.start_local_server()
        url = f"http://{self.local_server.host}:{self.local_server.port}/cesium_clouds/index.html"
        self.load_cesium_map(url)

    def start_local_server(self):
        if not self.local_server_thread:
            self.local_server_thread = QThread()
            self.local_server_thread.started.connect(self.local_server.start)
            self.local_server_thread.start()

    def load_cesium_map(self, url):
        print(url)
        url1 = QUrl(url)
        self.harita_webview.load(url1)
        
    def ikinci_ekranda_goster(self):
        screens = QApplication.screens()
        if len(screens) > 1:
            screen = screens[1]
            self.move(screen.geometry().topLeft())
            self.showFullScreen()
        elif len(screens) == 1:
            self.showFullScreen()

    def closeEvent(self, event):
        self.local_server.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HaritaKod()
    #window.ikinci_ekranda_goster()
    window.show()
    sys.exit(app.exec_())