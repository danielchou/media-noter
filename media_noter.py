import sys
import os
import json
import warnings

# 忽略 PyQt5 的棄用警告
warnings.filterwarnings('ignore', category=DeprecationWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QListWidget, QTextEdit, 
                           QFileDialog, QMessageBox, QSlider)
from PyQt5.QtCore import Qt
from tinytag import TinyTag
from audio_player import AudioPlayer

class MediaNoter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Media Noter')
        
        # 初始化變數
        self.current_directory = ''
        self.mp3_files = []
        self.notes_dir = 'notes'
        
        # 初始化設定
        self.load_config()
        
        # 設置窗口大小
        self.setGeometry(100, 100, self.config['window_size']['width'], 
                        self.config['window_size']['height'])
        
        # 更新變數
        self.current_directory = self.config['default_directory']
        self.notes_dir = self.config['notes_directory']
        
        # 初始化音訊播放器
        self.audio_player = AudioPlayer(self.config['volume'])
        
        # 確保筆記目錄存在
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
        
        # 設置主要部件
        self.init_ui()
        
        # 如果預設目錄存在，立即掃描
        if os.path.exists(self.config['default_directory']):
            self.scan_mp3_files()
        
    def load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 默認設定
            self.config = {
                'default_directory': '',
                'notes_directory': 'notes',
                'window_size': {'width': 800, 'height': 600},
                'volume': 0.5
            }
            # 保存默認設定
            self.save_config()
    
    def save_config(self):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def init_ui(self):
        # 創建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 創建主要布局
        layout = QHBoxLayout()
        
        # 左側面板
        left_panel = QVBoxLayout()
        self.select_dir_btn = QPushButton('選擇目錄')
        self.select_dir_btn.clicked.connect(self.select_directory)
        
        # 播放控制按鈕
        playback_layout = QHBoxLayout()
        self.play_btn = QPushButton('播放')
        self.play_btn.clicked.connect(self.toggle_playback)
        self.stop_btn = QPushButton('停止')
        self.stop_btn.clicked.connect(self.stop_playback)
        
        # 音量控制
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.config['volume'] * 100))
        self.volume_slider.valueChanged.connect(self.volume_changed)
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.load_note)
        
        left_panel.addWidget(self.select_dir_btn)
        left_panel.addWidget(self.file_list)
        
        # 添加播放控制
        playback_layout.addWidget(self.play_btn)
        playback_layout.addWidget(self.stop_btn)
        left_panel.addLayout(playback_layout)
        
        # 添加音量控制
        left_panel.addWidget(self.volume_slider)
        
        # 右側面板
        right_panel = QVBoxLayout()
        self.note_edit = QTextEdit()
        self.save_btn = QPushButton('保存筆記')
        self.save_btn.clicked.connect(self.save_note)
        
        right_panel.addWidget(self.note_edit)
        right_panel.addWidget(self.save_btn)
        
        # 添加面板到主布局
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        
        central_widget.setLayout(layout)
        
    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "選擇目錄")
        if directory:
            self.current_directory = directory
            self.scan_mp3_files()
            
    def scan_mp3_files(self):
        self.file_list.clear()
        self.mp3_files = []
        
        for root, dirs, files in os.walk(self.current_directory):
            for file in files:
                if file.lower().endswith('.mp3'):
                    full_path = os.path.join(root, file)
                    self.mp3_files.append(full_path)
                    display_name = os.path.basename(full_path)
                    self.file_list.addItem(display_name)
                    
    def get_note_path(self, mp3_path):
        file_name = os.path.basename(mp3_path)
        note_name = os.path.splitext(file_name)[0] + '.txt'
        return os.path.join(self.notes_dir, note_name)
        
    def load_note(self, item):
        current_index = self.file_list.currentRow()
        if current_index >= 0:
            mp3_path = self.mp3_files[current_index]
            note_path = self.get_note_path(mp3_path)
            
            # 顯示 MP3 資訊
            try:
                tag = TinyTag.get(mp3_path)
                info = f"標題: {tag.title or '未知'}\n"
                info += f"藝術家: {tag.artist or '未知'}\n"
                info += f"專輯: {tag.album or '未知'}\n"
                info += f"年份: {tag.year or '未知'}\n"
                info += f"時長: {int(tag.duration or 0)} 秒\n"
                info += f"\n--- 在下方輸入你的筆記 ---\n\n"
            except Exception as e:
                info = "無法讀取 MP3 標籤信息\n\n--- 在下方輸入你的筆記 ---\n\n"
            
            # 讀取現有筆記
            if os.path.exists(note_path):
                with open(note_path, 'r', encoding='utf-8') as f:
                    note_content = f.read()
                    self.note_edit.setText(info + note_content)
            else:
                self.note_edit.setText(info)
                
    def save_note(self):
        current_index = self.file_list.currentRow()
        if current_index >= 0:
            mp3_path = self.mp3_files[current_index]
            note_path = self.get_note_path(mp3_path)
            
            # 保存筆記內容
            note_content = self.note_edit.toPlainText()
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note_content)
                
            QMessageBox.information(self, "成功", "筆記已保存！")
    
    def toggle_playback(self):
        current_index = self.file_list.currentRow()
        if current_index >= 0:
            mp3_path = self.mp3_files[current_index]
            status = self.audio_player.get_status()
            
            if not status['is_playing']:
                self.audio_player.play(mp3_path)
                self.play_btn.setText('暫停')
            else:
                self.audio_player.pause()
                self.play_btn.setText('播放')
    
    def stop_playback(self):
        self.audio_player.stop()
        self.play_btn.setText('播放')
    
    def volume_changed(self, value):
        volume = value / 100.0
        self.audio_player.set_volume(volume)
        self.config['volume'] = volume
        self.save_config()
    
    def closeEvent(self, event):
        # 關閉時停止播放並保存設定
        self.audio_player.cleanup()
        self.save_config()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MediaNoter()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
