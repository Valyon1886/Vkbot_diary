from enum import Enum, auto


class States(Enum):
    NONE = auto()
    ADD_COMMUNITY = auto()
    DELETE_COMMUNITY = auto()


class VkBotStatus:
    _state = None

    @staticmethod
    def get_state():
        if VkBotStatus._state is None:
            VkBotStatus._state = States.NONE
        return VkBotStatus._state

    @staticmethod
    def set_state(state: States):
        VkBotStatus._state = state
