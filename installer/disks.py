#!/usr/bin/python3

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton

class DiskSelectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Selection")
        self.layout = QVBoxLayout()
        self.label = QLabel("Select a disk:")
        self.disk_list = QListWidget()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_disk)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.disk_list)
        self.layout.addWidget(self.select_button)
        self.setLayout(self.layout)

    def select_disk(self):
        selected_disk = self.disk_list.currentItem().text()
        # Export the selected disk as a variable or perform any other action
        with open('/tmp/selected-disk', 'w') as f:
            f.write(selected_disk)
        print(f"Selected disk: {selected_disk}")
        self.close()

def list_disks():
    disks = []
    output = subprocess.check_output(["lsblk", "-o", "NAME", "-n", "-l"]).decode().splitlines()
    disks = ["/dev/" + line.strip() for line in output if line.strip() and not any(char.isdigit() for char in line.strip())]
    return disks

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiskSelectionWindow()
    disks = list_disks()
    window.disk_list.addItems(disks)
    window.show()
    sys.exit(app.exec_())
