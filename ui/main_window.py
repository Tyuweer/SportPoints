import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QListWidget, QGroupBox,
    QMessageBox, QTextEdit, QLineEdit, QDialog, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt
from pathlib import Path
import json
from PyQt5.QtGui import QIcon

from parsers.parser_factory import get_parser_by_name, PARSERS

class ParserSelectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выберите тип соревнования и фиксацию")
        layout = QVBoxLayout()

        # Выбор типа соревнования
        layout.addWidget(QLabel("Тип соревнования:"))
        self.parser_combo = QComboBox()
        self.parser_combo.addItems(PARSERS.keys())
        layout.addWidget(self.parser_combo)

        # Ручная фиксация
        self.manual_fix_cb = QCheckBox("Ручная фиксация (+0.2 сек)")
        layout.addWidget(self.manual_fix_cb)

        # Кнопка OK
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        self.setLayout(layout)

    def get_selection(self):
        parser_name = self.parser_combo.currentText()
        is_manual = self.manual_fix_cb.isChecked()
        return parser_name, is_manual
    

class PredictorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расчет очков")
        self.resize(1200, 800)

        self.setWindowIcon(QIcon('icon.ico'))
        # Папка для JSON
        self.temp_dir = Path("./temp")
        self.temp_dir.mkdir(exist_ok=True)

        # Хранение файлов: [(path, parser_name, is_manual)]
        self.target_file = None
        self.target_parser = None
        self.target_is_manual = False
        self.history_files = []  # [(path, parser_name, is_manual)]

        self.init_ui()

    def closeEvent(self, event):
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

        self.history_add_btn = QPushButton("Добавить протокол")
        self.history_add_btn.clicked.connect(self.add_history_file)
        self.history_remove_btn = QPushButton("Удалить")
        self.history_remove_btn.clicked.connect(self.remove_selected)
        self.history_list = QListWidget()
        self.history_list.setFixedHeight(100)
        self.history_list.setFixedWidth(350)

        hist_layout = QHBoxLayout()
        hist_layout.addWidget(self.history_add_btn)
        hist_layout.addWidget(self.history_remove_btn)
        hist_layout.addWidget(self.history_list)
        history_layout.addLayout(hist_layout)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # === Кнопка загрузки протоколов ===
        self.parse_btn = QPushButton("Загрузить протоколы")
        self.parse_btn.clicked.connect(self.parse_all)
        layout.addWidget(self.parse_btn)

        # === Расчёт очков ===
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

        # === Минималистичный стиль ===
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                border: 1px solid #ccc;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
            QListWidget { border: 1px solid #ccc; border-radius: 4px; }
        """)

    def select_target(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите целевой PDF", "", "PDF Files (*.pdf)")
        if path:
            dialog = ParserSelectionDialog()
            if dialog.exec_() == QDialog.Accepted:
                parser_name, is_manual = dialog.get_selection()
                self.target_file = Path(path)
                self.target_parser = parser_name
                self.target_is_manual = is_manual
                self.target_label.setText(f"{path.split('/')[-1]} ({parser_name})")

    def add_history_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Выберите PDF", "", "PDF Files (*.pdf)")
        for p in paths:
            dialog = ParserSelectionDialog()
            if dialog.exec_() == QDialog.Accepted:
                parser_name, is_manual = dialog.get_selection()
                path = Path(p)
                self.history_files.append((path, parser_name, is_manual))
                self.history_list.addItem(f"{path.name} ({parser_name})")

    def remove_selected(self):
        selected = self.history_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите файл для удаления.")
            return
        name = selected.text()
        self.history_files[:] = [f for f in self.history_files if f[0].name not in name]
        self.history_list.takeItem(self.history_list.row(selected))

    def log(self, msg):
        self.log_area.append(msg)

    def parse_all(self):
        # Очистка
        for f in self.temp_dir.glob("*.json"):
            f.unlink()

        # Парсинг целевого
        if self.target_file:
            try:
                parser = get_parser_by_name(self.target_parser)
                data = parser.parse(self.target_file, is_manual=self.target_is_manual)
                json_path = self.temp_dir / f"target_{self.target_parser}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.log(f"✅ Целевой: {self.target_file.name} → {json_path.name}")
            except Exception as e:
                self.log(f"❌ Ошибка парсинга целевого: {e}")

        # Парсинг истории
        for path, parser_name, is_manual in self.history_files:
            try:
                parser = get_parser_by_name(parser_name)
                data = parser.parse(path, is_manual=is_manual)
                json_path = self.temp_dir / f"{path.stem}_{parser_name}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.log(f"✅ История: {path.name} → {json_path.name}")
            except Exception as e:
                self.log(f"❌ Ошибка парсинга {path.name}: {e}")

        self.log("\n🎉 Загрузка завершена!")

    def predict_scores(self):
        # Загрузка всех JSON
        all_json = list(self.temp_dir.glob("*.json"))
        if not all_json:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите протоколы!")
            return

        target_data = []
        history_data = []

        for f in all_json:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
            if "target_" in f.name:
                target_data.extend(data)
            else:
                history_data.append(data)

        athlete_name = self.name_input.text().strip()
        if not athlete_name:
            QMessageBox.warning(self, "Ошибка", "Введите имя спортсмена!")
            return

        from core.athlete_predictor import calculate_predicted_scores
        from core.utils import format_time

        top3, details = calculate_predicted_scores(athlete_name, target_data, history_data)

        self.results_list.clear()
        if not details:
            self.total_label.setText("Спортсмен не найден.")
        else:
            for d in details:
                time_str = format_time(d['time'])
                if d['place'] > 0:
                    self.results_list.addItem(f"{d['event_key']}: {time_str} (место {d['place']}, {d['points']} очков)")
                else:
                    self.results_list.addItem(f"{d['event_key']}: {time_str} (нет в протоколе)")
            total = sum(d['points'] for d in top3)
            self.total_label.setText(f"Итог: {total} очков (3 лучшие дистанции)")