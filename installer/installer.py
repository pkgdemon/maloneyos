#!/usr/bin/env python3
'''
Installer for MaloneyOS that collects info and processes with backend.
'''

import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QLineEdit, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, QProcess

class MaloneyOSInstaller(QWidget):
    '''
    Define the QStackedWidget class so we can navigate through several screens collecting info and then install.
    '''
    def __init__(self):
        self.disk = None
        self.commands_executed = False
        self.username = ""
        self.password = ""
        super().__init__()
        self.setWindowTitle("MaloneyOS Installer")
        self.stacked_widget = QStackedWidget(self)
        self.init_ui()

    def init_ui(self):
        '''
        Define our pages that we will use in the installer, welcome, disk, user, install, etc.
        '''
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

        try:
            # Run lsblk command to get the list of disks
            disks = subprocess.check_output(["lsblk", "-d", "-n", "-o", "NAME"]).decode().splitlines()
            for disk in disks:
                # Check if the disk name contains any digits, if not, add it to the list
                if not any(char.isdigit() for char in disk):
                    disk_button = QPushButton(disk)
                    disk_button.clicked.connect(lambda _, disk=disk: self.select_disk(disk))
                    disk_selection_layout.addWidget(disk_button)

        except Exception as e:
            # Handle the exception (display an error message, log the error, etc.)
            print(f"Error getting disk information: {str(e)}")

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

        # Installation Page (integrated from scriptrunner.py)
        installation_page = QWidget()
        installation_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        installation_layout.addWidget(self.output_text)

        self.install_restart_button = QPushButton("Click to Install")
        self.install_restart_button.clicked.connect(self.run_commands)
        installation_layout.addWidget(self.install_restart_button)

        self.restart_system_button = QPushButton("Restart System")
        self.restart_system_button.clicked.connect(self.restart_system)
        self.restart_system_button.hide()  # Hide it initially
        installation_layout.addWidget(self.restart_system_button)

        installation_page.setLayout(installation_layout)
        self.stacked_widget.addWidget(installation_page)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.stacked_widget)

        self.worker_thread = WorkerThread()
        self.worker_thread.output_signal.connect(self.read_output)
        self.worker_thread.finished.connect(self.show_restart_button)

        self.commands_executed = False  # Flag to track if commands have been executed

    def show_disk_selection(self):
        '''
        Function to show disk selection.
        '''
        self.stacked_widget.setCurrentIndex(1)

    def select_disk(self, disk):
        '''
        If we have no disk selected prevent next from being pressed.
        '''
        self.disk = disk
        self.next_button_disk.setEnabled(True)

    def show_user_creation(self):
        '''
        Display the user creation window
        '''
        self.stacked_widget.setCurrentIndex(2)

    def validate_password(self):
        '''
        Confirm the password matches and prevent next from being pressed if it does not.
        '''
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        if password == confirm_password and password != "":
            self.next_button_user.setEnabled(True)
        else:
            self.next_button_user.setEnabled(False)

    def output_disk_value(self):
        '''
        Construct disk output as /dev/$DEVICE to be used by backend.
        '''
        disk_value = "/dev/" + self.disk
        with open('/tmp/selected-disk', 'w', encoding='utf-8') as file:
            file.write(disk_value)

    def output_credentials(self):
        '''
        Save credentials to be read by the backend to create users, add user to group, sudoers, etc.
        '''
        username_value = self.username
        password_value = self.password
        with open('/tmp/username', 'w', encoding='utf-8') as username_file:
            username_file.write(username_value)
        with open('/tmp/password', 'w', encoding='utf-8') as password_file:
            password_file.write(password_value)

    def show_installation(self):
        '''
        Output information collected during the wizard for the backend.
        '''
        self.username = self.username_input.text()
        self.password = self.password_input.text()
        self.stacked_widget.setCurrentIndex(3)
        self.output_disk_value()
        self.output_credentials()

    def run_commands(self):
        '''
        Hide the restart button until commands finish running.
        '''
        if not self.commands_executed:
            self.install_restart_button.setDisabled(True)
            self.worker_thread.start()
            self.commands_executed = True

    def read_output(self, output):
        '''
        Allow the output to be read.
        '''
        self.output_text.append(output)

    def show_restart_button(self):
        '''
        Change button to restart system when commands finish.
        '''
        self.install_restart_button.setEnabled(True)
        self.install_restart_button.hide()
        self.restart_system_button.show()
        self.output_text.append("All commands have finished.")
        self.stacked_widget.setCurrentIndex(3)

    def restart_system(self):
        '''
        Allow restarting the system and raise and exception if we cannot.
        '''
        try:
            process = QProcess()
            process.startDetached("shutdown", ["-r", "now"])
        except Exception as e:
            self.output_text.append(f"Error restarting system: {str(e)}")

class WorkerThread(QThread):
    '''
    Create a worker thread so we can display output real time.
    '''
    output_signal = pyqtSignal(str)

    def run(self):
        '''
        Run the backend with the informatoin we collected with the wizard to install the system.
        '''
        commands = [
            "python3 backend.py"
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
        self.finished.emit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    maloney_os_installer = MaloneyOSInstaller()
    maloney_os_installer.show()
    sys.exit(app.exec_())

# End-of-file (EOF)
