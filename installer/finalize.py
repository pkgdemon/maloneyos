import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QProcess

class InstallationCompleteWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Installation Complete")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()

        message_label = QLabel("Installation is complete!")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)

        restart_button = QPushButton("Restart System")
        restart_button.clicked.connect(self.restart_system)
        layout.addWidget(restart_button)

        self.setLayout(layout)

    def restart_system(self):
        # Restart the system using a command-line process
        process = QProcess()
        process.startDetached("shutdown -r -t 0")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallationCompleteWindow()
    window.show()
    sys.exit(app.exec_())
