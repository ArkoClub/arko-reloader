from pathlib import Path
from arko.utils.reloader import Process, FileReloader, FileWatcher


def test():
    import time

    time.sleep(5)
    print("OK")


def main():
    reloader = FileReloader(
        Process(test), FileWatcher(Path("Y:\\Arko\\arko-reloader\\test"))
    )
    reloader.run(background=True)
    print(reloader)
    import time

    time.sleep(3)


if __name__ == "__main__":
    main()
