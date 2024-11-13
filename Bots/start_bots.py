from threading import Thread, stack_size

# from ds_main import main as start_ds
from tg_main import main as start_tg


def main():
    # ds_thread = Thread(target=start_ds)
    tg_thread = Thread(target=start_tg)

    stack_size(2 ** 20)

    # ds_thread.start()
    tg_thread.start()


if __name__ == "__main__":
    main()
