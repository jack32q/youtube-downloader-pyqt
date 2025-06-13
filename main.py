import sys
import os
import re
from urllib.parse import urlparse, parse_qs
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import yt_dlp


def nettoyer_lien_youtube(lien):
    """Nettoie le lien YouTube pour garder uniquement l’ID de la vidéo."""
    if "youtu.be/" in lien:
        video_id = lien.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com" in lien and "v=" in lien:
        parsed_url = urlparse(lien)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get("v", [None])[0]
    else:
        return None

    if video_id and re.match(r"^[a-zA-Z0-9_-]{11}$", video_id):
        return f"https://www.youtube.com/watch?v={video_id}"
    return None


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, output_dir):
        super().__init__()
        self.url = url
        self.output_dir = output_dir

    def run(self):
        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4'
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished_signal.emit("Téléchargement terminé !")
        except Exception as e:
            self.error_signal.emit(str(e))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if d.get('total_bytes') and d.get('downloaded_bytes'):
                percent = int(d['downloaded_bytes'] * 100 / d['total_bytes'])
                self.progress_signal.emit(percent)
        elif d['status'] == 'finished':
            self.progress_signal.emit(100)


class YoutubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vodo By R.Jackson")
        self.setFixedSize(500, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # URL input
        h_url = QHBoxLayout()
        self.url_label = QLabel("URL YouTube :")
        self.url_input = QLineEdit()
        h_url.addWidget(self.url_label)
        h_url.addWidget(self.url_input)
        layout.addLayout(h_url)

        # Folder selection
        h_folder = QHBoxLayout()
        self.folder_label = QLabel("Dossier de destination :")
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        self.browse_button = QPushButton("Parcourir")
        self.browse_button.clicked.connect(self.browse_folder)
        h_folder.addWidget(self.folder_label)
        h_folder.addWidget(self.folder_path)
        h_folder.addWidget(self.browse_button)
        layout.addLayout(h_folder)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Download button
        self.download_button = QPushButton("Télécharger")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir un dossier")
        if folder:
            self.folder_path.setText(folder)

    def start_download(self):
        url_brut = self.url_input.text().strip()
        url = nettoyer_lien_youtube(url_brut)
        folder = self.folder_path.text().strip()

        if not url:
            QMessageBox.warning(self, "Erreur", "Lien YouTube invalide ou non reconnu.")
            return

        if not folder or not os.path.isdir(folder):
            QMessageBox.warning(self, "Erreur", "Merci de choisir un dossier de destination valide.")
            return

        self.download_button.setEnabled(False)
        self.progress_bar.setValue(0)

        self.thread = DownloadThread(url, folder)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.finished_signal.connect(self.download_finished)
        self.thread.error_signal.connect(self.download_error)
        self.thread.start()

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)

    def download_finished(self, message):
        QMessageBox.information(self, "Succès", message)
        self.download_button.setEnabled(True)

    def download_error(self, error_msg):
        QMessageBox.critical(self, "Erreur", f"Erreur lors du téléchargement :\n{error_msg}")
        self.download_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YoutubeDownloader()
    window.show()
    sys.exit(app.exec_())
