from requests import get as req_get
import speech_recognition as sr
from io import BytesIO
from subprocess import Popen, PIPE


class SpeechRecognizer:
    """Класс SpeechRecognizer используется для обработки голосовых сообщений."""

    @staticmethod
    def get_phrase(url):
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

        arr = BytesIO(req_get(url).content)
        arr.seek(0)

        input_track_data = bytearray(arr.read())

        # using pipe:0 refers to the stdin, pipe:1 refers to stdout
        ffmpeg_process = Popen('ffmpeg -v fatal -hide_banner -i pipe:0 -f wav pipe:1', stdin=PIPE, stdout=PIPE)

        output_stream = ffmpeg_process.communicate(input_track_data)

        arr = BytesIO(output_stream[0])
        arr.seek(0)

        r = sr.Recognizer()
        harvard = sr.AudioFile(arr)
        with harvard as source:
            audio = r.record(source)
        try:
            user_message = r.recognize_google(audio, language="ru-RU")
            return user_message
        except sr.UnknownValueError:
            return 'пустое сообщение'
