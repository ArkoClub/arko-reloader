# Arko Reloader

支持自动重载的重载器

```python
import time
from multiprocessing import Queue

from arko.utils.reloader import Process, Reloader, SIGNAL


def test(signal_queue: Queue):
    from random import choice

    if result := choice([False, True]):
        signal_queue.put(SIGNAL.RELOAD)

    print(f"Reload: {result}")
    time.sleep(1)
    print(time.time())


def main():
    signal_queue = Queue()
    reloader = Reloader(
        Process(test, signal_queue=signal_queue), process_signal_queue=signal_queue
    )
    reloader.run(background=False)


if __name__ == "__main__":
    main()

```