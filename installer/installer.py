#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal

import subprocess
import shlex

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

        self.restart_button = QPushButton("Restart System")
        self.restart_button.clicked.connect(self.restart_system)
        self.restart_button.setEnabled(False)  # Disable restart button initially

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.run_button)
        layout.addWidget(self.restart_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.worker_thread = WorkerThread()
        self.worker_thread.output_signal.connect(self.read_output)
        self.worker_thread.finished.connect(self.enable_restart_button)

    def run_commands(self):
        self.run_button.setDisabled(True)  # Disable the "Click to Install" button during execution
        self.worker_thread.start()

    def read_output(self, output):
        self.output_text.append(output)

        # Scroll to the bottom of the output
        self.scrollbar.setValue(self.scrollbar.maximum())

    def enable_restart_button(self):
        self.run_button.setDisabled(False)  # Enable the "Click to Install" button
        self.restart_button.setEnabled(True)  # Enable the "Restart System" button

    def restart_system(self):
        try:
            subprocess.run(["shutdown", "-r", "now"])
        except Exception as e:
            self.output_text.append(f"Error restarting system: {str(e)}")

class WorkerThread(QThread):
    output_signal = pyqtSignal(str)

    def run(self):
        commands = [
            "python zfs.py",
            "unsquashfs -f -d /tmp/maloneyos /dev/loop0",
            "pwd"
        ]

        for command in commands:
            try:
                process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

                while True:
                    output_line = process.stdout.readline()
                    if output_line == '' and process.poll() is not None:
                        break
                    self.output_signal.emit(output_line.rstrip())

                process.stdout.close()
                process.wait()
            except Exception as e:
                self.output_signal.emit(f"Error executing command '{command}': {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandRunner()
    window.show()
    sys.exit(app.exec_())
