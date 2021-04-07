from enum import Enum, auto


class States(Enum):
    """Перечисление всех состояний бота для пользователя"""
    NONE = auto()
    ADD_COMMUNITY = auto()
    DELETE_COMMUNITY = auto()


class VkBotStatus:
    """Статический класс для хранения состояний бота для каждого пользователя"""
    _states_dict = {}

    @staticmethod
    def get_state(user_id):
        """Получение состояния бота для данного пользователя"""
        return VkBotStatus._states_dict.get(user_id, States.NONE)

    @staticmethod
    def set_state(user_id, state: States):
        """Сохранение состояния бота для данного пользователя"""
        if state == States.NONE:
            VkBotStatus._states_dict.pop(user_id, None)
        else:
            VkBotStatus._states_dict[user_id] = state
