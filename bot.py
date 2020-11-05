import re
import random
import requests
import vk_api
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from bs4 import BeautifulSoup

import config
import answers


class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.rating = 30


class Bot:
    def __init__(self):
        self.bad_words = self._get_unprintable_words().replace('<p>', '').replace('</p>', '') + answers.BAD_WORDS
        self.vk_session: VkApi = vk_api.VkApi(token=config.VK_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk_session, config.VK_GROUP_ID)
        self.vk = self.vk_session.get_api()
        self.users = []

        # additional vars
        self.daily_news_flag = True
        self.peerSet = set()

        if not self.longpoll or not self.vk:
            self.reauth()

    def main(self):
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and \
             any(s in event.object['text'].lower() for s in config.BOT_NAMES):
                # get user that send the message
                user = self.get_user(event)
                # get user message
                message = event.object['text'].lower()
                self.update_user_list(user)
                msg = self._check_valid_words(message)

                # check if there are some bad words in user message
                if self._check_bad_words(message, user):
                    self._send_bad_answer_to_user(user, event)
                # if user message was valid, send the answer
                elif msg:
                    self.send(msg, event)
                else:
                    self.send("Не понял вопроса...", event)

    def _check_valid_words(self, message: str) -> str:
        if 'зовут' in message or 'names' in message or 'зывать' in \
                message:
            return "Привет, дружище! Можешь обращаться ко мне: " + str(config.BOT_NAMES) +\
                   ". Чтобы посмотреть список команд, набери 'Детка, список команд'"

        if 'команд' in message or 'command' in message:
            return ("Чтобы общаться со мной, ты можешь использвать следующие команды:\n\n"
                    "1. Детка, как тебя зовут? - посмотреть все способы обращения\n"
                    "2. Детка, команды? - просмотр списка команд\n"
                    "3. Детка, есть что-то новенькое на хабре? - получить последнюю статью с сайта habr.com\n"
                    "4. Детка, скинь анекдот. - самые свежие анекдоты\n"
                    "5. Детка, какая погода сегодня? - актуальный прогноз погоды в Петрозаводске\n"
                    "6. Детка, включи/выключи утренние новости - включение или отключение утренних публикаций\n"
                    "7. Детка, скинь новые мемы? - [в разработке]\n\n"
                    "Команды можно упрощать, оставляя только ключевые слова")

        if 'хабр' in message or 'habr' in message:
            return "Новый пост на Хабре: " + self.post_from_habr()

        if 'анекдот' in message:
            return "Держи свежий анекдот:\n\n" + self.new_anekdot()

        if 'погод' in message:
            return self.check_weather_forecast()

    def _send_bad_answer_to_user(self, user, event):
        u = self._get_user_object_by_id(user.get('id'))
        if u:
            msg = answers.BAD_ANSWERS[random.randint(0, 12)]
            u.rating -= 10
            self.send(msg, event, u.name)

    def _check_bad_words(self, message: str, user) -> bool:
        u = self._get_user_object_by_id(user.get('id'))

        if u and u.rating < 0:
            return True

        for word in message.split(' '):
            if word in self.bad_words:
                return True

    def update_user_list(self, user: dict):
        if not self._get_user_object_by_id(user.get('id')):
            u = User(id=user.get('id'), name=user['first_name'])
            self.users.append(u)

    def _get_user_object_by_id(self, id: int) -> User:
        for user in self.users:
            if user.id == id:
                return user

    def get_user(self, event) -> dict:
        return self.vk.users.get(user_id=event.object['from_id'])[0]

    def send(self, msg: str, event, user_name=None):
        if user_name:
            msg = msg.replace('{NAME}', user_name)

        self.vk.messages.send(random_id=random.randint(0, 999999), message=msg, peer_id=event.object['peer_id'])

    def reauth(self):
        try:
            self.vk_session = vk_api.VkApi(token=config.VK_TOKEN)
            self.longpoll = VkBotLongPoll(self.vk_session, config.VK_GROUP_ID)
            self.vk = self.vk_session.get_api()
        except Exception as e:
            pass

    def new_anekdot(self):
        r = requests.get("http://anekdotov.net/")
        r.encoding = r.apparent_encoding
        s = BeautifulSoup(r.text, 'lxml')
        anekdot = s.find("div", {'class': 'anekdot'})
        ready_anekdot = self.cleanhtml(str(anekdot))

        return ready_anekdot

    def check_weather_forecast(self):
        try:
            res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                               params={'q': config.WEATHER_CITY, 'units': 'metric', 'lang': 'ru',
                                       'APPID': config.WEATHER_API_KEY})
            data = res.json()
            res_list = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                                    params={'q': config.WEATHER_CITY, 'units': 'metric', 'lang': 'ru',
                                            'APPID': config.WEATHER_API_KEY})
            data_list = res_list.json()
            short_list = "\n\nКраткая сводка погоды на ближайшие дни: \n"
            pred = ""

            for i in data_list['list']:
                if pred != str(i['dt_txt'])[0:10] and str(i['dt_txt'])[11:13] == '12':
                    short_list += i['dt_txt'] + '{0:+3.0f}'.format(i['main']['temp']) + "°C. " + i['weather'][0][
                        'description'] + "\n"
                    pred = str(i['dt_txt'])[0:10]

            return ("Погода в петрозаводске сегодня:\n\n" +
                    "Текущая температура: " + str(data['main']['temp']) + "°C. \n" +
                    "Минимальная температура: " + str(data['main']['temp_min'] - 1) + "°C. \n" +
                    "Максимальная температура: " + str(data['main']['temp_max'] + 1) + "°C. \n" +
                    "Ветер: " + str(data['wind']['speed']) + " м/сек. \n" +
                    "Описание: " + str(data['weather'][0]['description']) + short_list)

        except Exception as e:
            print("Exception (weather):", e)
            pass

    @staticmethod
    def post_from_habr():
        resp = requests.get("https://habr.com/ru/all/")  # Получаем посты Habr
        soup = BeautifulSoup(resp.text, 'lxml')  # Преобразовываем получнееый результат в lxml (html)
        link = soup.find("h2").find('a').get('href')  # Выбираем первую статью из списка статей
        return link

    @staticmethod
    def _get_unprintable_words() -> str:
        """ Get words that we should shame"""
        resp = requests.get("https://www.myadept.ru/index.php/page/spisok-necenzurnyh-slov-dlja-anti-spama-i-cenzury")
        soup = BeautifulSoup(resp.text, 'lxml')
        return str(soup.find("div", {"class": "spoiler_div"}))

    @staticmethod
    def cleanhtml(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext


a = Bot()


if __name__ == '__main__':
    bot = Bot()

    while True:
        bot.main()
        bot.reauth()
