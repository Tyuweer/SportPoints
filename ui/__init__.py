from pathlib import Path
import tempfile
def __init__(self):
    super().__init__()
    self.setWindowTitle("Система прогноза очков спортсмена")
    self.resize(1200, 800)

    # Создаём временную папку для JSON-файлов
    self.temp_dir = Path(tempfile.mkdtemp(prefix="sport_predictor_"))
    
    # Добавь эту строку:
    print(f"📁 Временная папка: {self.temp_dir}")

    # Для отслеживания изменений
    self.file_timestamps = {}
    ...