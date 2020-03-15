from abc import ABC, abstractmethod


class MazeGame(ABC):

    def __init__(self) -> None:
        self.rooms = []
        self._prepare_rooms()

    def _prepare_rooms(self) -> None:
        room1 = self.make_room()
        room2 = self.make_room()

        room1.connect(room2)
        self.rooms.append(room1)
        self.rooms.append(room2)

    def play(self) -> None:
        print('Playing using "{}"'.format(self.rooms[0]))

    @abstractmethod
    def make_room(self):
        raise NotImplementedError("You should implement this!")


class MagicMazeGame(MazeGame):
    def make_room(self):
        print('i make room')

class OrdinaryMazeGame(MazeGame):
    def make_room(self):
        pass