import sys
import os
import json
import warnings

# 忽略 PyQt5 的棄用警告
warnings.filterwarnings('ignore', category=DeprecationWarning)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QListWidget, QTextEdit, 
                           QFileDialog, QMessageBox, QSlider, QLabel,
                           QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor
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
        
        # 初始化定時器用於更新進度條
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(100)  # 每 100ms 更新一次
        
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
        
        # 播放進度條
        progress_layout = QHBoxLayout()
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)  # 使用更精細的值
        self.progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self.progress_slider.sliderReleased.connect(self.on_progress_released)
        
        # 時間顯示
        self.time_label = QLabel('00:00 / 00:00')
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.time_label)
        
        # 時間標記按鈕
        self.mark_time_btn = QPushButton('標記時間點')
        self.mark_time_btn.clicked.connect(self.mark_current_time)
        
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
        
        # 添加進度條和時間顯示
        left_panel.addLayout(progress_layout)
        left_panel.addWidget(self.mark_time_btn)
        
        # 添加音量控制
        left_panel.addWidget(self.volume_slider)
        
        # 右側面板
        right_panel = QVBoxLayout()
        self.note_edit = QTextBrowser()
        self.note_edit.setOpenLinks(True)  # 允許打開鏈接
        self.note_edit.setOpenExternalLinks(False)  # 不打開外部鏈接
        self.note_edit.anchorClicked.connect(self.on_time_link_clicked)
        self.note_edit.mousePressEvent = self.note_edit_mouse_press
        self.note_edit.setReadOnly(False)
        
        # 設定樣式表
        self.note_edit.document().setDefaultStyleSheet(
            "a { color: blue; text-decoration: underline; cursor: pointer; }\n"
            "a:hover { color: red; }")
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
                info = f"時長: {int(tag.duration or 0)} 秒\n\n"
            except Exception as e:
                info = "無法讀取 MP3 時長\n\n"
            
            # 讀取現有筆記
            content = info
            if os.path.exists(note_path):
                with open(note_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('[') and ']' in line:
                            # 處理時間標記
                            time_str = line[1:line.index(']')]
                            try:
                                minutes, seconds = map(int, time_str.split(':'))
                                total_seconds = minutes * 60 + seconds
                                content += f'<a href="time:{total_seconds}" style="color: blue; text-decoration: underline; cursor: pointer;">[{time_str}]</a>'
                                content += line[line.index(']')+1:]
                            except:
                                content += line
                        else:
                            content += line
            
            self.note_edit.setHtml(content)
                
    def save_note(self):
        current_index = self.file_list.currentRow()
        if current_index >= 0:
            mp3_path = self.mp3_files[current_index]
            note_path = self.get_note_path(mp3_path)
            
            # 取得純文字內容
            html = self.note_edit.toHtml()
            
            # 將 HTML 轉換為純文字
            text = ""
            for line in html.split('\n'):
                if '<a href="time:' in line:
                    # 尋找時間標記
                    start = line.find('[') + 1
                    end = line.find(']', start)
                    if start > 0 and end > start:
                        time_str = line[start:end]
                        text += f"[{time_str}]"
                        # 尋找標記後的文字
                        text_start = line.find('</a>') + 4
                        if text_start > 4:
                            text += line[text_start:].strip()
                        text += '\n'
                elif not line.startswith('<!DOCTYPE') and \
                     not line.startswith('<html') and \
                     not line.startswith('<head') and \
                     not line.startswith('<style') and \
                     not line.startswith('<body') and \
                     not line.startswith('</') and \
                     line.strip() != '':
                    # 移除 HTML 標籤
                    text += line.replace('<p style=', '').replace('</p>', '')\
                               .replace('"', '').replace('>', '').strip() + '\n'
            
            # 保存純文字內容
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(text.strip())
                
            QMessageBox.information(self, "成功", "筆記已保存！")
    
    def toggle_playback(self):
        current_index = self.file_list.currentRow()
        if current_index >= 0:
            mp3_path = self.mp3_files[current_index]
            status = self.audio_player.get_status()
            
            if not status['is_playing']:
                if status['current_file'] != mp3_path:
                    self.audio_player.play(mp3_path)
                else:
                    self.audio_player.resume()
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
    
    def format_time(self, seconds):
        """將秒數轉換為 mm:ss 格式"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def update_progress(self):
        """更新進度條和時間顯示"""
        if not hasattr(self, 'is_seeking'):
            self.is_seeking = False
        
        if not self.is_seeking:
            status = self.audio_player.get_status()
            if status['total_length'] > 0:
                # 更新進度條
                progress = (status['position'] / status['total_length']) * 1000
                self.progress_slider.setValue(int(progress))
                
                # 更新時間顯示
                current = self.format_time(status['position'])
                total = self.format_time(status['total_length'])
                self.time_label.setText(f"{current} / {total}")
    
    def on_progress_pressed(self):
        """當用戶開始拖動進度條"""
        self.is_seeking = True
    
    def on_progress_released(self):
        """當用戶放開進度條"""
        status = self.audio_player.get_status()
        if status['total_length'] > 0:
            position = (self.progress_slider.value() / 1000.0) * status['total_length']
            self.audio_player.seek(position)
        self.is_seeking = False
    
    def mark_current_time(self):
        """在筆記中標記當前時間點"""
        status = self.audio_player.get_status()
        current_time = self.format_time(status['position'])
        seconds = status['position']
        
        # 在筆記中插入時間標記
        cursor = self.note_edit.textCursor()
        html_link = f'<a href="time:{seconds}">[{current_time}]</a> '
        cursor.insertHtml(html_link)
    
    def note_edit_mouse_press(self, event):
        """處理筆記編輯器的滑鼠點擊事件"""
        # 獲取點擊位置的鏈接
        anchor = self.note_edit.anchorAt(event.pos())
        if anchor.startswith('time:'):
            try:
                seconds = float(anchor.replace('time:', ''))
                print(f"測試: 點擊時間標記 {seconds} 秒")
                
                current_index = self.file_list.currentRow()
                if current_index >= 0:
                    # 確保文件已經載入
                    mp3_path = self.mp3_files[current_index]
                    if self.audio_player.current_playing != mp3_path:
                        self.audio_player.play(mp3_path)
                    
                    # 跳轉到指定時間
                    if self.audio_player.seek(seconds):
                        print(f"成功跳轉到 {seconds} 秒")
                    else:
                        print("跳轉失敗")
            except Exception as e:
                print(f"跳轉錯誤: {str(e)}")
        
        # 調用原始的點擊事件
        QTextBrowser.mousePressEvent(self.note_edit, event)
    
    def on_time_link_clicked(self, url):
        """當點擊時間標記時跳轉到相應位置"""
        pass  # 改用 note_edit_mouse_press 處理點擊事件
    
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
