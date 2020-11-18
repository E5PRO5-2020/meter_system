import logging
import logging.handlers

def get_logger():
    """
    Function for setting up logging to syslog file.
    Ignoring less severe messages than INFO.
    Returns a reference to a logger instance.
    """
    # Create logger with specific name
    log = logging.getLogger('TEAM 3: ')
    
    # Check if handlers are already present and if so, clear them
    if (log.hasHandlers()):
        log.handlers.clear()

    # Setting logger level 
    log.setLevel(logging.INFO)
    
    # Create handler addressed to syslog
    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    
    # Create and add formatter to handler
    formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to logger
    log.addHandler(handler)

    return log


