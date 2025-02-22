from concurrent.futures import Future, ProcessPoolExecutor
from multiprocessing import Manager
import time

class TaskManager:
    def __init__(self, max_workers=4):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.manager = Manager()
        self.count = 0  # Số lượng task đang chạy
        self.state = self.manager.Event()
        self.lock = self.manager.Lock()

    def _task_done_callback(self, future:Future):
        """ Wrapper để giảm bộ đếm sau khi task hoàn thành """
        print(f"----------------- {future.result()}")
        # result = future.result()
        with self.lock:
            self.count -= 1
            if self.count == 0:
                self.state.set()  # Đánh dấu tất cả task đã hoàn thành
        # return result

    def start(self, fn, *args, **kwargs):
        """ Submit một task và tăng bộ đếm """
        with self.lock:
          self.count += 1
          self.state.clear()  # Đặt lại event nếu có task mới

        future =  self.executor.submit(fn, *args, **kwargs)
        future.add_done_callback(self._task_done_callback)

    def wait_all(self):
        """ Chờ tất cả task hoàn thành """
        self.state.wait()
        print("Tất cả task đã hoàn thành.")
        self.reset()

    def reset(self):
        """ Reset trạng thái để sử dụng lại """
        with self.lock:
            self.count = 0
            self.state.clear()

    def shutdown(self):
        """ Đóng executor khi không còn sử dụng """
        self.executor.shutdown(wait=True)

# --- Test TaskManager ---
def test_task(n):
  time.sleep(n)
  # print(f"Task {n} hoàn thành")
  return n
if __name__ == "__main__":
    
    tm = TaskManager(max_workers=3)

    # Submit task từ nhiều nơi khác nhau
    tm.start(test_task, 2)
    # time.sleep(0.5)
    tm.start(test_task, 3)
    # time.sleep(0.5)
    tm.start(test_task, 1)

    # Chờ tất cả hoàn thành
    # tm.wait_all()

    tm.start(test_task, 0.5)
    print("Có thể submit batch mới")
    tm.wait_all()
    print("------------------------------------")
    # Đóng khi xong
    # tm.shutdown()
