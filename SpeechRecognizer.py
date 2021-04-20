from io import BytesIO
from subprocess import Popen, PIPE

from requests import get as req_get
import speech_recognition as sr


class SpeechRecognizer:
    """Класс SpeechRecognizer используется для обработки голосовых сообщений."""

    @staticmethod
    def get_phrase(url) -> str:
        """Преобразует голосовое сообщение пользователя в строку

        Parameters
        ----------
        url : str
            ссылка на голосовое сообщение пользователя
        Return
        ----------
        user_message: str
            преобразованная строка
        """
        # using pipe:0 refers to the stdin, pipe:1 refers to stdout
        ffmpeg_process = Popen('ffmpeg -v fatal -hide_banner -i pipe:0 -f wav pipe:1',
                               shell=True, stdin=PIPE, stdout=PIPE)

        output_stream = ffmpeg_process.communicate(req_get(url).content)

        output_file = BytesIO(output_stream[0])
        output_file.seek(0)

        req = sr.Recognizer()
        harvard = sr.AudioFile(output_file)
        with harvard as source:
            audio = req.record(source)
        try:
            user_message = req.recognize_google(audio, language="ru-RU")
            return user_message
        except sr.UnknownValueError:
            return 'непонятное сообщение'
