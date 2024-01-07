#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QProcess

class CommandRunner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MaloneyOS Installer")
        self.setGeometry(100, 100, 600, 400)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.scrollbar = self.output_text.verticalScrollBar()

        self.run_button = QPushButton("Click to Install")
        self.run_button.clicked.connect(self.run_commands)

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.run_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def run_commands(self):
        commands = [
            "python zfs.py",
            "unsquashfs -f -d /tmp/maloneyos /dev/loop0",
            "pwd"
        ]

        for command in commands:
            process = QProcess()
            process.start(command)
            process.waitForFinished(-1)
            output = process.readAllStandardOutput().data().decode()
            self.output_text.append(output)

            # Scroll to the bottom of the output
            self.scrollbar.setValue(self.scrollbar.maximum())

        self.run_button.setText("Restart System")
        self.run_button.clicked.disconnect(self.run_commands)
        self.run_button.clicked.connect(self.restart_system)

    def restart_system(self):
        process = QProcess()
        process.start("shutdown -r now")
        process.waitForFinished(-1)  # Wait for the shutdown process to finish

        # Exit the application
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandRunner()
    window.show()
    sys.exit(app.exec_())