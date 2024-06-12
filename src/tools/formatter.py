import logging


class ColorFormatter(logging.Formatter):
    """ログメッセージに色を付けるフォーマッタ"""

    COLORS = {
        logging.DEBUG: "\033[90m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"
    GREY = "\033[90m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, "\033[0m")
        output = ""
        for char in record.getMessage():
            codepoint = ord(char)
            if 0x2500 <= codepoint <= 0x257F:
                output += f"{self.GREY}{char}{color}"
            else:
                output += char
        prefix = f"[{record.levelname}]"
        return f"{color}{prefix:8} {output}{self.RESET}"
