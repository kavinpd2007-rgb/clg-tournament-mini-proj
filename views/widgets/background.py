"""Background task runner with Tk-thread callback delivery."""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from queue import Empty, Queue
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")

@dataclass(slots=True)
class Completion(Generic[T]):
    future: Future[T]
    on_success: Callable[[T], None]
    on_error: Callable[[BaseException], None]

class BackgroundTasks:
    """Run blocking work off-thread; all callbacks run from the Tk event loop."""
    def __init__(self, root: Any, workers: int = 4):
        self._root = root
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="sports-db")
        self._completed: Queue[Completion[Any]] = Queue()
        self._closed = False

    def start(self) -> None:
        self._root.after(60, self._drain)

    def submit(self, work: Callable[[], T], on_success: Callable[[T], None], on_error: Callable[[BaseException], None]) -> Future[T]:
        future = self._executor.submit(work)
        completion: Completion[T] = Completion(future, on_success, on_error)
        future.add_done_callback(lambda _: self._completed.put(completion))
        return future

    def shutdown(self) -> None:
        self._closed = True
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _drain(self) -> None:
        if self._closed:
            return
        while True:
            try:
                completion = self._completed.get_nowait()
            except Empty:
                break
            try:
                value = completion.future.result()
            except BaseException as exc:
                completion.on_error(exc)
            else:
                completion.on_success(value)
        self._root.after(60, self._drain)
