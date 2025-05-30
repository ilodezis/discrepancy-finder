import sys
import os
import pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFileDialog,
    QAction, QToolBar, QStatusBar, QTableView, QTabWidget, QMessageBox,
    QHeaderView, QTextEdit, QLabel, QProgressDialog, QInputDialog, QStyleFactory,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QIcon, QPalette, QColor, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QSize, QAbstractTableModel, QModelIndex
import logging

# Logger
LOG_PATH = Path.home() / "discrepancy_finder.log"
logging.basicConfig(
    filename=str(LOG_PATH), level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode='a'
)

# Base directory
BASE_DIR = Path(__file__).parent.resolve()

# Translations
T = {
    'ru': {
        'window_title': 'Discrepancy Finder',
        'open_registry': 'Открыть реестр',
        'open_act': 'Открыть акт',
        'compare': 'Сравнить',
        'save': 'Сохранить',
        'clear': 'Очистить',
        'exit': 'Выход',
        'menu_file': 'Файл',
        'tab_results': 'Результаты',
        'tab_logs': 'Логи',
        'registry_label': 'Реестр: --',
        'act_label': 'Акт: --',
        'sum_registry': 'Сумма реестра: 0.00',
        'sum_act': 'Сумма акта: 0.00',
        'warn_load': 'Загрузите оба файла перед сравнением.',
        'err_id': 'Не найдены колонки ID. Доступные: {}',
        'err_amount': 'Не найдены колонки суммы. Доступные: {}',
        'err_load': 'Не удалось загрузить {}: {}',
        'no_diff': 'Расхождений не найдено.',
        'diff_found': 'Найдено {} расхождений.',
        'dlg_compare': 'Сравнение...',
        'save_dialog': 'Сохранить результаты',
        'msg_saved': 'Результаты сохранены:\n{}',
        'reminder': '<b>Напоминание:</b> выгружайте реестр во временной зоне UTC+3 и не забудьте добавить сумму реестра доставки (если доступна в регионе) и НДС по стране.'
    },
    'en': {
        'window_title': 'Discrepancy Finder',
        'open_registry': 'Open Registry',
        'open_act': 'Open Act',
        'compare': 'Compare',
        'save': 'Save',
        'clear': 'Clear',
        'exit': 'Exit',
        'menu_file': 'File',
        'tab_results': 'Results',
        'tab_logs': 'Logs',
        'registry_label': 'Registry: --',
        'act_label': 'Act: --',
        'sum_registry': 'Registry Total: 0.00',
        'sum_act': 'Act Total: 0.00',
        'warn_load': 'Please load both files before comparing.',
        'err_id': 'ID column not found. Available: {}',
        'err_amount': 'Amount column not found. Available: {}',
        'err_load': 'Failed to load {}: {}',
        'no_diff': 'No discrepancies found.',
        'diff_found': '{} discrepancies found.',
        'dlg_compare': 'Comparing...',
        'save_dialog': 'Save Results',
        'msg_saved': 'Saved:\n{}',
        'reminder': '<b>Reminder:</b> export the registry in UTC+3 and make sure to include delivery (if available in the region) and country-specific VAT in the total.'
    }
}

ID_KEYS = ["идентификатор заказа", "order id", "id заказа", "order no"]
AMOUNT_KEYS = ["сумма", "amount"]

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df
    def rowCount(self, parent=QModelIndex()): return len(self._df)
    def columnCount(self, parent=QModelIndex()): return len(self._df.columns)
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            return str(self._df.iat[index.row(), index.column()])
        return None
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return None

class LogHandler(logging.Handler):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        msg = self.format(record)
        self.log_widget.append(msg)

class MainWindow(QMainWindow):
    def __init__(self, lang_code):
        super().__init__()
        self.tr = T[lang_code]
        self.setWindowTitle(self.tr['window_title'])
        self.setWindowIcon(QIcon(resource_path('assets/icons/icons8-yandex-international-240.ico')))
        self.resize(900, 600)
        self.registry_path = None
        self.act_path = None
        self.diffs = pd.DataFrame()
        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        # Reminder banner
        self.reminder = QLabel(self.tr['reminder'], self)
        self.reminder.setTextFormat(Qt.RichText)
        self.reminder.setStyleSheet(
            'padding:8px; background:#fff3cd; border:1px solid #ffeeba; border-radius:6px;'
        )
        # Tab widget
        self.table = QTableView()
        self.log = QTextEdit(); self.log.setReadOnly(True)
        tabs = QTabWidget()
        tabs.addTab(self.table, self.tr['tab_results'])
        tabs.addTab(self.log, self.tr['tab_logs'])
        # Layout
        c = QWidget(); vbox = QVBoxLayout(c)
        vbox.setContentsMargins(12, 12, 12, 12)
        vbox.setSpacing(10)
        vbox.addWidget(self.reminder)
        vbox.addWidget(tabs)
        self.setCentralWidget(c)
        # Toolbar, menu, status
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        # Shadow for central widget
        shadow = QGraphicsDropShadowEffect(self.centralWidget())
        shadow.setBlurRadius(15)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.centralWidget().setGraphicsEffect(shadow)

    def _create_actions(self):
        ic = QIcon.fromTheme
        self.a_open_reg = QAction(ic('document-open'), self.tr['open_registry'], self)
        self.a_open_reg.triggered.connect(lambda: self._load('reg'))
        self.a_open_act = QAction(ic('document-open'), self.tr['open_act'], self)
        self.a_open_act.triggered.connect(lambda: self._load('act'))
        self.a_compare = QAction(ic('view-refresh'), self.tr['compare'], self)
        self.a_compare.setEnabled(False); self.a_compare.triggered.connect(self._compare)
        self.a_save = QAction(ic('document-save'), self.tr['save'], self)
        self.a_save.setEnabled(False); self.a_save.triggered.connect(self._save)
        self.a_clear = QAction(ic('edit-clear'), self.tr['clear'], self)
        self.a_clear.triggered.connect(self._clear)
        self.a_exit = QAction(self.tr['exit'], self)
        self.a_exit.triggered.connect(self.close)

    def _create_menu(self):
        m = self.menuBar().addMenu(self.tr['menu_file'])
        for a in [self.a_open_reg, self.a_open_act, None, self.a_compare, self.a_save, None, self.a_clear, None, self.a_exit]:
            m.addAction(a) if a else m.addSeparator()

    def _create_toolbar(self):
        tb = QToolBar(); tb.setIconSize(QSize(24, 24)); self.addToolBar(tb)
        for a in [self.a_open_reg, self.a_open_act, None, self.a_compare, self.a_save, None, self.a_clear, self.a_exit]:
            tb.addAction(a) if a else tb.addSeparator()
        tb.setStyleSheet(
            'QToolBar{background:#ececec; spacing:6px; border-radius:6px;}'
        )

    def _create_statusbar(self):
        sb = QStatusBar(); self.setStatusBar(sb)
        self.l_reg = QLabel(self.tr['registry_label']); sb.addPermanentWidget(self.l_reg)
        self.l_act = QLabel(self.tr['act_label']); sb.addPermanentWidget(self.l_act)
        self.l_sum_reg = QLabel(self.tr['sum_registry']); sb.addPermanentWidget(self.l_sum_reg)
        self.l_sum_act = QLabel(self.tr['sum_act']); sb.addPermanentWidget(self.l_sum_act)
        for lbl in (self.l_reg, self.l_act, self.l_sum_reg, self.l_sum_act):
            lbl.setStyleSheet(
                'padding:4px; border:1px solid #888; background:#eef; border-radius:4px;'
            )

    def _normalize(self, x):
        s = str(x).replace(' ', '')
        if ',' in s and '.' in s:
            s = s.replace('.', '') if s.rfind('.') < s.rfind(',') else s.replace(',', '')
        s = s.replace(',', '.')
        try: return float(s)
        except: return 0.0

    def _detect_header(self, path):
        raw = pd.read_excel(path, header=None, nrows=50, engine='openpyxl')
        header_index = None
        for i, row in raw.iterrows():
            txt = ' '.join(map(str, row.fillna(''))).lower()
            if any(k in txt for k in ID_KEYS):
                header_index = i; break
        if header_index is None:
            counts = raw.notna().sum(axis=1)
            max_rows = counts[counts == counts.max()].index
            if len(max_rows): header_index = int(max_rows[0])
        return header_index

    def _update_buttons(self):
        self.a_compare.setEnabled(bool(self.registry_path and self.act_path))

    def _load(self, mode):
        title = self.tr['open_registry'] if mode=='reg' else self.tr['open_act']
        path, _ = QFileDialog.getOpenFileName(self, title, '', 'Excel Files (*.xlsx *.xls)')
        if not path: return
        header = self._detect_header(path)
        if header is None:
            QMessageBox.critical(self, 'Error', self.tr['err_load'].format(Path(path).name, 'header not found'))
            return
        df = pd.read_excel(path, header=header, engine='openpyxl')
        cols = list(df.columns)
        id_cols = [c for c in cols if any(k in str(c).lower() for k in ID_KEYS)]
        amt_cols = [c for c in cols if any(k in str(c).lower() for k in AMOUNT_KEYS) and c not in id_cols]
        if not id_cols:
            QMessageBox.critical(self, 'Error', self.tr['err_id'].format(cols)); return
        if not amt_cols:
            QMessageBox.critical(self, 'Error', self.tr['err_amount'].format(cols)); return
        idc, amc = id_cols[0], amt_cols[0]
        df2 = df.loc[df[idc].notna() & ~df[idc].astype(str).str.lower().isin(['итого','total'])]
        df2 = df2.drop_duplicates(subset=[idc])
        total = df2[amc].apply(self._normalize).sum()
        if mode=='reg':
            self.registry_path = path
            self.l_reg.setText(f"{self.tr['open_registry']}: {Path(path).name}")
            self.l_sum_reg.setText(f"{self.tr['sum_registry'].split(':')[0]}: {total:,.2f}")
        else:
            self.act_path = path
            self.l_act.setText(f"{self.tr['open_act']}: {Path(path).name}")
            self.l_sum_act.setText(f"{self.tr['sum_act'].split(':')[0]}: {total:,.2f}")
        self._update_buttons()
        logging.info(f"Loaded {mode}: {path}")

    def _compare(self):
        if not(self.registry_path and self.act_path):
            QMessageBox.warning(self, 'Warning', self.tr['warn_load']); return
        dlg = QProgressDialog(self.tr['dlg_compare'], None, 0, 100, self)
        dlg.setWindowTitle(self.tr['dlg_compare'] if self.tr['dlg_compare'] == 'Сравнение...' else 'Finding discrepancies...')
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumWidth(300)  # Ensure the progress bar stretches properly
        dlg.setCancelButton(None)
        dlg.setValue(0)
        dlg.show()
        QApplication.processEvents()
        hdr1 = self._detect_header(self.registry_path)
        hdr2 = self._detect_header(self.act_path)
        try:
            df1 = pd.read_excel(self.registry_path, engine='openpyxl', header=hdr1 or 0)
            dlg.setValue(50)  # Update progress
        except Exception as e:
            dlg.close(); QMessageBox.critical(self, 'Error', self.tr['err_load'].format(Path(self.registry_path).name, str(e))); return
        try:
            df2 = pd.read_excel(self.act_path, engine='openpyxl', header=hdr2 or 0)
            dlg.setValue(100)  # Update progress
        except Exception as e:
            dlg.close(); QMessageBox.critical(self, 'Error', self.tr['err_load'].format(Path(self.act_path).name, str(e))); return
        dlg.close()
        id_list1 = [c for c in df1.columns if any(k in str(c).lower() for k in ID_KEYS)]
        if not id_list1: QMessageBox.critical(self,'Error',self.tr['err_id'].format(list(df1.columns)));return
        amt_list1 = [c for c in df1.columns if any(k in str(c).lower() for k in AMOUNT_KEYS) and c not in id_list1]
        if not amt_list1: QMessageBox.critical(self,'Error',self.tr['err_amount'].format(list(df1.columns)));return
        id1, amt1 = id_list1[0], amt_list1[0]
        id_list2 = [c for c in df2.columns if any(k in str(c).lower() for k in ID_KEYS)]
        if not id_list2: QMessageBox.critical(self,'Error',self.tr['err_id'].format(list(df2.columns)));return
        amt_list2 = [c for c in df2.columns if any(k in str(c).lower() for k in AMOUNT_KEYS) and c not in id_list2]
        if not amt_list2: QMessageBox.critical(self,'Error',self.tr['err_amount'].format(list(df2.columns)));return
        id2, amt2 = id_list2[0], amt_list2[0]
        r = df1.loc[df1[id1].notna() & ~df1[id1].astype(str).str.lower().isin(['итого','total'])].drop_duplicates(subset=[id1])
        a = df2.loc[df2[id2].notna() & ~df2[id2].astype(str).str.lower().isin(['итого','total'])].drop_duplicates(subset=[id2])
        reg = pd.DataFrame({'ID': r[id1].astype(str), 'Registry': r[amt1].apply(self._normalize)})
        act = pd.DataFrame({'ID': a[id2].astype(str), 'Act': a[amt2].apply(self._normalize)})
        merged = pd.merge(reg, act, on='ID', how='outer').fillna(0)
        merged['Diff'] = merged['Registry'] - merged['Act']
        diffs = merged.loc[merged['Diff'].abs() > 0.01]
        if diffs.empty:
            self.table.setModel(PandasModel()); self.a_save.setEnabled(False)
            QMessageBox.information(self,'Info',self.tr['no_diff']);return
        for col in ['Registry','Act','Diff']:
            diffs[col] = diffs[col].map(lambda x: f"{x:,.2f}")
        self.diffs = diffs
        self.table.setModel(PandasModel(self.diffs))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.a_save.setEnabled(True)
        QMessageBox.information(self,'Info',self.tr['diff_found'].format(len(diffs)))
        logging.info(f"Found {len(diffs)} discrepancies")

    def _clear(self):
        self.registry_path = None; self.act_path = None; self.diffs = pd.DataFrame()
        self.table.setModel(PandasModel(self.diffs)); self.log.clear()
        self.l_reg.setText(self.tr['registry_label']); self.l_act.setText(self.tr['act_label'])
        self.l_sum_reg.setText(self.tr['sum_registry']); self.l_sum_act.setText(self.tr['sum_act'])
        self.a_compare.setEnabled(False); self.a_save.setEnabled(False)
        logging.info("Cleared data")

    def _save(self):
        if self.diffs.empty: return
        default = Path.home() / 'Downloads' / 'discrepancies.txt'
        fn, _ = QFileDialog.getSaveFileName(self,self.tr['save_dialog'],str(default),'Text Files (*.txt)')
        if not fn: return
        with open(fn,'w',encoding='utf-8') as f:
            f.write('ID\tRegistry\tAct\tDiff\n')
            for _,row in self.diffs.iterrows(): f.write(f"{row['ID']}\t{row['Registry']}\t{row['Act']}\t{row['Diff']}\n")
        QMessageBox.information(self,self.tr['save_dialog'],self.tr['msg_saved'].format(fn))
        logging.info(f"Saved to {fn}")

    def _setup_logging(self):
        log_handler = LogHandler(self.log)
        log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)

def resource_path(relative_path):
    # Use sys._MEIPASS for PyInstaller compatibility
    base_path = getattr(sys, '_MEIPASS', BASE_DIR)
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Загрузка иконки
    icon_path = resource_path('assets/icons/icons8-yandex-international-240.ico')
    app.setWindowIcon(QIcon(icon_path))
    
    # Загрузка шрифта Inter
    font_path = resource_path('assets/fonts/Inter-VariableFont_opsz,wght.ttf')
    QFontDatabase.addApplicationFont(font_path)
    app.setFont(QFont('Inter', 10))
    
    # Глобальная таблица стилей
    app.setStyleSheet("""
        QWidget { font-family: 'Inter'; }
        QPushButton, QLineEdit, QComboBox {
            border: 1px solid #CCCCCC; border-radius: 6px; padding: 4px 8px; background-color: #FFFFFF;
        }
        QPushButton:hover { background-color: #F5F5F5; }
        QPushButton:pressed { background-color: #E6E6E6; }
        QTableWidget, QTableView {
            border: 1px solid #CCCCCC; border-radius: 6px; gridline-color: #E0E0E0;
        }
        QToolBar { background: #ECECEC; spacing: 6px; border-radius: 6px; }
        QMainWindow { background-color: #F0F0F0; }
        QGroupBox { background-color: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 8px; padding: 8px; margin-top: 20px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; margin-left: 10px; background-color: transparent; }
    """)
    # Палитра акцентов
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(240,240,240))
    pal.setColor(QPalette.Highlight, QColor(255,0,0))
    app.setPalette(pal)
    # Выбор языка
    lang, _ = QInputDialog.getItem(
        None, 
        T['en']['window_title'], 
        'Select language / Выберите язык', 
        ['English', 'Русский'], 
        0, 
        editable=False  # Ensure no "Cancel" button
    )
    code = 'en' if lang == 'English' else 'ru'
    win = MainWindow(code)
    win.show()
    sys.exit(app.exec_())
