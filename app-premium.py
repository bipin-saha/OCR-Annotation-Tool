import sys
import csv
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLabel, QLineEdit, QHBoxLayout, QSpacerItem, QSizePolicy, QGridLayout, QCompleter
from PyQt5.QtGui import QPixmap, QStandardItemModel
from PyQt5.QtCore import Qt, QTimer, QStringListModel
from text_extraction import auto_annotate_ocr  # Make sure this function is properly defined in your module

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR Annotation Tool")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Top Row: Open Image Folder button
        self.open_image_folder_button = QPushButton("Open Image Folder")
        self.open_image_folder_button.clicked.connect(self.open_image_folder)
        self.layout.addWidget(self.open_image_folder_button)

        # Middle Row: Image display, label, update and delete buttons
        self.middle_layout = QHBoxLayout()
        self.image_label = QLabel()
        self.image_label.setFixedSize(800, 450)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.middle_layout.addWidget(self.image_label)

        self.right_side_layout = QVBoxLayout()

        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Label")
        self.label_edit.returnPressed.connect(self.update_label)  # Connect the returnPressed signal to the update_label method
        self.label_edit.textChanged.connect(self.update_completer_suggestions)  # Connect the textChanged signal to update_completer_suggestions
        self.right_side_layout.addWidget(self.label_edit)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.update_label)
        self.right_side_layout.addWidget(self.update_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_image)
        self.right_side_layout.addWidget(self.delete_button)

        # Bottom Row: Next, Previous, and Last Annotate buttons (moved to right side layout)
        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self.previous_image)
        self.right_side_layout.addWidget(self.previous_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_image)
        self.right_side_layout.addWidget(self.next_button)

        self.last_annotate_button = QPushButton("Last Annotate")
        self.last_annotate_button.clicked.connect(self.last_annotate_image)
        self.right_side_layout.addWidget(self.last_annotate_button)

        self.middle_layout.addLayout(self.right_side_layout)
        self.layout.addLayout(self.middle_layout)

        # Spacer between label box and message
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Success Label for temporary message
        self.success_label = QLabel()
        self.success_label.setAlignment(Qt.AlignCenter)
        self.success_label.setStyleSheet("font-size: 14px; qproperty-wordWrap: true;")
        self.layout.addWidget(self.success_label)

        # Suggestion Layout for showing previous 7 image labels
        self.suggestion_layout = QGridLayout()
        self.suggestion_layout.setAlignment(Qt.AlignTop)
        self.layout.addLayout(self.suggestion_layout)

        # Auto Annotation Button
        self.auto_annotation_button = QPushButton("Auto Annotation")
        self.auto_annotation_button.clicked.connect(self.auto_annotation_clicked)
        self.layout.addWidget(self.auto_annotation_button)

        self.image_folder = ""
        self.csv_file = ""
        self.csv_data = {}
        self.current_image_index = 0

        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#update_button {
                background-color: green;
            }
            QPushButton#update_button:hover {
                background-color: #45a049;
            }
            QPushButton#delete_button {
                background-color: red;
            }
            QPushButton#delete_button:hover {
                background-color: #d32f2f;
            }
            QPushButton#previous_button, QPushButton#next_button {
                background-color: lightblue;
            }
            QPushButton#previous_button:hover, QPushButton#next_button:hover {
                background-color: #87cefa;
            }
            QLineEdit {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 5px;
            }
            QLabel {
                border: none;
                padding: 5px;
            }
        """)

        # Set object names for buttons to apply specific styles
        self.update_button.setObjectName("update_button")
        self.delete_button.setObjectName("delete_button")
        self.previous_button.setObjectName("previous_button")
        self.next_button.setObjectName("next_button")

        # Initialize the completer for label suggestions
        self.completer = QCompleter()
        self.label_edit.setCompleter(self.completer)

    def open_image_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Image Folder")
        if folder_path:
            self.image_folder = folder_path
            self.csv_file = os.path.join(self.image_folder, "annotations.csv")
            if not os.path.exists(self.csv_file):
                self.generate_csv()
            self.read_csv()
            self.show_image()

    def generate_csv(self):
        image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        with open(self.csv_file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["filename", "label"])
            for image_file in image_files:
                csv_writer.writerow([image_file, ""])

    def read_csv(self):
        self.csv_data = {}
        with open(self.csv_file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                filename, label = row
                self.csv_data[filename] = label
        self.update_completer()  # Update the completer after reading the CSV
        self.show_image()

    def update_completer(self):
        labels = list(set(self.csv_data.values()))  # Get unique labels
        model = QStringListModel(labels)
        self.completer.setModel(model)

    def update_completer_suggestions(self, text):
        filtered_labels = [label for label in self.csv_data.values() if text.lower() in label.lower()]
        model = QStringListModel(filtered_labels)
        self.completer.setModel(model)

    def show_image(self):
        if not self.image_folder:
            self.show_temporary_message("Image folder not selected.")
            return

        filenames = list(self.csv_data.keys())
        if not filenames:
            self.show_temporary_message("No filenames found in the CSV file.")
            return

        filename = filenames[self.current_image_index]
        label = self.csv_data.get(filename, "")

        image_path = os.path.join(self.image_folder, filename)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setScaledContents(False)
            self.label_edit.setText(label)
            self.update_suggestion_layout()
        else:
            self.show_temporary_message(f"Image file not found: {image_path}")

    def update_suggestion_layout(self):
        # Clear previous suggestions
        for i in reversed(range(self.suggestion_layout.count())):
            self.suggestion_layout.itemAt(i).widget().setParent(None)

        filenames = list(self.csv_data.keys())
        current_index = self.current_image_index
        previous_labels = [self.csv_data[filename] for filename in filenames[max(0, current_index - 7):current_index]]
        for i, label in enumerate(previous_labels):
            label_widget = QLabel(label)
            self.suggestion_layout.addWidget(label_widget, i, 0)

    def next_image(self):
        if self.current_image_index < len(self.csv_data) - 1:
            self.current_image_index += 1
        self.show_image()

    def previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
        self.show_image()

    def update_label(self):
        if not self.csv_file or not self.image_folder:
            self.show_temporary_message("CSV file or image folder not selected.")
            return

        filenames = list(self.csv_data.keys())
        if not filenames:
            self.show_temporary_message("No filenames found in the CSV file.")
            return

        filename = filenames[self.current_image_index]
        new_label = self.label_edit.text()
        self.csv_data[filename] = new_label
        self.update_csv()

        # Show the message
        self.show_temporary_message("Label updated successfully!")

    def show_temporary_message(self, message, duration=3000):
        self.success_label.setText(message)
        self.success_label.adjustSize()
        self.success_label.show()
        QTimer.singleShot(duration, self.success_label.hide)

    def update_csv(self):
        with open(self.csv_file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["filename", "label"])
            for filename, label in self.csv_data.items():
                csv_writer.writerow([filename, label])
        self.show_image()

    def delete_image(self):
        if not self.image_folder or not self.csv_file:
            self.show_temporary_message("Image folder or CSV file not selected.")
            return

        filenames = list(self.csv_data.keys())
        if not filenames:
            self.show_temporary_message("No filenames found in the CSV file.")
            return

        filename = filenames[self.current_image_index]
        image_path = os.path.join(self.image_folder, filename)
        if os.path.exists(image_path):
            os.remove(image_path)
        del self.csv_data[filename]
        self.update_csv()

    def auto_annotation_clicked(self):
        self.auto_annotate()

    def auto_annotate(self):
        auto_annotate_ocr(self.csv_file, self.image_folder, self.csv_file)
        self.read_csv()
        self.show_image()
        self.show_temporary_message("Auto Annotation completed!")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left or event.key() == Qt.Key_A:
            self.previous_image()
        elif event.key() == Qt.Key_Right or event.key() == Qt.Key_D:
            self.next_image()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.update_label()
        elif event.key() == Qt.Key_Tab:
            if self.completer.popup().isVisible():
                self.completer.popup().hide()
                self.label_edit.setText(self.completer.currentCompletion())
                self.update_label()

    def last_annotate_image(self):
        filenames = list(self.csv_data.keys())
        # Find the last annotated image index
        for i in range(len(filenames) - 1, -1, -1):
            if self.csv_data[filenames[i]]:  # Check if the label is not empty
                self.current_image_index = i
                break
        self.show_image()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

