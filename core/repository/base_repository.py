from abc import ABC, abstractmethod


class BaseRepository(ABC):

    @staticmethod
    @abstractmethod
    def save(save_object):
        pass

    @staticmethod
    @abstractmethod
    def get_all():
        pass
