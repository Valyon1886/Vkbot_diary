from enum import Enum, auto


class States(Enum):
    """Перечисление всех состояний бота для пользователя"""
    NONE = auto()
    ADD_COMMUNITY = auto()
    DELETE_COMMUNITY = auto()
    ADD_TASK_INIT = auto()
    ADD_TASK_HAS_DATE = auto()
    DELETE_TASK_INIT = auto()
    DELETE_TASK_HAS_DATE = auto()
    CHANGE_TASK_INIT = auto()
    CHANGE_TASK_HAS_DATE = auto()
    CHANGE_TASK_ENTER_DATA = auto()


class VkBotStatus:
    """Статический класс для хранения состояний бота для каждого пользователя"""
    _states_dict = {}

    @staticmethod
    def get_state(user_id):
        """Получение состояния бота для данного пользователя"""
        return VkBotStatus._states_dict.get(user_id, States.NONE) \
            if isinstance(VkBotStatus._states_dict.get(user_id, States.NONE), States) \
            else VkBotStatus._states_dict.get(user_id, States.NONE)[0]

    @staticmethod
    def get_data(user_id):
        """Получение данных у состояния бота для данного пользователя"""
        try:
            if not isinstance(VkBotStatus._states_dict.get(user_id, [])[-1], States):
                return VkBotStatus._states_dict.get(user_id, States.NONE)[-1]
        except IndexError:
            pass
        return None

    @staticmethod
    def set_state(user_id, state: States, task_data=None):
        """Сохранение состояния бота для данного пользователя"""
        if state == States.NONE:
            VkBotStatus._states_dict.pop(user_id, None)
        else:
            if task_data is None:
                VkBotStatus._states_dict[user_id] = [state]
            else:
                VkBotStatus._states_dict[user_id] = [state, task_data]
