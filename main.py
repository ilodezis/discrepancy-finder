"""GUI application for Discrepancy Finder."""

import logging
import os
import sys
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import (
    Qt,
    QSize,
    QModelIndex,
    QThreadPool,
    QAbstractTableModel,
)
from PyQt5.QtGui import (
    QIcon,
    QPalette,
    QColor,
    QFontDatabase,
    QFont,
)
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QGraphicsDropShadowEffect,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QStatusBar,
    QTabWidget,
    QTableView,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from logic import ExcelProcessor
from background import CompareFilesTask

# Initialize Excel processor
excel_processor = ExcelProcessor()

# Initialize logger using path from config
LOG_PATH = Path.home() / excel_processor.config.get(
    "log_path", "discrepancy_finder.log"
)
logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
)

# Base directory for resources
BASE_DIR = Path(__file__).parent.resolve()


class PandasModel(QAbstractTableModel):
    """Qt model for displaying pandas DataFrame in QTableView."""

    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            return str(self._df.iat[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return None


class LogHandler(logging.Handler):
    """Custom logging handler that writes to QTextEdit widget."""

    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.append(msg)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, lang_code):
        super().__init__()
        self.tr = excel_processor.load_translation(lang_code)
        self.config = excel_processor.config

        self.setWindowTitle(self.tr["window_title"])
        self.setWindowIcon(
            QIcon(resource_path("assets/icons/icons8-yandex-international-240.ico"))
        )
        self.resize(self.config["window"]["width"], self.config["window"]["height"])

        self.registry_path = None
        self.act_path = None
        self.diffs = pd.DataFrame()
        self.thread_pool = QThreadPool()

        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        """Build the user interface."""
        # Reminder banner
        self.reminder = QLabel(self.tr["reminder"], self)
        self.reminder.setTextFormat(Qt.RichText)
        self.reminder.setStyleSheet(
            "padding:8px; background:#fff3cd; border:1px solid #ffeeba; border-radius:6px;"
        )

        # Tab widget
        self.table = QTableView()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        tabs = QTabWidget()
        tabs.addTab(self.table, self.tr["tab_results"])
        tabs.addTab(self.log, self.tr["tab_logs"])

        # Layout
        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)
        vbox.addWidget(self.reminder)
        vbox.addWidget(tabs)
        self.setCentralWidget(central)

        # Create UI elements
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self.centralWidget())
        shadow.setBlurRadius(self.config["colors"]["shadow"]["blur"])
        shadow.setOffset(self.config["colors"]["shadow"]["offset"])
        shadow.setColor(rgba_to_qcolor(self.config["colors"]["shadow"]["color"]))
        self.centralWidget().setGraphicsEffect(shadow)

    def _create_actions(self):
        """Create application actions."""
        ic = QIcon.fromTheme
        self.a_open_reg = QAction(ic("document-open"), self.tr["open_registry"], self)
        self.a_open_reg.triggered.connect(lambda: self._load("reg"))

        self.a_open_act = QAction(ic("document-open"), self.tr["open_act"], self)
        self.a_open_act.triggered.connect(lambda: self._load("act"))

        self.a_compare = QAction(ic("view-refresh"), self.tr["compare"], self)
        self.a_compare.setEnabled(False)
        self.a_compare.triggered.connect(self._compare)

        self.a_save = QAction(ic("document-save"), self.tr["save"], self)
        self.a_save.setEnabled(False)
        self.a_save.triggered.connect(self._save)

        self.a_clear = QAction(ic("edit-clear"), self.tr["clear"], self)
        self.a_clear.triggered.connect(self._clear)

        self.a_exit = QAction(self.tr["exit"], self)
        self.a_exit.triggered.connect(self.close)

    def _create_menu(self):
        """Create application menu."""
        menu = self.menuBar().addMenu(self.tr["menu_file"])
        actions = [
            self.a_open_reg,
            self.a_open_act,
            None,
            self.a_compare,
            self.a_save,
            None,
            self.a_clear,
            None,
            self.a_exit,
        ]
        for action in actions:
            if action:
                menu.addAction(action)
            else:
                menu.addSeparator()

    def _create_toolbar(self):
        """Create application toolbar."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        actions = [
            self.a_open_reg,
            self.a_open_act,
            None,
            self.a_compare,
            self.a_save,
            None,
            self.a_clear,
            self.a_exit,
        ]
        for action in actions:
            if action:
                toolbar.addAction(action)
            else:
                toolbar.addSeparator()

        # Load style from file
        with open(Path(BASE_DIR) / "style.qss", "r") as f:
            toolbar.setStyleSheet(f.read())

    def _create_statusbar(self):
        """Create application status bar."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        self.l_reg = QLabel(self.tr["registry_label"])
        self.l_act = QLabel(self.tr["act_label"])
        self.l_sum_reg = QLabel(self.tr["sum_registry"])
        self.l_sum_act = QLabel(self.tr["sum_act"])

        for label in (self.l_reg, self.l_act, self.l_sum_reg, self.l_sum_act):
            statusbar.addPermanentWidget(label)
            label.setStyleSheet(
                "padding:4px; border:1px solid #888; background:#eef; border-radius:4px;"
            )

    def _load(self, mode):
        """Load Excel file for registry or act."""
        title = self.tr["open_registry"] if mode == "reg" else self.tr["open_act"]
        path, _ = QFileDialog.getOpenFileName(
            self, title, "", "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return

        try:
            df, id_col, amt_col = excel_processor.load_excel(Path(path))
            df_clean = excel_processor.preprocess_dataframe(df, id_col, amt_col)
            total = pd.to_numeric(df_clean[amt_col], errors="coerce").fillna(0).sum()

            if mode == "reg":
                self.registry_path = path
                self.l_reg.setText(f"{self.tr['open_registry']}: {Path(path).name}")
                self.l_sum_reg.setText(
                    f"{self.tr['sum_registry'].split(':')[0]}: {total:,.2f}"
                )
            else:
                self.act_path = path
                self.l_act.setText(f"{self.tr['open_act']}: {Path(path).name}")
                self.l_sum_act.setText(
                    f"{self.tr['sum_act'].split(':')[0]}: {total:,.2f}"
                )

            self._update_buttons()
            logging.info("Loaded %s: %s", mode, path)

        except FileNotFoundError as e:
            logging.exception("Failed to find file: %s", path)
            QMessageBox.critical(
                self, "Error", self.tr["err_load"].format(Path(path).name, str(e))
            )
        except pd.errors.EmptyDataError:
            logging.exception("Empty file: %s", path)
            QMessageBox.critical(
                self,
                "Error",
                self.tr["err_load"].format(Path(path).name, "File is empty"),
            )
        except (pd.errors.ParserError, ValueError) as e:
            logging.exception("Failed to parse file: %s", path)
            QMessageBox.critical(
                self, "Error", self.tr["err_load"].format(Path(path).name, str(e))
            )

    def _update_buttons(self):
        """Update button states based on loaded files."""
        self.a_compare.setEnabled(bool(self.registry_path and self.act_path))

    def _compare(self):
        """Compare Excel files in background thread."""
        if not (self.registry_path and self.act_path):
            QMessageBox.warning(self, "Warning", self.tr["warn_load"])
            return

        # Create progress dialog
        self.dlg = QProgressDialog(self.tr["dlg_compare"], None, 0, 100, self)
        self.dlg.setWindowTitle(self.tr["dlg_compare"])
        self.dlg.setWindowModality(Qt.WindowModal)
        self.dlg.setMinimumWidth(300)
        self.dlg.setCancelButton(None)
        self.dlg.setValue(0)
        self.dlg.show()

        # Create and start background task
        task = CompareFilesTask(self.registry_path, self.act_path)
        task.signals.progress.connect(self.dlg.setValue)
        task.signals.finished.connect(self._handle_comparison_result)
        task.signals.error.connect(self._handle_comparison_error)
        self.thread_pool.start(task)

    def _handle_comparison_result(self, diffs):
        """Handle successful comparison results."""
        self.dlg.close()

        if diffs.empty:
            self.table.setModel(PandasModel())
            self.a_save.setEnabled(False)
            QMessageBox.information(self, "Info", self.tr["no_diff"])
            return

        self.diffs = diffs
        self.table.setModel(PandasModel(self.diffs))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.a_save.setEnabled(True)

        QMessageBox.information(self, "Info", self.tr["diff_found"].format(len(diffs)))
        logging.info("Found %s discrepancies", len(diffs))

    def _handle_comparison_error(self, error_msg):
        """Handle comparison task errors."""
        self.dlg.close()
        QMessageBox.critical(self, "Error", str(error_msg))

    def _clear(self):
        """Clear all loaded data."""
        self.registry_path = None
        self.act_path = None
        self.diffs = pd.DataFrame()

        self.table.setModel(PandasModel())
        self.log.clear()

        self.l_reg.setText(self.tr["registry_label"])
        self.l_act.setText(self.tr["act_label"])
        self.l_sum_reg.setText(self.tr["sum_registry"])
        self.l_sum_act.setText(self.tr["sum_act"])

        self.a_compare.setEnabled(False)
        self.a_save.setEnabled(False)

        logging.info("Cleared data")

    def _save(self):
        """Save comparison results to file."""
        if self.diffs.empty:
            return

        default = Path.home() / "Downloads" / "discrepancies.txt"
        fn, _ = QFileDialog.getSaveFileName(
            self, self.tr["save_dialog"], str(default), "Text Files (*.txt)"
        )
        if not fn:
            return

        try:
            with open(fn, "w", encoding="utf-8") as f:
                f.write("ID\tRegistry\tAct\tDiff\n")
                for _, row in self.diffs.iterrows():
                    f.write(
                        f"{row['ID']}\t{row['Registry']}\t{row['Act']}\t{row['Diff']}\n"
                    )

            QMessageBox.information(
                self, self.tr["save_dialog"], self.tr["msg_saved"].format(fn)
            )
            logging.info("Saved to %s", fn)

        except PermissionError as e:
            logging.exception("Permission denied when saving to %s", fn)
            QMessageBox.critical(
                self,
                "Error",
                f"Access denied. Make sure you have write permissions: {str(e)}",
            )
        except OSError as e:
            logging.exception("Failed to save %s", fn)
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")

    def _setup_logging(self):
        """Setup logging to both file and GUI."""
        handler = LogHandler(self.log)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)


def hex_to_rgb(hex_color):
    """Convert hex color string to RGB tuple."""
    hex_str = hex_color.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgba_to_qcolor(rgba):
    """Convert RGBA values to QColor."""
    if len(rgba) != 4:
        raise ValueError("RGBA color must have 4 components")
    return QColor(rgba[0], rgba[1], rgba[2], rgba[3])


def resource_path(relative_path):
    """Get absolute path to resource for PyInstaller compatibility."""
    base_path = getattr(sys, "_MEIPASS", BASE_DIR)
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load assets
    icon_path = resource_path("assets/icons/icons8-yandex-international-240.ico")
    app.setWindowIcon(QIcon(icon_path))

    font_path = resource_path("assets/fonts/Inter-VariableFont_opsz,wght.ttf")
    QFontDatabase.addApplicationFont(font_path)
    app.setFont(QFont("Inter", 10))

    # Load and apply global stylesheet
    with open(Path(BASE_DIR) / "style.qss", "r") as f:
        app.setStyleSheet(f.read())

    # Set color palette
    palette = QPalette()

    # Set window background color
    bg_color = hex_to_rgb(excel_processor.config["colors"]["window_background"])
    palette.setColor(QPalette.Window, QColor(*bg_color))

    # Set accent color
    accent_color = hex_to_rgb(excel_processor.config["colors"]["accent"])
    palette.setColor(QPalette.Highlight, QColor(*accent_color))

    app.setPalette(palette)

    # Show language selection dialog with built-in strings first
    lang, _ = QInputDialog.getItem(
        None,
        "Select Language",
        "Select language / Выберите язык",
        ["English", "Русский"],
        0,
        editable=False,
    )
    code = "en" if lang == "English" else "ru"

    # Create and show main window
    win = MainWindow(code)
    win.show()

    sys.exit(app.exec_())
