import requests
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton
import sys

API_URL = "https://YOUR_DOMAIN"

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio Panel")

        layout = QVBoxLayout()
        self.log = QTextEdit()

        btn = QPushButton("Yeni Yanıtları Getir")
        btn.clicked.connect(self.fetch_data)

        layout.addWidget(btn)
        layout.addWidget(self.log)
        self.setLayout(layout)

    def fetch_data(self):
        r = requests.get(f"{API_URL}/responses")
        self.log.setText(str(r.json()))

app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())