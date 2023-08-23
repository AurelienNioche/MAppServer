from multiprocessing import Pool, Value
from tqdm import tqdm
import time


def _foo(my_number):
    square = my_number * my_number
    time.sleep(1)
    with shared_counter.get_lock():
        shared_counter.value += 1
    return square

def init_globals(counter):
    global shared_counter
    shared_counter = counter


def wrapper(kwargs):
    return _foo(**kwargs)


if __name__ == '__main__':
    counter = Value('i', 0)
    with Pool(2, initializer=init_globals, initargs=(counter,)) as p:
        result = p.map_async(wrapper, [dict(my_number=i) for i in range(30)])

        with tqdm(total=30) as pbar:
            while not result.ready():
                pbar.n = counter.value
                pbar.refresh()
                time.sleep(0.1)
            pbar.n = counter.value
            pbar.refresh()
        r = result.get()