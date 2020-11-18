import logging
import logging.handlers

def log_error(message) -> None:
    """
    Function for sending logging message to syslog file.
    Use this one for error messages.
    """
    # Create logger with specific name
    logger = logging.getLogger('Test_logging: ')

    # Setting logger level 
    logger.setLevel(logging.INFO)
    
    # Create handler addressed to syslog
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    
    # Create and add formatter to handler
    formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)

    # Log message
    logger.error(message)

    # Remove the handle after logging
    logger.removeHandler(handler)
    

def log_info(message) -> None:
    """
    Function for sending logging message to syslog file.
    Use this one for info messages.
    """
    # Create logger with specific name
    logger = logging.getLogger('Test_logging: ')

    # Setting logger level 
    logger.setLevel(logging.INFO)
    
    # Create handler addressed to syslog
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    
    # Create and add formatter to handler
    formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)

    # Log message
    logger.info(message)

    # Remove the handle after logging
    logger.removeHandler(handler)

