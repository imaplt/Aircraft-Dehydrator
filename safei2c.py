import busio
import board
import threading
import time
import logging

logger = logging.getLogger(__name__)

class SafeI2C(busio.I2C):
    def __init__(self, scl=board.SCL, sda=board.SDA, retries=3, delay=0.1):
        super().__init__(scl, sda)
        self._lock = threading.Lock()
        self._retries = retries
        self._delay = delay

    def _with_retry(self, func, *args, **kwargs):
        for attempt in range(self._retries):
            try:
                with self._lock:
                    return func(*args, **kwargs)
            except OSError as e:
                if attempt < self._retries - 1:
                    logger.warning(
                        f"I2C error {e} on {func.__name__}, retry {attempt+1}/{self._retries}"
                    )
                    time.sleep(self._delay)
                else:
                    logger.error(f"I2C failed after {self._retries} retries: {e}")
                    raise e

    def writeto(self, *args, **kwargs):
        return self._with_retry(super().writeto, *args, **kwargs)

    def readfrom_into(self, *args, **kwargs):
        return self._with_retry(super().readfrom_into, *args, **kwargs)

    def writeto_then_readfrom(self, *args, **kwargs):
        return self._with_retry(super().writeto_then_readfrom, *args, **kwargs)
