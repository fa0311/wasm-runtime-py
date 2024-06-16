import logging


class NestedLogger:
    """ネストされたログを出力するためのクラス"""

    def __init__(self, logging: logging.Logger):
        self.logging = logging
        self.nested = -1

    def logger(self: "NestedLogger", func):
        """関数をラップしてログを出力するデコレータ"""

        def wrapper(*args, **kwargs):
            self.nested += 1
            if self.nested == 0:
                self.logging.debug(f"┏━[ {func.__name__} ]")
            else:
                self.logging.debug(f"{'┃' * (self.nested - 1)}┣┳[ {func.__name__} ]")

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                self.logging.error(f"{'┃' * self.nested}┣━[ {func.__name__} ]")
                self.logging.error(f"{'┃' * self.nested}┗━[ Error ] {e}")
                self.nested -= 1
                raise e

            if self.nested == 0:
                self.logging.debug(f"┗━[ {func.__name__} ]")
            else:
                self.logging.debug(f"{'┃' * self.nested}┗━[ {func.__name__} ]")
            self.nested -= 1
            return result

        return wrapper

    def message(self, msg):
        """ログメッセージを整形して返す"""
        return f"{'┃' * self.nested}┣━ {msg}"

    def debug(self, msg, *args, **kwargs):
        """デバッグログを出力する"""
        self.logging.debug(self.message(msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """情報ログを出力する"""
        self.logging.info(self.message(msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """警告ログを出力する"""
        self.logging.warning(self.message(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """エラーログを出力する"""
        self.logging.error(self.message(msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """致命的なエラーログを出力する"""
        self.logging.critical(self.message(msg), *args, **kwargs)
