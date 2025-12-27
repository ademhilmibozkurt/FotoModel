import sys
from database import SupabaseDB
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QFileDialog

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.supabase = SupabaseDB()

        self.setWindowTitle("Foto Model")

        layout = QVBoxLayout()
        self.log = QTextEdit()

        uploadButton = QPushButton("Şablon Yükle")
        uploadButton.clicked.connect(self.upload_photos)

        # make these prettier
        updateButton  = QPushButton("Güncelle")
        updateButton.clicked.connect(self.fetch_selection)

        layout.addWidget(uploadButton)
        layout.addWidget(updateButton)
        layout.addWidget(self.log)
        self.setLayout(layout)

    def upload_photos(self):
        filePath, _ = QFileDialog.getOpenFileName(self, 'Open', r'C:\ProgramFiles\FotoModel\templates', '*.jpg, *.png, *.avif, *.svg, *.webp')
        with open(filePath, 'r', encoding='mbcs') as file_pointer:
            self.lines = file_pointer.readlines()

    def fetch_selection(self):
        formResponses = self.supabase.fetch_data()
        self.log.setText(str(formResponses))

app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())