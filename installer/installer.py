#!/usr/bin/env python3

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QLineEdit
import os
import subprocess

class MaloneyOS(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MaloneyOS Installer")
        self.stacked_widget = QStackedWidget(self)
        self.init_ui()

    def init_ui(self):
        # Welcome Page
        welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_label = QLabel("Welcome to MaloneyOS")
        welcome_layout.addWidget(welcome_label)
        next_button = QPushButton("Next")
        next_button.clicked.connect(self.show_disk_selection)
        welcome_layout.addWidget(next_button)
        welcome_page.setLayout(welcome_layout)
        self.stacked_widget.addWidget(welcome_page)

        # Disk Selection Page
        disk_selection_page = QWidget()
        disk_selection_layout = QVBoxLayout()
        disk_label = QLabel("Select a disk:")
        disk_selection_layout.addWidget(disk_label)
        # Use subprocess to get disks with lsblk and populate them in the window
        disks = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME"]).decode().splitlines()
        for disk in disks:
            if not any(char.isdigit() for char in disk):
                disk_button = QPushButton(disk)
                disk_button.clicked.connect(lambda _, disk=disk: self.select_disk(disk))
                disk_selection_layout.addWidget(disk_button)
        next_button = QPushButton("Next")
        next_button.clicked.connect(self.show_user_creation)
        next_button.setEnabled(False)
        self.next_button_disk = next_button
        disk_selection_layout.addWidget(next_button)
        disk_selection_page.setLayout(disk_selection_layout)
        self.stacked_widget.addWidget(disk_selection_page)

        # User Creation Page
        user_creation_page = QWidget()
        user_creation_layout = QVBoxLayout()
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.textChanged.connect(self.validate_password)
        next_button = QPushButton("Next")
        next_button.clicked.connect(self.show_installation)
        next_button.setEnabled(False)
        self.next_button_user = next_button
        user_creation_layout.addWidget(username_label)
        user_creation_layout.addWidget(self.username_input)
        user_creation_layout.addWidget(password_label)
        user_creation_layout.addWidget(self.password_input)
        user_creation_layout.addWidget(confirm_password_label)
        user_creation_layout.addWidget(self.confirm_password_input)
        user_creation_layout.addWidget(next_button)
        user_creation_page.setLayout(user_creation_layout)
        self.stacked_widget.addWidget(user_creation_page)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.stacked_widget)

    def show_disk_selection(self):
        self.stacked_widget.setCurrentIndex(1)

    def select_disk(self, disk):
        self.DISK = disk
        self.next_button_disk.setEnabled(True)

    def show_user_creation(self):
        self.stacked_widget.setCurrentIndex(2)

    def validate_password(self):
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        if password == confirm_password and password != "":
            self.next_button_user.setEnabled(True)
        else:
            self.next_button_user.setEnabled(False)

    def output_disk_value(self):
        disk_value = "/dev/" + self.DISK
        with open('/tmp/selected-disk', 'w') as file:
            file.write(disk_value)

    def output_credentials(self):
        username_value = self.USERNAME
        password_value = self.PASSWORD
        with open('/tmp/username', 'w') as username_file:
            username_file.write(username_value)
        with open('/tmp/password', 'w') as password_file:
            password_file.write(password_value)

    def show_installation(self):
        self.USERNAME = self.username_input.text()
        self.PASSWORD = self.password_input.text()
        self.stacked_widget.setCurrentIndex(3)
        self.output_disk_value()
        self.output_credentials()
        #subprocess.Popen(["python3", "scriptrunner.py"])
        sys.exit()  # Add this line to exit the application

if __name__ == "__main__":
    app = QApplication(sys.argv)
    maloney_os = MaloneyOS()
    maloney_os.show()
    sys.exit(app.exec_())