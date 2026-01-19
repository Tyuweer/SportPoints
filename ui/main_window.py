import sys
import os
import tempfile
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QGroupBox,
    QMessageBox, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pathlib import Path
import json

from parsers.parser_factory import get_parser_by_type

class PredictorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sport Predictor")
        self.resize(1000, 700)

        # Создаём папку ./temp/ рядом с программой
        self.temp_dir = Path("./temp")
        self.temp_dir.mkdir(exist_ok=True)

        self.target_file = None
        self.target_type = "russian"  # Теперь всегда российский
        self.auto_files = []  # [(path, "russian")]
        self.manual_files = []  # [(path, "krasnoyarsk")]

        self.init_ui()

    def closeEvent(self, event):
        # Удаляем папку ./temp/ при закрытии
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        event.accept()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # === Целевой протокол ===
        target_group = QGroupBox("Целевой протокол")
        target_layout = QHBoxLayout()
        self.target_btn = QPushButton("Выбрать PDF")
        self.target_btn.clicked.connect(self.select_target)
        self.target_label = QLabel("Не выбран")
        target_layout.addWidget(self.target_btn)
        target_layout.addWidget(self.target_label)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # === История результатов ===
        history_group = QGroupBox("История результатов")
        history_layout = QVBoxLayout()

        # Авто (российские)
        auto_layout = QHBoxLayout()
        self.auto_add_btn = QPushButton("Добавить")
        self.auto_add_btn.clicked.connect(lambda: self.add_files(self.auto_files, "russian"))
        self.auto_remove_btn = QPushButton("Удалить")
        self.auto_remove_btn.clicked.connect(lambda: self.remove_selected(self.auto_list, self.auto_files))
        self.auto_list = QListWidget()
        self.auto_list.setFixedHeight(100)
        self.auto_list.setFixedWidth(350)  # ← Фиксируем ширину
        auto_layout.addWidget(QLabel("Российские:"))
        auto_layout.addWidget(self.auto_add_btn)
        auto_layout.addWidget(self.auto_remove_btn)
        auto_layout.addWidget(self.auto_list)
        history_layout.addLayout(auto_layout)

        # Ручная (краевые)
        manual_layout = QHBoxLayout()
        self.manual_add_btn = QPushButton("Добавить")
        self.manual_add_btn.clicked.connect(lambda: self.add_files(self.manual_files, "krasnoyarsk"))
        self.manual_remove_btn = QPushButton("Удалить")
        self.manual_remove_btn.clicked.connect(lambda: self.remove_selected(self.manual_list, self.manual_files))
        self.manual_list = QListWidget()
        self.manual_list.setFixedHeight(100)
        self.manual_list.setFixedWidth(350)  # ← Фиксируем ширину
        manual_layout.addWidget(QLabel("Краевые:"))
        manual_layout.addWidget(self.manual_add_btn)
        manual_layout.addWidget(self.manual_remove_btn)
        manual_layout.addWidget(self.manual_list)
        history_layout.addLayout(manual_layout)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # === Кнопка загрузки протоколов ===
        self.parse_btn = QPushButton("Загрузить протоколы")
        self.parse_btn.clicked.connect(self.parse_all)
        layout.addWidget(self.parse_btn)

        # === Поле ввода имени и кнопка расчёта ===
        calc_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Фамилия Имя спортсмена")
        self.calc_btn = QPushButton("Рассчитать очки")
        self.calc_btn.clicked.connect(self.predict_scores)
        calc_layout.addWidget(QLabel("Спортсмен:"))
        calc_layout.addWidget(self.name_input)
        calc_layout.addWidget(self.calc_btn)
        layout.addLayout(calc_layout)

        # === Результаты ===
        result_group = QGroupBox("Результаты по дистанциям")
        result_layout = QVBoxLayout()
        self.results_list = QListWidget()
        self.total_label = QLabel("Итог: 0 очков (3 лучшие дистанции)")
        result_layout.addWidget(self.results_list)
        result_layout.addWidget(self.total_label)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # === Лог ===
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

        central.setLayout(layout)
        self.setCentralWidget(central)

        # === Минималистичный дизайн ===
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #e0e0e0;  /* Нейтральный серый */
                color: #333;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                font-size: 12px;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)

    def select_target(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите целевой PDF", "", "PDF Files (*.pdf)")
        if path:
            self.target_file = Path(path)
            self.target_label.setText(self.target_file.name)

    def add_files(self, file_list, ptype):
        paths, _ = QFileDialog.getOpenFileNames(self, f"Выберите PDF ({ptype})", "", "PDF Files (*.pdf)")
        for p in paths:
            path = Path(p)
            if (path, ptype) not in file_list:
                file_list.append((path, ptype))
                if ptype == "russian":
                    self.auto_list.addItem(f"{path.name}")
                else:
                    self.manual_list.addItem(f"{path.name}")

    def remove_selected(self, list_widget, file_list):
        selected = list_widget.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите файл для удаления.")
            return
        name = selected.text()
        path_to_remove = next((p for p, t in file_list if p.name == name), None)
        if path_to_remove:
            file_list[:] = [(p, t) for p, t in file_list if p != path_to_remove]
            list_widget.takeItem(list_widget.row(selected))

    def log(self, msg):
        self.log_area.append(msg)

    def parse_all(self):
        # Очищаем папку перед парсингом
        for f in self.temp_dir.glob("*.json"):
            f.unlink()

        # Парсим целевой
        if not self.target_file:
            QMessageBox.warning(self, "Ошибка", "Целевой протокол не выбран!")
            return

        try:
            parser, is_manual = get_parser_by_type(self.target_type)
            data = parser.parse(self.target_file, is_manual=is_manual)
            json_filename = self.temp_dir / self.target_file.with_suffix('.json').name
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"✅ Целевой: {self.target_file.name} ({self.target_type}) → {json_filename.name}")
        except Exception as e:
            self.log(f"❌ Ошибка парсинга целевого: {e}")
            return

        # Парсим историю
        all_history_files = self.auto_files + self.manual_files
        for path, ptype in all_history_files:
            try:
                parser, is_manual = get_parser_by_type(ptype)
                data = parser.parse(path, is_manual=is_manual)
                json_filename = self.temp_dir / path.with_suffix('.json').name
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.log(f"✅ {ptype.capitalize()}: {path.name} → {json_filename.name}")
            except Exception as e:
                self.log(f"❌ Ошибка парсинга {path.name}: {e}")

        self.log("\n🎉 Загрузка завершена! JSON-файлы сохранены в папку ./temp/.")

    def predict_scores(self):
        # Проверяем, есть ли распарсенные файлы
        if not self.target_file:
            QMessageBox.warning(self, "Ошибка", "Целевой протокол не загружен!")
            return

        target_json_name = self.target_file.with_suffix('.json').name
        target_json_path = self.temp_dir / target_json_name
        if not target_json_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Целевой файл {target_json_name} не найден. Загрузите протоколы.")
            return

        with open(target_json_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)

        # Загрузка всех исторических JSON
        history_files = list(self.temp_dir.glob("*.json"))
        history_data = []
        for f in history_files:
            if f.name != target_json_name:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                history_data.append(data)

        # Импортируем логику
        from core.athlete_predictor import calculate_predicted_scores
        from core.utils import format_time
        athlete_name = self.name_input.text().strip()
        if not athlete_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя спортсмена!")
            return

        top3, details = calculate_predicted_scores(athlete_name, target_data, history_data)

        if not details:
            self.results_list.clear()
            self.total_label.setText("Спортсмен не найден или не имеет результатов.")
        else:
            self.results_list.clear()
            for d in details:
                time_str = format_time(d['time'])
                if d['place'] > 0:
                    self.results_list.addItem(f"{d['event_key']}: {time_str} (место {d['place']}, {d['points']} очков)")
                else:
                    self.results_list.addItem(f"{d['event_key']}: {time_str} (нет в протоколе)")

            total = sum(d['points'] for d in top3)
            self.total_label.setText(f"Итог: {total} очков (3 лучшие дистанции)")