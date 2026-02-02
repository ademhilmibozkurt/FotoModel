import os
import logging

root = logging.getLogger()
for h in root.handlers[:]:
    root.removeHandler(h)

class Log:
    _logger = None

    @classmethod
    def db_log(cls):
        if cls._logger:
            return cls._logger

        os.makedirs("logs", exist_ok=True)

        logger = logging.getLogger("AppLogger")
        logger.setLevel(logging.INFO)

        logger.handlers.clear()
        logger.propagate = False

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

        file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        cls._logger = logger
        return logger

    
    def push_log_todb():
        pass