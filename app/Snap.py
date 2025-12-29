import sys
import Snap
import cv2
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QMenu
)


# Subclass QMainWindow to customize your application's main window
class PlayerController:
    def __init__(self, window):
        self.window = window
        self.frames = []
        self.playing = False
        self.timer = QTimer(window)

        window.btnLoad.clicked.connect(self.load_video)
        window.btnPlay.clicked.connect(self.toggle_play)
        window.btnNext.clicked.connect(self.next_frame)
        window.btnPrev.clicked.connect(self.prev_frame)
        window.frameSlider.valueChanged.connect(self.on_slider)

        self.timer.timeout.connect(self.advance)

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window, "Open Video", "", "Video Files (*.mp4 *.avi)"
        )
        if not path:
            return

        self.frames.clear()
        cap = cv2.VideoCapture(path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self.frames.append(frame)

        cap.release()

        self.window.frameSlider.setMaximum(len(self.frames) - 1)
        self.show_frame(0)

    def show_frame(self, idx):
        if not self.frames:
            return
        frame = self.frames[idx]
        h, w, ch = frame.shape

        image = QImage(
            frame.data, w, h, ch * w, QImage.Format_BGR888
        )
        pix = QPixmap.fromImage(image)
        self.window.frameLabel.setPixmap(pix)
        self.window.lblFrameInfo.setText(f"{idx}/{len(self.frames)-1}")


    # ---------------- CONTROLS ----------------

    def on_slider(self, val):
        if self.frames:
            self.show_frame(val)

    def next_frame(self):
        v = self.window.frameSlider.value()
        self.window.frameSlider.setValue(min(v + 1, len(self.frames) - 1))

    def prev_frame(self):
        v = self.window.frameSlider.value()
        self.window.frameSlider.setValue(max(v - 1, 0))

    def toggle_play(self):
        if not self.frames:
            return
        self.playing = not self.playing
        if self.playing:
            self.timer.start(33)
            self.window.btnPlay.setText("⏸")
        else:
            self.timer.stop()
            self.window.btnPlay.setText("▶")

    def advance(self):
        v = self.window.frameSlider.value()
        if v < len(self.frames) - 1:
            self.window.frameSlider.setValue(v + 1)
        else:
            self.toggle_play()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    ui_file = QFile("Snap.ui")
    ui_file.open(QFile.ReadOnly)
    window = QUiLoader().load(ui_file)
    ui_file.close()

    controller = PlayerController(window)

    window.show()
    sys.exit(app.exec())
