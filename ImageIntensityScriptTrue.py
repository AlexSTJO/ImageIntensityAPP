import os
import shutil
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QGridLayout, QPushButton, QWidget, QFrame, QLineEdit
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from script import CreateRedox




class ImageDropZone(QFrame):
    def __init__(self, parent, folder_name, session_folder):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 300)
        self.setStyleSheet("QFrame { background-color: #EAEAEA; border: 2px dashed #AAAAAA; }")

        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setMaximumWidth(200)
        self.file_list_widget.setDragDropMode(QListWidget.NoDragDrop)

        self.folder_name = folder_name
        self.file_counter = 1  # Counter for appending to file names
        self.session_folder = session_folder

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            if os.path.isfile(file):
                self.process_image(file)

    def process_image(self, image_path):
        file_name = os.path.basename(image_path)
        file_name, file_extension = os.path.splitext(file_name)
        file_name = f"{file_name}_{self.file_counter}{file_extension}"
        self.file_counter += 1
        destination_folder = os.path.join(self.session_folder, self.folder_name)
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy(image_path, destination_path)
        self.file_list_widget.addItem(file_name)


class ImageDropApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Drop Application")
        self.setGeometry(100, 100, 800, 400)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        self.layout = QGridLayout(main_widget)
        main_widget.setLayout(self.layout)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)

        self.session_folder = self.create_session_folder()

        self.nadh_drop_zone = ImageDropZone(main_widget, "NADH", self.session_folder)
        self.fad_drop_zone = ImageDropZone(main_widget, "FAD", self.session_folder)

        self.layout.addWidget(self.nadh_drop_zone, 0, 0)
        self.layout.addWidget(QLabel("NADH Files:"), 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.nadh_drop_zone.file_list_widget, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.fad_drop_zone, 0, 1)
        self.layout.addWidget(QLabel("FAD Files:"), 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.fad_drop_zone.file_list_widget, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        submit_button = QPushButton("Submit Files", main_widget)
        submit_button.clicked.connect(self.submit_files)
        self.layout.addWidget(submit_button, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

    def create_session_folder(self):
        base_folder = "ImageAnalyzerASTJO"
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        session_folder = os.path.join(base_folder, timestamp)
        os.makedirs(session_folder, exist_ok=True)
        return session_folder

    def submit_files(self):
        nadh_files = [self.nadh_drop_zone.file_list_widget.item(i).text() for i in
                      range(self.nadh_drop_zone.file_list_widget.count())]
        fad_files = [self.fad_drop_zone.file_list_widget.item(i).text() for i in
                     range(self.fad_drop_zone.file_list_widget.count())]

        # Example: Display the submitted file names in the console
        print("NADH Files:")
        for file in nadh_files:
            print(file)
        print("FAD Files:")
        for file in fad_files:
            print(file)

        # Close the current window and create a new window
        self.hide()
        self.new_window = NewWindow(nadh_files, fad_files, self.nadh_drop_zone.session_folder,
                                     self.fad_drop_zone.session_folder)
        self.new_window.show()


class NewWindow(QWidget):
    def __init__(self, nadh_files, fad_files, nadh_session_folder, fad_session_folder):
        super().__init__()
        self.setWindowTitle("New Window")
        self.setGeometry(100, 100, 400, 300)

        self.nadh_session_folder = nadh_session_folder
        self.fad_session_folder = fad_session_folder

        layout = QGridLayout(self)

        self.nadh_label = QLabel("NADH Files:")
        self.nadh_list_widget = QListWidget()
        self.nadh_list_widget.addItems(nadh_files)
        self.nadh_list_widget.itemClicked.connect(self.on_nadh_item_clicked)

        self.fad_label = QLabel("FAD Files:")
        self.fad_list_widget = QListWidget()
        self.fad_list_widget.addItems(fad_files)
        self.fad_list_widget.itemClicked.connect(self.on_fad_item_clicked)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(300, 200)

        self.nadh_gain_label = QLabel("NADH Gain:")
        self.nadh_gain_textbox = QLineEdit(self)
        self.nadh_power_label = QLabel("NADH Power:")
        self.nadh_power_textbox = QLineEdit(self)
        self.fad_gain_label = QLabel("FAD Gain:")
        self.fad_gain_textbox = QLineEdit(self)
        self.fad_power_label = QLabel("FAD Power:")
        self.fad_power_textbox = QLineEdit(self)

        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.submit)

        layout.addWidget(self.nadh_label)
        layout.addWidget(self.nadh_list_widget)
        layout.addWidget(self.fad_label)
        layout.addWidget(self.fad_list_widget)
        layout.addWidget(self.image_label)

        layout.addWidget(self.nadh_gain_label)
        layout.addWidget(self.nadh_gain_textbox)
        layout.addWidget(self.nadh_power_label)
        layout.addWidget(self.nadh_power_textbox)
        layout.addWidget(self.fad_gain_label)
        layout.addWidget(self.fad_gain_textbox)
        layout.addWidget(self.fad_power_label)
        layout.addWidget(self.fad_power_textbox)

        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    @pyqtSlot(QListWidgetItem)
    def on_nadh_item_clicked(self, item):
        selected_file = item.text()
        image_path = os.path.join(self.nadh_session_folder, "NADH", selected_file)
        self.display_image(image_path)

    @pyqtSlot(QListWidgetItem)
    def on_fad_item_clicked(self, item):
        selected_file = item.text()
        image_path = os.path.join(self.fad_session_folder, "FAD", selected_file)
        self.display_image(image_path)

    def display_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def submit(self):
        nadh_gain = float(self.nadh_gain_textbox.text())
        nadh_power = float(self.nadh_power_textbox.text())
        fad_gain = float(self.fad_gain_textbox.text())
        fad_power = float(self.fad_power_textbox.text())
        CreateRedox(nadh_gain, nadh_power, fad_gain, fad_power)




if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = ImageDropApplication()
    window.show()
    sys.exit(app.exec_())