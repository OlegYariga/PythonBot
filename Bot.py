import re
import random
import requests
import vk_api
from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType, VkBotMessageEvent, VkBotEvent
from bs4 import BeautifulSoup

my_names = ['детка', 'baby', 'умник', 'clever boy', 'ублюдок']
answers = ['Что опять?!',
           'Как же вы меня все достали...',
           'А сами погуглить не можете?',
           ', сколько можно задавать тупые вопросы?!'
           'Я устала',
           ', держи: www.google.ru',
           'Какого хрена?',
           'Now you have really pissed me off',
           'Go to blazes!',
           'Мне надоела эта работа',
           ', я не буду отвечать на такие сообщения',
           ', тебе сложно общаться по-нормальному?',
           'Я не буду отвечать на такие вопрсоы',
           'Делайте это сами',
           ', я выполняю только те команды, которые описаны в мануале. Остальное делайте сами',
           ]
daily_news_flag = True
peerSet = set()

groupID = 188911054  # Здесь ввести ID сообщества
token = 'ae8985a2422e64d29b4329ab268cc9aa1e9a1753181fe7b34f3008f04e09c5b2d24e1a464852f0ac1713d'  # Здесь ввести token сообщества (не удаляя апострофы)
# weather settings
weather_api_key = '3231530f6b58e5ee4cde4ae6f4770ce4'
s_city = "Petrozavodsk,RU"



vk_session: VkApi = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, groupID)
vk = vk_session.get_api()


def reauth():
    try:
        global vk, longpoll, vk_session
        vk_session = vk_api.VkApi(token=token)
        longpoll = VkBotLongPoll(vk_session, groupID)
        vk = vk_session.get_api()
    except Exception as e:
        pass


def post_from_habr():
    resp = requests.get("https://habr.com/ru/all/")  # Получаем посты Habr
    soup = BeautifulSoup(resp.text, 'lxml')  # Преобразовываем получнееый результат в lxml (html)
    link = soup.find("h2").find('a').get('href')  # Выбираем первую статью из списка статей
    return link


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def new_anekdot():
    r = requests.get("http://anekdotov.net/")  # Получаем анекдот
    r.encoding = r.apparent_encoding
    s = BeautifulSoup(r.text, 'lxml')  # Преобразовываем получнееый результат в lxml (html)
    anekdot = s.find("div", {'align': 'justify'})
    ready_anekdot = cleanhtml(str(anekdot))
    return ready_anekdot


def check_weather_forecast():

    try:
        res = requests.get("http://api.openweathermap.org/data/2.5/weather",
                           params={'q': s_city, 'units': 'metric', 'lang': 'ru', 'APPID': weather_api_key})
        data = res.json()
        res_list = requests.get("http://api.openweathermap.org/data/2.5/forecast",
                           params={'q': s_city, 'units': 'metric', 'lang': 'ru', 'APPID': weather_api_key})
        data_list = res_list.json()
        short_list = "\n\nКраткая сводка погоды на ближайшие дни: \n"
        pred = ""
        for i in data_list['list']:
            if pred != str(i['dt_txt'])[0:10] and str(i['dt_txt'])[11:13] == '12':
                short_list += i['dt_txt']+ '{0:+3.0f}'.format(i['main']['temp'])+"°C. "+i['weather'][0]['description'] + "\n"
                pred = str(i['dt_txt'])[0:10]
        return ("Погода в петрозаводске сегодня:\n\n"+\
               "Текущая температура: "+ str(data['main']['temp']) + "°C. \n"+\
               "Минимальная температура: "+ str(data['main']['temp_min']-1) + "°C. \n" + \
               "Максимальная температура: "+ str(data['main']['temp_max']+1) + "°C. \n" + \
               "Ветер: " + str(data['wind']['speed']) + " м/сек. \n" + \
               "Описание: " + str(data['weather'][0]['description'])+short_list)

    except Exception as e:
        print("Exception (weather):", e)
        pass


def send(msg):  # msg — сообщение
    vk.messages.send(random_id=random.randint(0, 999999), message=msg, peer_id=peerID)


def main():
    try:
        global peerID, peerSet
        for event in longpoll.listen():
            print(peerSet)
            if event.type == VkBotEventType.MESSAGE_NEW:
                print(event.object)
                if any(s in event.object['text'].lower() for s in my_names):
                    peerSet.add(event.object['peer_id'])
                    if 'зовут' in event.object['text'].lower() or 'names' in event.object['text'].lower() or 'зывать' in event.object['text'].lower():
                        peerID = event.object['peer_id']
                        send("Привет, дружище! Можешь обращаться ко мне: " + str(my_names)+
                             ". Чтобы посмотреть список команд, набери 'Детка, список команд'")
                        continue
                    if 'команд' in event.object['text'].lower() or 'command' in event.object['text'].lower():
                        peerID = event.object['peer_id']
                        send("Чтобы общаться со мной, ты можешь использвать следующие команды:\n\n"
                             "1. Детка, как тебя зовут? - посмотреть все способы обращения\n"
                             "2. Детка, команды? - просмотр списка команд\n"
                             "3. Детка, есть что-то новенькое на хабре? - получить последнюю статью с сайта habr.com\n"
                             "4. Детка, скинь анекдот. - самые свежие анекдоты\n"
                             "5. Детка, какая погода сегодня? - актуальный прогноз погоды в Петрозаводске\n"
                             "6. Детка, включи/выключи утренние новости - включение или отключение утренних публикаций\n"
                             "7. Детка, скинь новые мемы? - [в разработке]\n\n"
                             "Команды можно упрощать, оставляя только ключевые слова")
                        continue
                    if 'хабр' in event.object['text'].lower() or 'habr' in event.object['text'].lower():
                        peerID = event.object['peer_id']
                        send("Новый пост на Хабре: "+post_from_habr())
                        continue
                    if 'анекдот' in event.object['text'].lower():
                        peerID = event.object['peer_id']
                        send("Держи свежий анекдот:\n\n"+new_anekdot())
                        continue
                    if 'погод' in event.object['text'].lower():
                        peerID = event.object['peer_id']
                        send(check_weather_forecast())
                        continue
                    choise = random.randint(0, 14)
                    user = event.object['from_id']
                    answer = answers[choise]
                    if answer[0] == ',':
                        peerID = event.object['peer_id']
                        send(str(vk.users.get(user_id=user)[0]['first_name'])+answer)
                        continue
                    peerID = event.object['peer_id']
                    send(answer)
    except Exception as e:
        pass


if __name__ == '__main__':
    print("Запустился")
    print(check_weather_forecast())
    while True:
        main()
        reauth()
    print("hahaha")
