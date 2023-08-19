from arko.utils.reloader import Process, Reloader


def test():
    import time

    time.sleep(1)
    print("OK")


def main():
    reloader = Reloader(Process(test))
    reloader.run(background=True)
    print(reloader)
    import time

    time.sleep(2)


if __name__ == "__main__":
    main()
