# Памятка по установке проекта

Данный проект предназначен для получения погодных данных в режиме реального времени

# Зависимости

Для корректной работы требуется использовать Python 3.10 и выше

# Установка программы

1. Склонировать репозиторий (или скачать его и распаковать в нужной папке)
2. Создать виртуальное окружение `python -m venv venv`
3. Активировать виртуальное окружение
   1. Для Windows `venv/Scripts/activate`
   2. Для MacOS/Linux `source venv/bin/activate`
4. Установить необходимые зависимости командой `pip install -r requirements.txt`
5. Создать **.env** файл по следующему шаблону
````
SECRET_KEY = "Секретный ключ"
API_KEY = "YOUR_API_KEY"
````
   
[Получение API-ключа](https://openweathermap.org/api)
