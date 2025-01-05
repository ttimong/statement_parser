from abc import ABC, abstractmethod


class AbstractParser(ABC):
    @abstractmethod
    def extract_data(self):
        """Abstract method to extract data from source"""
        pass
