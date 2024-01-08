#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, QProcess, QIODevice

class CommandRunner(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MaloneyOS Installer")
        self.setGeometry(100, 100, 600, 400)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.scrollbar = self.output_text.verticalScrollBar()

        self.install_restart_button = QPushButton("Click to Install")
        self.install_restart_button.clicked.connect(self.run_commands)

        layout = QVBoxLayout()
        layout.addWidget(self.output_text)
        layout.addWidget(self.install_restart_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.worker_thread = WorkerThread()
        self.worker_thread.output_signal.connect(self.read_output)
        self.worker_thread.finished.connect(self.show_restart_button)

        self.commands_executed = False  # Flag to track if commands have been executed

    def run_commands(self):
        if not self.commands_executed:
            self.install_restart_button.setDisabled(True)  # Disable the button during execution
            self.worker_thread.start()
            self.commands_executed = True
        else:
            self.restart_system()

    def read_output(self, output):
        self.output_text.append(output)

        # Scroll to the bottom of the output
        self.scrollbar.setValue(self.scrollbar.maximum())

    def show_restart_button(self):
        self.install_restart_button.setText("Restart System")
        self.install_restart_button.setEnabled(True)

    def restart_system(self):
        try:
            process = QProcess()
            process.startDetached("shutdown", ["-r", "now"])
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
                process = QProcess()
                process.setProcessChannelMode(QProcess.MergedChannels)
                process.start(command)

                process.readyReadStandardOutput.connect(lambda: self.output_signal.emit(process.readAllStandardOutput().data().decode("utf-8")))
                process.waitForFinished(-1)

                if process.exitCode() != 0:
                    raise Exception(f"Error executing command '{command}': {process.readAllStandardOutput().data().decode('utf-8')}")

            except Exception as e:
                self.output_signal.emit(f"Error executing command '{command}': {str(e)}")

        # All commands have finished, show restart button
        self.output_signal.emit("All commands have finished.")
        self.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandRunner()
    window.show()
    sys.exit(app.exec_())