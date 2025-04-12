import pygame
import time
from mutagen.mp3 import MP3

class AudioPlayer:
    def __init__(self, initial_volume=0.5):
        # 初始化 pygame 音訊
        pygame.mixer.init()
        self.current_playing = None
        self.is_playing = False
        self.current_position = 0
        self.total_length = 0
        self.last_update_time = 0
        self.set_volume(initial_volume)
    
    def load_file(self, file_path):
        """載入音檔並取得總長度"""
        try:
            audio = MP3(file_path)
            self.total_length = audio.info.length
            pygame.mixer.music.load(file_path)
            self.current_playing = file_path
            self.current_position = 0
            return True
        except Exception as e:
            print(f"載入音檔錯誤: {str(e)}")
            return False
    
    def play(self, file_path=None, start_pos=None):
        """播放指定的音檔"""
        try:
            # 如果是新文件，先載入
            if file_path and file_path != self.current_playing:
                if not self.load_file(file_path):
                    return False
            # 如果沒有指定文件，但有當前文件
            elif not file_path and self.current_playing:
                pygame.mixer.music.load(self.current_playing)
            
            # 從指定位置或當前位置開始播放
            start_position = start_pos if start_pos is not None else self.current_position
            pygame.mixer.music.play(start=start_position)
            
            self.is_playing = True
            self.current_position = start_position
            self.last_update_time = time.time()
            return True
        except Exception as e:
            print(f"播放錯誤: {str(e)}")
            return False
    
    def pause(self):
        """暫停播放"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            # 暫停時更新位置
            self._update_position()
    
    def resume(self):
        """恢復播放"""
        if not self.is_playing and self.current_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
            self.last_update_time = time.time()
    
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_position = 0
    
    def set_volume(self, volume):
        """設置音量 (0.0 到 1.0)"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    
    def _update_position(self):
        """更新當前播放位置"""
        if self.is_playing:
            current_time = time.time()
            elapsed = current_time - self.last_update_time
            self.current_position += elapsed
            self.last_update_time = current_time
    
    def seek(self, position):
        """跳轉到指定位置"""
        try:
            # 確保位置在有效範圍內
            position = max(0, min(float(position), self.total_length))
            
            # 重新載入當前文件
            if self.current_playing:
                pygame.mixer.music.load(self.current_playing)
                
                # 從新位置開始播放
                pygame.mixer.music.play(start=position)
                
                # 如果原本是暫停狀態，則維持暫停
                if not self.is_playing:
                    pygame.mixer.music.pause()
                
                self.current_position = position
                self.last_update_time = time.time()
                return True
            return False
        except Exception as e:
            print(f"跳轉錯誤: {str(e)}")
            return False
    
    def get_status(self):
        """獲取當前播放狀態"""
        self._update_position()
        return {
            'is_playing': self.is_playing,
            'current_file': self.current_playing,
            'position': min(self.current_position, self.total_length),
            'total_length': self.total_length
        }
    
    def cleanup(self):
        """清理資源"""
        self.stop()
        pygame.mixer.quit()
