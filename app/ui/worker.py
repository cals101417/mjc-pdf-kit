"""Run slow PDF work off the UI thread; deliver results back on it.

Tk isn't thread-safe, so the worker never touches widgets. It drops messages
in a queue that the UI polls every 80 ms.
"""

from __future__ import annotations

import queue
import threading
import traceback
from typing import Any, Callable


class Worker:
    def __init__(self, root):
        self.root = root
        self.inbox: queue.Queue = queue.Queue()
        self.busy = False
        self._poll()

    def _poll(self) -> None:
        try:
            while True:
                callback, args = self.inbox.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def post(self, callback: Callable, *args: Any) -> None:
        """Call from the worker thread to run `callback(*args)` on the UI thread."""
        self.inbox.put((callback, args))

    def run(self, job: Callable[[], Any], on_done: Callable[[Any], None],
            on_error: Callable[[str], None]) -> bool:
        if self.busy:
            return False
        self.busy = True

        def target():
            try:
                result = job()
            except Exception as exc:  # shown to the user, so keep it readable
                message = str(exc) or exc.__class__.__name__
                traceback.print_exc()
                self.post(self._finish, on_error, message)
            else:
                self.post(self._finish, on_done, result)

        threading.Thread(target=target, daemon=True).start()
        return True

    def _finish(self, callback: Callable, value: Any) -> None:
        self.busy = False
        callback(value)
