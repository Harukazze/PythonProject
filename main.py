from flask import Flask, render_template, request, jsonify
import time
from urllib.parse import unquote
from dotenv import load_dotenv
import requests
import os

app = Flask(__name__)
app.debug = True
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")


def getWeather(cityName, countryCode):
    weather_responce = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lang=ru&q={cityName},{countryCode}&appid={os.getenv('API_KEY')}&units=metric").json()
    if 'message' in weather_responce:
        return 0
    name = weather_responce['name']
    description = weather_responce['weather'][0]['description']
    temp_now = weather_responce['main']['temp']
    temp_max = weather_responce['main']['temp_max']
    temp_min = weather_responce['main']['temp_min']
    temp_feels_like = weather_responce['main']['feels_like']
    sunrise_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunrise']))
    sunset_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunset']))
    return [description, temp_now, temp_max, temp_min, temp_feels_like, sunrise_time, sunset_time, name]


def weatherDataTransform(data):
    updatedData = {}
    min_temp = 999999999
    max_temp = -100000000
    feels_like = 0
    pressure = 0
    humidity = 0
    print(data)
    for i in data:
        for j in range(len(data[i])):
            min_temp = min(min_temp, data[i][j]['main']['temp_min'])
            max_temp = max(max_temp, data[i][j]['main']['temp_max'])
            feels_like += data[i][j]['main']['feels_like']
            pressure += data[i][j]['main']['pressure']
            humidity += data[i][j]['main']['humidity']
        feels_like = round(feels_like / len(data[i]), 2)
        pressure = round(pressure / len(data[i]), 2)
        humidity = round(humidity / len(data[i]), 2)
        updatedData[i] = {"MinTemp": min_temp, "MaxTemp": max_temp, "AvgFeelsLike": feels_like, "AvgPressure": pressure,
                          "AvgHumidity": humidity, "description": data[i][0]['weather'][0]['description']}
    return updatedData


def fiveDaysWeather(cityName, countryCode):
    weather_responce = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lang=ru&q={cityName},{countryCode}&appid={os.getenv('API_KEY')}&units=metric").json()
    if weather_responce['message'] != 0:
        return 0
    five_day_weather = {}
    for i in weather_responce['list']:
        if time.strftime("%d.%m.%Y", time.localtime(i['dt'])) not in five_day_weather:
            five_day_weather[time.strftime("%d.%m.%Y", time.localtime(i['dt']))] = [i]
        else:
            five_day_weather[time.strftime("%d.%m.%Y", time.localtime(i['dt']))].append(i)
    five_day_weather = weatherDataTransform(five_day_weather)
    return five_day_weather


@app.route('/')
def index():
    arguments = dict(request.args)
    print(arguments)
    if len(arguments) == 0:
        weather_data = getWeather('Токио', 'JP')
        five_day_weather = fiveDaysWeather('Токио', 'JP')
    else:
        # response = requests.get(
        #     f"http://api.openweathermap.org/geo/1.0/direct?lang=ru&q={arguments['cityName']},{arguments['countryCode']}&limit=1&appid={os.getenv("API_KEY")}").json()
        weather_data = getWeather(arguments['cityName'], arguments['countryCode'])
        five_day_weather = fiveDaysWeather(arguments['cityName'], arguments['countryCode'])
        print(five_day_weather)
        if weather_data == 0:
            return "Ошибка в получении погодных данных для выбранного города, убедитель в правильности выбранного города"
    return render_template('weather.html',
                           city=weather_data[-1],
                           description=weather_data[0],
                           temp_now=weather_data[1],
                           temp_max=weather_data[2],
                           temp_min=weather_data[3],
                           temp_feels_like=weather_data[4],
                           sunrise_time=weather_data[5],
                           sunset_time=weather_data[6],
                           five_day_weather=five_day_weather)


@app.route("/find_city", methods=["POST"])
def findCity():
    data = unquote(str(request.data).split("=")[1][:-1])
    print(data)
    cities_dict = {}
    if len(data) == 0:
        return "Введите название города"

    responce = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?lang=ru&q={data}&limit=4&appid={os.getenv('API_KEY')}").json()

    for i in responce:
        if 'local_names' in i:
            if 'ru' in i['local_names']:
                print(i)
                cities_dict[f"{i['local_names']['ru']}-{i['country']}"] = {'cityName': i['name'],
                                                                           'countryCode': i['country']}

    return jsonify(cities_dict)


if "__main__" == __name__:
    app.run()

# lat 139.7595 lon 35.6828
