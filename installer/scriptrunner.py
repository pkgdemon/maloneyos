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

        self.restart_button = QPushButton("Restart System")
        self.restart_button.clicked.connect(self.restart_system)

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.restart_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Run commands when the application opens
        self.run_commands()

    def run_commands(self):
        commands = [
            "python zfs.py",
            "echo 'Hello, World!'",
            "pwd"
        ]

        for command in commands:
            process = QProcess()
            process.start(command)
            process.waitForFinished(-1)
            exit_code = process.exitCode()
            if exit_code != 0:
                error_output = process.readAllStandardError().data().decode()
                self.output_text.append(f"Command failed: {command}")
                self.output_text.append(f"Error output: {error_output}")
                break
            else:
                output = process.readAllStandardOutput().data().decode()
                self.output_text.append(output)

            # Scroll to the bottom of the output
            self.scrollbar.setValue(self.scrollbar.maximum())

    def restart_system(self):
        process = QProcess()
        process.start("shutdown -r now")
        process.waitForFinished(-1)
        exit_code = process.exitCode()
        if exit_code != 0:
            error_output = process.readAllStandardError().data().decode()
            self.output_text.append("Restart command failed")
            self.output_text.append(f"Error output: {error_output}")
        else:
            self.output_text.append("System restarted successfully")

        # Scroll to the bottom of the output
        self.scrollbar.setValue(self.scrollbar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandRunner()
    window.show()
    sys.exit(app.exec_())
