import functools
import logging
import time
from typing import Any, Callable


def log_method_call(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        class_name = self.__class__.__name__
        method_name = func.__name__
        logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        )

        # Start timing
        start_time = time.perf_counter()

        try:
            # Log method call
            logger.debug(
                f"{class_name}.{method_name} called with args={args}, kwargs={kwargs}",
                extra={"skip_module_func": True},
            )

            # Execute the method
            result = func(self, *args, **kwargs)

            return result

        except Exception as e:
            # Log any exceptions
            logger.error(
                f"{class_name}.{method_name} raised an exception: {e}",
                extra={"skip_module_func": True},
            )
            raise  # Re-raise the exception

        finally:
            # End timing and log execution time
            end_time = time.perf_counter()
            elapsed_time = (end_time - start_time) * 1000
            logger.debug(
                f"{class_name}.{method_name} returned {result} (Execution time: {elapsed_time:.4f} milliseconds)",
                extra={"skip_module_func": True},
            )

    return wrapper
