import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QFileDialog
from PySide6.QtCore import QTimer, QThread, Signal, Qt, QMutex, QWaitCondition
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from PySide6.QtGui import QPixmap, QImage
import queue
import cv2


class FrameReader(QThread):
    error = Signal(str)

    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.frame_queue = queue.Queue(maxsize=30)
        self.seek_queue = queue.Queue()
        self.is_running = True
        self.paused = False
        self.frame_idx = 0
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def seek_to(self, frame_idx: int):
        # Flush stale frames
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        self.seek_queue.put(frame_idx)

    def _do_seek(self, frame_idx: int):
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        if frame_idx < self.frame_idx:
            # OpenCV can't seek backwards reliably — reopen
            self.cap.release()
            self.cap = cv2.VideoCapture(self.video_path)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self.frame_idx = frame_idx

    def run(self):
        while self.is_running:
            # Handle seek requests
            try:
                idx = self.seek_queue.get_nowait()
                self._do_seek(idx)
            except queue.Empty:
                pass

            if self.paused:
                print("pausing")
                self.mutex.lock()
                self.wait_condition.wait(self.mutex)
                self.mutex.unlock()
                continue

            if self.frame_queue.full():
                self.msleep(5)
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.msleep(20)
                continue

            self.frame_queue.put((self.frame_idx, frame))
            self.frame_idx += 1

    def stop(self):
        self.is_running = False
        self.wait_condition.wakeAll()  # wake thread so it can exit
        self.cap.release()
    
    def pause(self):
        self.paused = True
    
    def unpause(self):
        self.paused = False
        self.wait_condition.wakeAll()


def process_frame(frame: np.ndarray) -> np.ndarray:
    """---- YOUR PROCESSING GOES HERE ----"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 50, 150)


def to_pixmap(frame: np.ndarray, target_w: int, target_h: int) -> QPixmap:
    frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
    if len(frame.shape) == 2:
        h, w = frame.shape
        qt_img = QImage(frame.data.tobytes(), w, h, w, QImage.Format_Grayscale8)
    else:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data.tobytes(), w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qt_img)


class PlayerController:
    def __init__(self, window):
        self.window = window
        self.reader: FrameReader | None = None
        self.current_frame = 0
        self.playing = False
        self.last_frame: np.ndarray | None = None  # for freeze-on-pause

        self.window.setMaximumSize(1280, 720)
        self.window.resize(1280, 720)

        # Connect signals
        self.window.btnLoad.clicked.connect(self.load_video)
        self.window.btnPlay.clicked.connect(self.toggle_play)
        self.window.btnNext.clicked.connect(self.next_frame)
        self.window.btnPrev.clicked.connect(self.prev_frame)
        self.window.frameSlider.sliderMoved.connect(self.on_slider_moved)

        self.timer = QTimer()
        self.timer.timeout.connect(self.show_frame)

    # ---------------------------------------------------------------- load --

    def load_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window, "Open Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov)"
        )
        if not path:
            return

        if self.reader:
            self.reader.stop()
            self.reader.wait()
            self.timer.stop()

        self.reader = FrameReader(path)
        if not self.reader.cap.isOpened():
            self.window.statusBar().showMessage("Failed to open video")
            return

        self.window.frameSlider.setMaximum(max(0, self.reader.total_frames - 1))
        self.window.frameSlider.setValue(0)
        self.current_frame = 0
        self.last_frame = None

        self.reader.start()
        self.speed = 1.0  # lower = faster, higher = slower
        interval = max(1, int((1000 / self.reader.fps) * self.speed))
        self.timer.start(interval)

        self.window.statusBar().showMessage(
            f"Loaded: {self.reader.total_frames} frames @ {self.reader.fps:.1f} FPS"
        )

    # --------------------------------------------------------------- render --

    def show_frame(self):
        if self.reader is None:
            return

        # ONE frame per tick only
        try:
            idx, frame = self.reader.frame_queue.get_nowait()
            self.current_frame = idx
            self.last_frame = frame
        except queue.Empty:
            frame = self.last_frame  # freeze on last known frame

        if frame is None:
            return

        w1 = self.window.frameLabel.width()
        h1 = self.window.frameLabel.height()
        self.window.frameLabel.setPixmap(to_pixmap(frame, w1, h1))

        processed = process_frame(frame)
        w2 = self.window.processedLabel.width()
        h2 = self.window.processedLabel.height()
        self.window.processedLabel.setPixmap(to_pixmap(processed, w2, h2))

        self.window.frameSlider.blockSignals(True)
        self.window.frameSlider.setValue(self.current_frame)
        self.window.frameSlider.blockSignals(False)

    # ------------------------------------------------------------- controls --

    def toggle_play(self):
        self.playing = not self.playing
        if self.reader:
            if self.reader.paused:
                self.reader.unpause()
                self.timer.start()
            else:
                self.reader.pause()
                self.timer.stop()
        self.window.btnPlay.setText("⏸" if self.playing else "▶")

    def next_frame(self):
        if self.reader:
            self.reader.pause()
            self.playing = False
            self.window.btnPlay.setText("▶")
            self.reader.seek_to(self.current_frame + 1)

    def prev_frame(self):
        if self.reader:
            self.reader.pause()
            self.playing = False
            self.window.btnPlay.setText("▶")
            self.reader.seek_to(self.current_frame - 1)

    def on_slider_moved(self, val):
        if self.reader:
            self.reader.paused = True
            self.playing = False
            self.window.btnPlay.setText("▶")
            self.reader.seek_to(val)

    # --------------------------------------------------------------- cleanup --

    def cleanup(self):
        self.timer.stop()
        if self.reader:
            self.reader.stop()
            self.reader.wait()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui_file = QFile("Snap.ui")
    ui_file.open(QFile.ReadOnly)
    window = QUiLoader().load(ui_file)
    ui_file.close()

    controller = PlayerController(window)
    app.aboutToQuit.connect(controller.cleanup)
    window.show()
    sys.exit(app.exec())