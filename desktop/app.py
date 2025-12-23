import sys
from database import supabase
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Foto Model")

        layout = QVBoxLayout()
        self.log = QTextEdit()

        # make these prettier
        btn = QPushButton("Güncelle")
        btn.clicked.connect(self.fetch_data)

        layout.addWidget(btn)
        layout.addWidget(self.log)
        self.setLayout(layout)

    # add a list of customers
    # select one customer
    # show selected photo templates
    # add is_made button and allow for deletion
    def fetch_data(self):
        responses = (
            supabase
            .table("responses")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        self.log.setText(str(responses))

app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec())