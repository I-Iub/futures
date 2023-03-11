import logging


def configure_logger():
    message_format = ('%(asctime)s - %(levelname)s - %(module)s:%(lineno)s - '
                      '%(message)s')
    logging.basicConfig(format=message_format,
                        level=logging.INFO)
