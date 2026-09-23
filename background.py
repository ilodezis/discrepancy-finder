"""Background task runner for heavy Excel work."""

import logging

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


class TaskSignals(QObject):
    """Signals for a background task."""

    finished = pyqtSignal(object)  # Emits the function result
    error = pyqtSignal(object)  # Emits the exception


class Task(QRunnable):
    """Run ``fn(*args)`` in a thread pool and report back via signals.

    Every exception is caught and forwarded, so the UI never waits forever.
    """

    def __init__(self, fn, *args):
        super().__init__()
        self.fn = fn
        self.args = args
        self.signals = TaskSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args)
        except Exception as e:  # noqa: BLE001 - anything must reach the UI
            logging.exception("Background task failed")
            self.signals.error.emit(e)
        else:
            self.signals.finished.emit(result)
