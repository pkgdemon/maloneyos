import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QLineEdit
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

        # Installation Page
        installation_page = QWidget()
        installation_layout = QVBoxLayout()

        # Run zfs.py and squashfs.py scripts here and show terminal output
        def run_zfs_script():
            try:
                output = subprocess.check_output(["python", "zfs.py"])
                print(output.decode())
            except subprocess.CalledProcessError as e:
                print(f"Error running zfs.py: {e}")

        run_zfs_script()
        next_button = QPushButton("Next")
        next_button.clicked.connect(self.show_installation_finished)
        next_button.setEnabled(False)
        self.next_button_installation = next_button
        installation_layout.addWidget(next_button)
        installation_page.setLayout(installation_layout)
        self.stacked_widget.addWidget(installation_page)

        # Installation Finished Page
        installation_finished_page = QWidget()
        installation_finished_layout = QVBoxLayout()
        finished_label = QLabel("Installation finished!")
        installation_finished_layout.addWidget(finished_label)
        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(self.restart)
        installation_finished_layout.addWidget(restart_button)
        installation_finished_page.setLayout(installation_finished_layout)
        self.stacked_widget.addWidget(installation_finished_page)

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

    def show_installation(self):
        self.USERNAME = self.username_input.text()
        self.PASSWORD = self.password_input.text()
        self.stacked_widget.setCurrentIndex(3)

    def show_installation_finished(self):
        self.stacked_widget.setCurrentIndex(4)

    def restart(self):
        subprocess.run(["shutdown", "-r", "now"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    maloney_os = MaloneyOS()
    maloney_os.show()
    sys.exit(app.exec_())
