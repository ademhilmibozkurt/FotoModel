import logging

class Log:
    def __init__(self, tab = None):
        self.tab = tab

    def desktop_log(self, message):
        self.tab.log_area.insert("end", f"{message}\n")
        self.tab.log_area.see("end")

    def db_log(self):
        logger = logging.getLogger("SimpleLogger")
        logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler("logs/app.log")
        logger.addHandler(file_handler)

        return logger
    
    def push_log_todb(self):
        pass