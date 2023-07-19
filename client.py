import os
import shutil
import datetime
import numpy as np
from PIL import Image
from PyQt6.QtWidgets import QApplication, QCheckBox, QMainWindow, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QGridLayout, QPushButton, QWidget, QFrame, QLineEdit, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSlot, QSizeF
from PyQt6.QtGui import QPixmap, QImage, QImageReader
from PIL.ImageQt import ImageQt
from script import CreateRedox
import matplotlib.pyplot as plt
import matplotlib.cm as cm



class ImageDropZone(QFrame):
    def __init__(self, parent, folder_name, session_folder):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 300)
        self.setStyleSheet("QFrame { background-color: #EAEAEA; border: 2px dashed #AAAAAA; }")

        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setMaximumWidth(200)
        self.file_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)

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
        self.layout.addWidget(QLabel("NADH Files:"), 1, 0, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.nadh_drop_zone.file_list_widget, 2, 0, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.layout.addWidget(self.fad_drop_zone, 0, 1)
        self.layout.addWidget(QLabel("FAD Files:"), 1, 1, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.fad_drop_zone.file_list_widget, 2, 1, alignment=Qt.AlignmentFlag.AlignHCenter)

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
                                     self.fad_drop_zone.session_folder, self.session_folder)
        print("pp" + self.session_folder)
        self.new_window.show()


class NewWindow(QWidget):
    def __init__(self, nadh_files, fad_files, nadh_session_folder, fad_session_folder, session_folder):
        super().__init__()
        self.setWindowTitle("New Window")
        self.setGeometry(100, 100, 400, 300)

        self.nadh_session_folder = nadh_session_folder
        self.fad_session_folder = fad_session_folder
        self.session_folder = session_folder
        print(os.getcwd())
        #self.results_session_folder = 

        layout = QGridLayout(self)

        self.nadh_label = QLabel("NADH Files:")
        self.nadh_list_widget = QListWidget()
        self.nadh_list_widget.addItems(nadh_files)
        self.nadh_list_widget.itemClicked.connect(self.on_nadh_item_clicked)

        self.fad_label = QLabel("FAD Files:")
        self.fad_list_widget = QListWidget()
        self.fad_list_widget.addItems(fad_files)
        self.fad_list_widget.itemClicked.connect(self.on_fad_item_clicked)

        self.results_label = QLabel("Results")
        self.results_list_widget = QListWidget()
        self.results_list_widget.itemClicked.connect(self.on_results_item_clicked)


        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.image_label.setMinimumSize(300, 200)

        self.nadh_gain_label = QLabel("NADH Gain:")
        self.nadh_gain_textbox = QLineEdit(self)
        self.nadh_power_label = QLabel("NADH Power:")
        self.nadh_power_textbox = QLineEdit(self)
        self.fad_gain_label = QLabel("FAD Gain:")
        self.fad_gain_textbox = QLineEdit(self)
        self.fad_power_label = QLabel("FAD Power:")
        self.fad_power_textbox = QLineEdit(self)

        self.button1 = QPushButton("NADH/FAD")
        self.button2 = QPushButton("NADH/(FAD+NADH)")
        self.button3 = QPushButton("FAD/NADH")
        self.button4 = QPushButton("FAD/(NADH+FAD)")

        self.apply_pretty_redox_checkbox = QCheckBox("Apply PrettyRedox", self)
        self.apply_pretty_redox_checkbox.setChecked(False)

        self.button1.clicked.connect(self.on_button1_clicked)
        self.button2.clicked.connect(self.on_button2_clicked)
        self.button3.clicked.connect(self.on_button3_clicked)
        self.button4.clicked.connect(self.on_button4_clicked)



        layout.addWidget(self.nadh_label, 0, 0)
        layout.addWidget(self.nadh_list_widget, 1, 0)
        layout.addWidget(self.fad_label, 0, 1)
        layout.addWidget(self.fad_list_widget, 1, 1)
        layout.addWidget(self.image_label, 2, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.results_label, 0, 2)
        layout.addWidget(self.results_list_widget, 1, 2)

        layout.addWidget(self.nadh_gain_label, 3, 0)
        layout.addWidget(self.nadh_gain_textbox, 3, 1)
        layout.addWidget(self.nadh_power_label, 4, 0)
        layout.addWidget(self.nadh_power_textbox, 4, 1)
        layout.addWidget(self.fad_gain_label, 5, 0)
        layout.addWidget(self.fad_gain_textbox, 5, 1)
        layout.addWidget(self.fad_power_label, 6, 0)
        layout.addWidget(self.fad_power_textbox, 6, 1)

        layout.addWidget(self.button1, 3, 2)
        layout.addWidget(self.button2, 4, 2)
        layout.addWidget(self.button3, 5, 2)
        layout.addWidget(self.button4, 6, 2)
        layout.addWidget(self.apply_pretty_redox_checkbox, 7, 0, 1, 2)

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

    @pyqtSlot(QListWidgetItem)
    def on_results_item_clicked(self, item):
        selected_file = item.text()
        image_path = os.path.join(self.session_folder,"results",selected_file)
        self.display_image(image_path)
    
    @pyqtSlot()
    def on_button1_clicked(self):
        # Existing code...
        self.call_create_redox('NADH_div_FAD')

    @pyqtSlot()
    def on_button2_clicked(self):
        # Existing code...
        self.call_create_redox('NADH_div_FAD_NADH')

    @pyqtSlot()
    def on_button3_clicked(self):
        # Existing code...
        self.call_create_redox('FAD_div_NADH')

    @pyqtSlot()
    def on_button4_clicked(self):
        # Existing code...
        self.call_create_redox('FAD_div_NADH_FAD')



    @pyqtSlot()
    def call_create_redox(self, choice):
        # Get the state of the checkbox
        apply_pretty_redox = self.apply_pretty_redox_checkbox.isChecked()

        # Get the gain and power values from the textboxes
        nadh_gain = float(self.nadh_gain_textbox.text())
        nadh_power = float(self.nadh_power_textbox.text())
        fad_gain = float(self.fad_gain_textbox.text())
        fad_power = float(self.fad_power_textbox.text())

        # Call the CreateRedox function
        results_path = CreateRedox(nadh_gain, nadh_power, fad_gain, fad_power, choice, apply_pretty_redox)

        self.populate_results_list(results_path)



    def populate_results_list(self, results_path):
        tiff_files = [file for file in os.listdir(results_path) if file.endswith(".tif")]
        self.results_list_widget.clear()
        self.results_list_widget.addItems(tiff_files)
        os.chdir('../..')



    def display_image(self, image_path):
        image = Image.open(image_path)

        # Create QImage from image data
        qimage = QImage(image_path)

        # Create QPixmap from QImage
        pixmap = QPixmap.fromImage(qimage)

        # Scale the pixmap while maintaining the aspect ratio
        scaled_pixmap = pixmap.scaledToWidth(self.image_label.width())

        # Adjust the label height to match the aspect ratio of the image
        adjusted_height = int(scaled_pixmap.height() * (self.image_label.width() / scaled_pixmap.width()))
        self.image_label.setFixedHeight(adjusted_height)

        self.image_label.setPixmap(scaled_pixmap)
            
    



if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = ImageDropApplication()
    window.show()
    sys.exit(app.exec())