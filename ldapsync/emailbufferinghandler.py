import logging.handlers

from ocflib.misc import mail


class EmailBufferingHandler(logging.handlers.BufferingHandler):
    """
    Collects log messages, and sends them all at once as an 
    ocflib problem report email.
    """

    def __init__(self):
        # Initialize with a buffer capacity of 9999 messages.
        super().__init__(9999)

    def flush(self):
        mail_string = ""
        for log_record in self.buffer:
            mail_string += log_record.getMessage() + "\n"
        mail.send_problem_report(mail_string)

        super().flush()

    # Never automatically flush the buffer.
    def shouldFlush(self, record):
        return False
