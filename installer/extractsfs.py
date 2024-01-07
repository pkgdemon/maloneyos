#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPlainTextEdit, QSizePolicy
from PyQt5.QtCore import QProcess, pyqtSlot

class ShellCommandApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Shell Command Output')

        # Layout
        layout = QVBoxLayout()

        # Output display
        self.output_display = QPlainTextEdit(self)
        self.output_display.setReadOnly(True)
        self.output_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.output_display)

        self.setLayout(layout)

        self.show()

        # Run the command automatically
        self.runCommand()

    @pyqtSlot()
    def runCommand(self):
        # Clear previous output
        self.output_display.clear()

        # Set the command to extract"
        command = ["sudo", "unsquashfs", "-f", "-d", "/tmp/maloneyos", "/dev/loop0"]

        # Create a QProcess instance
        self.process = QProcess()

        # Connect signals to update the UI
        self.process.readyReadStandardOutput.connect(self.updateOutput)
        self.process.finished.connect(self.commandFinished)

        # Start the process
        self.process.start(command[0], command[1:])

    @pyqtSlot()
    def updateOutput(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.output_display.insertPlainText(output)
        self.output_display.verticalScrollBar().setValue(self.output_display.verticalScrollBar().maximum())

    @pyqtSlot()
    def commandFinished(self):
        self.output_display.insertPlainText("\nCommand finished.")
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ShellCommandApp()
    sys.exit(app.exec_())
