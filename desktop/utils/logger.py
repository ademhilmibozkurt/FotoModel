import logging

class Log:
    def __init__(self, tab = None):
        self.tab = tab

        self.logger = self.create_logger()

    def desktop_log(self, message):
        self.tab.log_area.insert("end", f"{message}\n")
        self.tab.log_area.see("end")

    def create_logger(self):
        logger = logging.getLogger("DbLogger")
        logger.setLevel(logging.INFO)
        logger.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
        
        file_handler = logging.FileHandler("logs/app.log")
        logger.addHandler(file_handler)

        return logger

    def db_log(self):
        return self.logger
    
    def push_log_todb(self):
        pass