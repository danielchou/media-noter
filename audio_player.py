import pygame

class AudioPlayer:
    def __init__(self, initial_volume=0.5):
        # 初始化 pygame 音訊
        pygame.mixer.init()
        self.current_playing = None
        self.is_playing = False
        self.set_volume(initial_volume)
    
    def play(self, file_path):
        """播放指定的音檔"""
        try:
            # 如果選擇了新的歌曲
            if self.current_playing != file_path:
                pygame.mixer.music.load(file_path)
                self.current_playing = file_path
            pygame.mixer.music.play()
            self.is_playing = True
            return True
        except Exception as e:
            print(f"播放錯誤: {str(e)}")
            return False
    
    def pause(self):
        """暫停播放"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
    
    def resume(self):
        """恢復播放"""
        if not self.is_playing and self.current_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
    
    def stop(self):
        """停止播放"""
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def set_volume(self, volume):
        """設置音量 (0.0 到 1.0)"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    
    def get_status(self):
        """獲取當前播放狀態"""
        return {
            'is_playing': self.is_playing,
            'current_file': self.current_playing
        }
    
    def cleanup(self):
        """清理資源"""
        self.stop()
        pygame.mixer.quit()
