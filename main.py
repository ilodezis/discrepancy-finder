"""GUI application for Discrepancy Finder."""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QSize,
    Qt,
    QThreadPool,
    pyqtSignal,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QFontDatabase, QIcon, QPalette
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QStatusBar,
    QTableView,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from background import Task
from logic import (
    STATUS_ONLY_ACT,
    STATUS_ONLY_REGISTRY,
    DataError,
    ExcelProcessor,
    __version__,
    resource_path,
)

ICON_PATH = "assets/icons/icons8-yandex-international-240.ico"
FONT_PATH = "assets/fonts/Inter-VariableFont_opsz,wght.ttf"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

ROOT_INDEX = QModelIndex()
RESULT_COLUMNS = ["ID", "Registry", "Act", "Diff", "Status"]
STATUS_COLORS = {
    STATUS_ONLY_REGISTRY: QColor("#FFF4E5"),
    STATUS_ONLY_ACT: QColor("#E8F1FF"),
}


def load_languages():
    """Return {code: translations} for every i18n/*.json file."""
    languages = {}
    for path in sorted(resource_path("i18n").glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            languages[path.stem] = json.load(f)
    return languages


def format_amount(value):
    return f"{value:,.2f}"


class ResultsModel(QAbstractTableModel):
    """Qt model for the discrepancy table, sortable by any column."""

    def __init__(self, tr, df=None, parent=None):
        super().__init__(parent)
        self.tr = tr
        self._df = df if df is not None else pd.DataFrame(columns=RESULT_COLUMNS)

    def rowCount(self, parent=ROOT_INDEX):
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=ROOT_INDEX):
        return 0 if parent.isValid() else len(RESULT_COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        column = RESULT_COLUMNS[index.column()]
        value = self._df.iat[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if column == "Status":
                return self.tr[f"status_{value}"]
            if column in ("Registry", "Act", "Diff"):
                return format_amount(value)
            return str(value)
        if role == Qt.TextAlignmentRole and column in ("Registry", "Act", "Diff"):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        if role == Qt.BackgroundRole:
            color = STATUS_COLORS.get(self._df.iat[index.row(), 4])
            return QBrush(color) if color else None
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.tr[f"col_{RESULT_COLUMNS[section].lower()}"]
        return str(section + 1)

    def sort(self, column, order=Qt.AscendingOrder):
        name = RESULT_COLUMNS[column]
        key = (lambda s: s.abs()) if name == "Diff" else None
        self.layoutAboutToBeChanged.emit()
        self._df = self._df.sort_values(
            name, ascending=order == Qt.AscendingOrder, key=key, kind="stable"
        ).reset_index(drop=True)
        self.layoutChanged.emit()


class LogBridge(QObject):
    """Carries log messages from any thread to the GUI thread."""

    message = pyqtSignal(str)


class LogHandler(logging.Handler):
    """Logging handler that forwards records to a QTextEdit via a signal."""

    def __init__(self, log_widget):
        super().__init__()
        self.bridge = LogBridge()
        self.bridge.message.connect(log_widget.append)

    def emit(self, record):
        self.bridge.message.emit(self.format(record))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, tr, processor):
        super().__init__()
        self.tr = tr
        self.processor = processor
        self.config = processor.config

        self.setWindowTitle(f"{self.tr['window_title']} {__version__}")
        self.setWindowIcon(QIcon(str(resource_path(ICON_PATH))))
        self.resize(self.config["window"]["width"], self.config["window"]["height"])

        self.files = {"reg": None, "act": None}
        self.diffs = pd.DataFrame(columns=RESULT_COLUMNS)
        self.thread_pool = QThreadPool.globalInstance()
        self._tasks = set()
        self.dlg = None

        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        """Build the user interface."""
        self.reminder = QLabel(self.tr["reminder"], self)
        self.reminder.setObjectName("reminder")
        self.reminder.setTextFormat(Qt.RichText)
        self.reminder.setWordWrap(True)

        self.table = QTableView()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # Default order matches find_discrepancies: biggest |Diff| first
        header.setSortIndicator(RESULT_COLUMNS.index("Diff"), Qt.DescendingOrder)
        self.table.setSortingEnabled(True)
        self.table.setModel(ResultsModel(self.tr))

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        tabs = QTabWidget()
        tabs.addTab(self.table, self.tr["tab_results"])
        tabs.addTab(self.log, self.tr["tab_logs"])

        central = QWidget()
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)
        vbox.addWidget(self.reminder)
        vbox.addWidget(tabs)
        self.setCentralWidget(central)

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()

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

    def _main_actions(self):
        return [
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

    def _create_menu(self):
        """Create application menu."""
        menu = self.menuBar().addMenu(self.tr["menu_file"])
        for action in self._main_actions():
            if action:
                menu.addAction(action)
            else:
                menu.addSeparator()

    def _create_toolbar(self):
        """Create application toolbar."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for action in self._main_actions():
            if action:
                toolbar.addAction(action)
            else:
                toolbar.addSeparator()

    def _create_statusbar(self):
        """Create application status bar."""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        self.labels = {"reg": QLabel(), "act": QLabel()}
        for label in self.labels.values():
            label.setObjectName("fileLabel")
            statusbar.addPermanentWidget(label)
        self._update_file_labels()

    def _update_file_labels(self):
        """Show loaded file names, detected columns and totals."""
        names = {"reg": "registry", "act": "act"}
        for mode, label in self.labels.items():
            loaded = self.files[mode]
            name = names[mode]
            if loaded is None:
                label.setText(self.tr[f"{name}_label"].format("--", format_amount(0)))
                label.setToolTip("")
                continue
            label.setText(
                self.tr[f"{name}_label"].format(
                    loaded.path.name, format_amount(loaded.total)
                )
            )
            label.setToolTip(
                self.tr["file_tooltip"].format(
                    loaded.id_col, loaded.amount_col, loaded.rows, len(loaded.data)
                )
            )

    def _run(self, title, fn, args, on_finished):
        """Run ``fn(*args)`` in the background behind a busy dialog."""
        self.dlg = QProgressDialog(title, None, 0, 0, self)
        self.dlg.setWindowTitle(title)
        self.dlg.setWindowModality(Qt.WindowModal)
        self.dlg.setMinimumWidth(300)
        self.dlg.setCancelButton(None)
        self.dlg.setMinimumDuration(0)
        self.dlg.show()

        task = Task(fn, *args)
        task.setAutoDelete(False)
        self._tasks.add(task)

        def done(handler, payload):
            self._tasks.discard(task)
            self.dlg.close()
            handler(payload)

        task.signals.finished.connect(lambda result: done(on_finished, result))
        task.signals.error.connect(lambda error: done(self._show_error, error))
        self.thread_pool.start(task)

    def _show_error(self, error):
        if isinstance(error, DataError):
            message = self.tr[error.key].format(*error.params)
        else:
            message = f"{type(error).__name__}: {error}"
        QMessageBox.critical(self, self.tr["title_error"], message)

    def _load(self, mode):
        """Load Excel file for registry or act."""
        title = self.tr["open_registry"] if mode == "reg" else self.tr["open_act"]
        path, _ = QFileDialog.getOpenFileName(
            self, title, "", "Excel (*.xlsx *.xlsm *.xls)"
        )
        if not path:
            return

        def loaded(result):
            self.files[mode] = result
            self._update_file_labels()
            self._update_buttons()
            if result.unparsed_amounts:
                QMessageBox.warning(
                    self,
                    self.tr["title_warning"],
                    self.tr["warn_unparsed"].format(
                        result.unparsed_amounts, result.path.name
                    ),
                )

        self._run(self.tr["dlg_load"], self.processor.load_file, (Path(path),), loaded)

    def _update_buttons(self):
        """Update button states based on loaded files."""
        self.a_compare.setEnabled(all(self.files.values()))

    def _compare(self):
        """Compare the loaded files."""
        reg, act = self.files["reg"], self.files["act"]
        if not (reg and act):
            QMessageBox.warning(self, self.tr["title_warning"], self.tr["warn_load"])
            return
        self._run(
            self.tr["dlg_compare"],
            self.processor.find_discrepancies,
            (reg.data, act.data),
            self._show_results,
        )

    def _show_results(self, diffs):
        """Display comparison results."""
        self.diffs = diffs
        self.table.setModel(ResultsModel(self.tr, diffs))
        self.a_save.setEnabled(not diffs.empty)

        if diffs.empty:
            QMessageBox.information(self, self.tr["title_info"], self.tr["no_diff"])
            logging.info("No discrepancies found")
            return

        counts = diffs["Status"].value_counts()
        QMessageBox.information(
            self,
            self.tr["title_info"],
            self.tr["diff_found"].format(
                len(diffs),
                counts.get(STATUS_ONLY_REGISTRY, 0),
                counts.get(STATUS_ONLY_ACT, 0),
                format_amount(diffs["Diff"].sum()),
            ),
        )
        logging.info("Found %d discrepancies", len(diffs))

    def _clear(self):
        """Clear all loaded data."""
        self.files = {"reg": None, "act": None}
        self.diffs = pd.DataFrame(columns=RESULT_COLUMNS)
        self.table.setModel(ResultsModel(self.tr))
        self.log.clear()
        self._update_file_labels()
        self.a_compare.setEnabled(False)
        self.a_save.setEnabled(False)
        logging.info("Cleared data")

    def _export_frame(self):
        """Results with translated headers and statuses, ready for export."""
        df = self.diffs.copy()
        df["Status"] = df["Status"].map(lambda s: self.tr[f"status_{s}"])
        return df.rename(
            columns={c: self.tr[f"col_{c.lower()}"] for c in RESULT_COLUMNS}
        )

    def _save(self):
        """Save comparison results to .xlsx or tab-separated .txt."""
        if self.diffs.empty:
            return

        default = Path.home() / "Downloads" / "discrepancies.xlsx"
        fn, _ = QFileDialog.getSaveFileName(
            self,
            self.tr["save_dialog"],
            str(default),
            "Excel (*.xlsx);;Text (*.txt)",
        )
        if not fn:
            return

        path = Path(fn)
        if path.suffix.lower() not in (".xlsx", ".txt"):
            path = path.with_suffix(".xlsx")

        try:
            df = self._export_frame()
            if path.suffix.lower() == ".xlsx":
                df.to_excel(path, index=False)
            else:
                df.to_csv(path, sep="\t", index=False, float_format="%.2f")
        except OSError as e:
            logging.exception("Failed to save %s", path)
            QMessageBox.critical(
                self, self.tr["title_error"], self.tr["err_save"].format(path, e)
            )
            return

        QMessageBox.information(
            self, self.tr["save_dialog"], self.tr["msg_saved"].format(path)
        )
        logging.info("Saved to %s", path)

    def _setup_logging(self):
        """Mirror log records to the Logs tab."""
        handler = LogHandler(self.log)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(handler)


def setup_file_logging(config):
    """Log to a file in the user's home directory."""
    handlers = []
    try:
        handlers.append(
            logging.FileHandler(Path.home() / config["log_path"], encoding="utf-8")
        )
    except OSError:
        pass  # Read-only home: keep logging to the GUI only
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=handlers)


def choose_language(languages):
    """Ask for the UI language; returns None if the dialog was cancelled."""
    names = [tr["language_name"] for tr in languages.values()]
    name, ok = QInputDialog.getItem(
        None, "Discrepancy Finder", "Language / Язык", names, 0, editable=False
    )
    if not ok:
        return None
    return next(tr for tr in languages.values() if tr["language_name"] == name)


def main():
    app = QApplication(sys.argv)
    processor = ExcelProcessor()
    config = processor.config
    setup_file_logging(config)

    app.setWindowIcon(QIcon(str(resource_path(ICON_PATH))))
    QFontDatabase.addApplicationFont(str(resource_path(FONT_PATH)))
    app.setFont(QFont("Inter", 10))

    with open(resource_path("style.qss"), "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(config["colors"]["window_background"]))
    palette.setColor(QPalette.Highlight, QColor(config["colors"]["accent"]))
    app.setPalette(palette)

    tr = choose_language(load_languages())
    if tr is None:
        return 0

    win = MainWindow(tr, processor)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
