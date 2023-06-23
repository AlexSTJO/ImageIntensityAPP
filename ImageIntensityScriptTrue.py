import os
import shutil
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QGridLayout, QPushButton, QWidget, QFrame
from PyQt5.QtCore import Qt


class ImageDropZone(QFrame):
    def __init__(self, parent, folder_name):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 300)
        self.setStyleSheet("QFrame { background-color: #EAEAEA; border: 2px dashed #AAAAAA; }")

        self.file_list_widget = QListWidget(self)
        self.file_list_widget.setMaximumWidth(200)
        self.file_list_widget.setDragDropMode(QListWidget.NoDragDrop)

        self.folder_name = folder_name
        self.file_counter = 1  # Counter for appending to file names
        self.session_folder = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for file in files:
            if os.path.isfile(file):
                session_folder = self.session_folder
                if session_folder is None:
                    session_folder = self.create_session_folder()
                    self.session_folder = session_folder
                self.process_image(file, session_folder)

    def create_session_folder(self):
        base_folder = "ImageAnalyzerASTJO"
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        session_folder = os.path.join(base_folder, timestamp)
        os.makedirs(session_folder, exist_ok=True)
        return session_folder

    def process_image(self, image_path, session_folder):
        file_name = os.path.basename(image_path)
        file_name, file_extension = os.path.splitext(file_name)
        file_name = f"{file_name}_{self.file_counter}{file_extension}"
        self.file_counter += 1
        destination_folder = os.path.join(session_folder, self.folder_name)
        os.makedirs(destination_folder, exist_ok=True)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.move(image_path, destination_path)
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

        self.session_folder = None

        self.nadh_drop_zone = ImageDropZone(main_widget, "NADH")
        self.fadh_drop_zone = ImageDropZone(main_widget, "FADH")

        self.layout.addWidget(self.nadh_drop_zone, 0, 0)
        self.layout.addWidget(QLabel("NADH Files:"), 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.nadh_drop_zone.file_list_widget, 2, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.fadh_drop_zone, 0, 1)
        self.layout.addWidget(QLabel("FADH Files:"), 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.fadh_drop_zone.file_list_widget, 2, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        submit_button = QPushButton("Submit Files", main_widget)
        submit_button.clicked.connect(self.submit_files)
        self.layout.addWidget(submit_button, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

    def submit_files(self):
        nadh_files = [self.nadh_drop_zone.file_list_widget.item(i).text() for i in
                      range(self.nadh_drop_zone.file_list_widget.count())]
        fadh_files = [self.fadh_drop_zone.file_list_widget.item(i).text() for i in
                      range(self.fadh_drop_zone.file_list_widget.count())]

        # Example: Display the submitted file names in the console
        print("NADH Files:")
        for file in nadh_files:
            print(file)
        print("FADH Files:")
        for file in fadh_files:
            print(file)

        # Close the current window and create a new window
        self.hide()
        self.new_window = NewWindow(nadh_files, fadh_files)
        self.new_window.show()


class NewWindow(QWidget):
    def __init__(self, nadh_files, fadh_files):
        super().__init__()
        self.setWindowTitle("New Window")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout(self)

        nadh_label = QLabel("NADH Files:")
        nadh_list_widget = QListWidget()
        nadh_list_widget.addItems(nadh_files)

        fadh_label = QLabel("FADH Files:")
        fadh_list_widget = QListWidget()
        fadh_list_widget.addItems(fadh_files)

        layout.addWidget(nadh_label)
        layout.addWidget(nadh_list_widget)
        layout.addWidget(fadh_label)
        layout.addWidget(fadh_list_widget)

        self.setLayout(layout)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = ImageDropApplication()
    window.show()
    sys.exit(app.exec_())