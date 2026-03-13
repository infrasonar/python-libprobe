import colorlog
import logging
import logging.handlers
import os


_IS_DEBUG = os.getenv('LOG_LEVEL', '').upper() == 'DEBUG'
_MAP_LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def setup_logger(name: str = 'root', loggers: tuple[str, ...] = tuple()):
    """Setup logger."""

    _LOG_LEVEL = os.getenv('LOG_LEVEL', 'warning')
    _LOG_COLORIZED = int(os.getenv('LOG_COLORIZED', '0'))
    _LOG_DATE_FMT = os.getenv('LOG_FMT', '%y%m%d %H:%M:%S')

    incl_name = '%(name)s:' if loggers else ''

    if _LOG_COLORIZED:
        # setup colorized formatter
        formatter = colorlog.ColoredFormatter(
            fmt=(
                '%(log_color)s[%(levelname)1.1s %(asctime)s '
                f'{incl_name}%(module)s:%(lineno)d]%(reset)s %(message)s'),
            datefmt=_LOG_DATE_FMT,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white'},
            secondary_log_colors={},
            style='%')
    else:
        # setup formatter without using colors
        formatter = logging.Formatter(
            fmt=(
                '[%(levelname)1.1s %(asctime)s '
                f'{incl_name}%(module)s:%(lineno)d] %(message)s'),
            datefmt=_LOG_DATE_FMT,
            style='%')

    log_level = _MAP_LOG_LEVELS[_LOG_LEVEL.upper()]
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.name = name
    ch = logging.StreamHandler()

    # we can set the handler level to DEBUG since we control the root level
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    for name in loggers:
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        if not logger.hasHandlers():
            logger.addHandler(ch)


def exception(msg: str = ''):
    """Log exception only when debug logging is enabled."""
    if _IS_DEBUG:
        logging.exception(msg)
