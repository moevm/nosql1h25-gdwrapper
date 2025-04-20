from typing import Dict, Callable, List


class FormattersManager: 
    formatters: List[Callable]

    def __init__(self):
        self.formatters = []

    def register_formatter(self):
        def wrapper(func):
            self.formatters.append(func)
        return wrapper
    
    def apply_formatters(self, document):
        for formatter in self.formatters:
            formatter(document)