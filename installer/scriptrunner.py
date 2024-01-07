#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QProcess

class CommandRunner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Command Runner")
        self.setGeometry(100, 100, 600, 400)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.scrollbar = self.output_text.verticalScrollBar()

        self.run_button = QPushButton("Run Commands")
        self.run_button.clicked.connect(self.run_commands)

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.run_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def run_commands(self):
        commands = [
            "ls -l",
            "echo 'Hello, World!'",
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandRunner()
    window.show()
    sys.exit(app.exec_())
