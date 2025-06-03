"""Background task processing for Excel comparison."""

from pathlib import Path
import logging
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
import pandas as pd

from logic import ExcelProcessor


class CompareSignals(QObject):
    """Signals for Excel comparison background task."""

    finished = pyqtSignal(object)  # Emits DataFrame with results
    error = pyqtSignal(str)  # Emits error message
    progress = pyqtSignal(int)  # Emits progress percentage


class CompareFilesTask(QRunnable):
    """Background task for comparing Excel files."""

    def __init__(self, registry_path: Path, act_path: Path):
        super().__init__()
        self.registry_path = Path(registry_path)
        self.act_path = Path(act_path)
        self.signals = CompareSignals()
        self.processor = ExcelProcessor()

    @pyqtSlot()
    def run(self):
        """Execute the comparison task."""
        try:
            # Load registry file
            self.signals.progress.emit(10)
            reg_df, reg_id, reg_amt = self.processor.load_excel(self.registry_path)

            # Load act file
            self.signals.progress.emit(30)
            act_df, act_id, act_amt = self.processor.load_excel(self.act_path)

            # Preprocess data
            self.signals.progress.emit(50)
            reg_clean = self.processor.preprocess_dataframe(reg_df, reg_id, reg_amt)
            self.signals.progress.emit(70)
            act_clean = self.processor.preprocess_dataframe(act_df, act_id, act_amt)

            # Find discrepancies
            self.signals.progress.emit(90)
            result = self.processor.find_discrepancies(
                reg_clean, act_clean, reg_id, reg_amt, act_id, act_amt
            )
            self.signals.progress.emit(100)

            # Emit result
            self.signals.finished.emit(result)

        except (FileNotFoundError, pd.errors.EmptyDataError) as e:
            logging.exception("File error in comparison task")
            self.signals.error.emit(f"File error: {str(e)}")
        except ValueError as e:
            logging.exception("Value error in comparison task")
            self.signals.error.emit(str(e))
        except pd.errors.ParserError as e:
            logging.exception("Parser error in comparison task")
            self.signals.error.emit(f"Failed to parse Excel file: {str(e)}")
        except RuntimeError as e:
            logging.exception("Runtime error in comparison task")
            self.signals.error.emit(str(e))
