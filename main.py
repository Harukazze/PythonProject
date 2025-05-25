from flask import Flask, render_template, request, jsonify
import time
import pandas as pd
import numpy as np
from urllib.parse import unquote
from dotenv import load_dotenv
import requests
import os

app = Flask(__name__)
app.debug = True
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

df = pd.read_csv("weather_data.csv", sep=",")
print(df)


def calculateWeatherQuality(temp, humidity, windspeed, pressure):
    weight = {
        'temp': 0.3,
        'humidity': 0.25,
        'wind': 0.2,
        'pressure': 0.25,
    }
    #print(temp, humidity, windspeed, pressure)
    if 18 <= temp <= 24:  # Оптимальная температура - от 18 до 24
        temp_score = 1
    else:
        temp_score = 1 - min(abs(temp - 18), abs(temp - 24)) / 10
    #print(temp_score)

    if 40 <= humidity <= 60:
        humidity_score = 1
    else:
        humidity_score = 1 - min(abs(humidity - 40), abs(humidity - 60)) / 100
    #print(humidity_score)

    if 0 <= windspeed <= 5:  # от 0 до 5 м/c
        wind_score = 1
    else:
        wind_score = 1 - min(windspeed, abs(windspeed - 5)) / 10
    #print(wind_score)

    if 1013 <= pressure <= 1067:
        pressure_score = 1
    else:
        pressure_score = 1 - min(abs(pressure - 1013), abs(pressure - 1067)) / 10
    #print(pressure_score)

    weather_score = (temp_score * weight['temp'] + humidity_score * weight['humidity'] + wind_score * weight[
        'wind'] + pressure_score * weight['pressure']) * 10

    return {'temp_score': temp_score, 'humidity_score': humidity_score, 'wind_score': wind_score,
            'pressure_score': pressure_score, 'weather_score': round(weather_score, 2)}


def getWeather(cityName, countryCode):
    weather_responce = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lang=ru&q={cityName},{countryCode}&appid={os.getenv('API_KEY')}&units=metric").json()
    if 'message' in weather_responce:
        return 0
    print(weather_responce)
    name = weather_responce['name']
    date = time.strftime("%c", time.localtime(weather_responce['dt']))
    country = weather_responce['sys']['country']
    description = weather_responce['weather'][0]['description'].capitalize()
    temp_now = weather_responce['main']['temp']
    temp_max = weather_responce['main']['temp_max']
    temp_min = weather_responce['main']['temp_min']
    temp_feels_like = weather_responce['main']['feels_like']
    windspeed = weather_responce['wind']['speed']
    pressure = weather_responce['main']['pressure']
    humidity = weather_responce['main']['humidity']
    calculated_weather_scores = calculateWeatherQuality(temp_now, humidity, windspeed, pressure)
    df.loc[len(df)] = [date, name, country, temp_now, temp_feels_like, humidity, windspeed,
                       pressure, description, calculated_weather_scores['temp_score'],
                       calculated_weather_scores['humidity_score'], calculated_weather_scores['wind_score'],
                       calculated_weather_scores['pressure_score'], calculated_weather_scores['weather_score']]
    df_unique = df.drop_duplicates(
        subset=['date', 'city', 'country', 'temp', 'feels_like', 'humidity', 'windspeed', 'pressure', 'description'])

    print(df_unique)
    df_unique.to_csv('weather_data.csv', encoding='utf-8', index=False)
    sunrise_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunrise']))
    sunset_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunset']))
    return [description, temp_now, temp_max, temp_min, temp_feels_like, sunrise_time, sunset_time, name, windspeed,
            pressure, humidity]


def weatherDataTransform(data):
    updatedData = {}
    for i in data:
        min_temp = 999999999
        max_temp = -100000000
        feels_like = 0
        pressure = 0
        humidity = 0
        wind_speed = 0

        morning_temp = 0
        day_temp = 0
        evening_temp = 0
        night_temp = 0

        morning_feels_temp = 0
        day_feels_temp = 0
        evening_feels_temp = 0
        night_feels_temp = 0
        for j in range(len(data[i])):
            forecast_time = time.strftime("%H", time.localtime(data[i][j]['dt']))
            if forecast_time in ["00", "03"]:
                night_temp += data[i][j]['main']['temp']
                night_feels_temp += data[i][j]['main']['feels_like']

            if forecast_time in ["06", "09"]:
                morning_temp += data[i][j]['main']['temp']
                morning_feels_temp += data[i][j]['main']['feels_like']

            if forecast_time in ["12", "15"]:
                day_temp += data[i][j]['main']['temp']
                day_feels_temp += data[i][j]['main']['feels_like']

            if forecast_time in ["18", "21"]:
                evening_temp += data[i][j]['main']['temp']
                evening_feels_temp += data[i][j]['main']['feels_like']

            min_temp = min(min_temp, data[i][j]['main']['temp_min'])
            max_temp = max(max_temp, data[i][j]['main']['temp_max'])
            feels_like += data[i][j]['main']['feels_like']
            pressure += data[i][j]['main']['pressure']
            humidity += data[i][j]['main']['humidity']
            wind_speed += data[i][j]['wind']['speed']
        feels_like = round(feels_like / len(data[i]), 2)

        pressure = round(pressure / len(data[i]), 2)
        humidity = round(humidity / len(data[i]), 2)
        wind_speed = round(wind_speed / len(data[i]), 2)

        night_temp = round(night_temp / 2, 2)
        morning_temp = round(morning_temp / 2, 2)
        day_temp = round(day_temp / 2, 2)
        evening_temp = round(evening_temp / 2, 2)

        night_feels_temp = round(night_feels_temp / 2, 2)
        morning_feels_temp = round(morning_feels_temp / 2, 2)
        day_feels_temp = round(day_feels_temp / 2, 2)
        evening_feels_temp = round(evening_feels_temp / 2, 2)

        updatedData[i] = {"MinTemp": min_temp, "MaxTemp": max_temp, "AvgFeelsLike": feels_like, "AvgPressure": pressure,
                          "AvgHumidity": humidity, "description": data[i][0]['weather'][0]['description'],
                          "WindSpeed": wind_speed, "NightTemp": night_temp, "MorningTemp": morning_temp,
                          "DayTemp": day_temp, "EveningTemp": evening_temp, "NightFeelsTemp": night_feels_temp,
                          "MorningFeelsTemp": morning_feels_temp, "DayFeelsTemp": day_feels_temp,
                          "EveningFeelsTemp": evening_feels_temp}
    return updatedData


def fiveDaysWeather(cityName, countryCode):
    weather_responce = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast?lang=ru&q={cityName},{countryCode}&appid={os.getenv('API_KEY')}&units=metric").json()
    if weather_responce['message'] != 0:
        return 0
    five_day_weather = {}
    for i in weather_responce['list']:
        if time.strftime("%a, %b %d", time.localtime(i['dt'])) != time.strftime("%a, %b %d", time.gmtime()):
            if time.strftime("%a, %b %d", time.localtime(i['dt'])) not in five_day_weather:
                five_day_weather[time.strftime("%a, %b %d", time.localtime(i['dt']))] = [i]
            else:
                five_day_weather[time.strftime("%a, %b %d", time.localtime(i['dt']))].append(i)
    five_day_weather = weatherDataTransform(five_day_weather)
    return five_day_weather


def hourleForecast(cityName, countryCode):
    labels = []
    temp_data = []
    hourly_forecast_response = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast/?lang=ru&q={cityName},{countryCode}&appid={os.getenv('API_KEY')}&units=metric&cnt=9")
    for i in range(len(hourly_forecast_response.json()['list'])):
        labels.append(
            time.strftime("%b %d %H:%M", time.localtime(hourly_forecast_response.json()['list'][i]['dt'])))
        temp_data.append(hourly_forecast_response.json()['list'][i]['main']['temp'])
    return [labels, temp_data]


@app.route('/')
def index():
    arguments = dict(request.args)
    if len(arguments) == 0:
        weather_data = getWeather('Токио', 'JP')
        five_day_weather = fiveDaysWeather('Токио', 'JP')
        hourly_forecast = hourleForecast('Токио', 'JP')
    else:
        weather_data = getWeather(arguments['cityName'], arguments['countryCode'])
        five_day_weather = fiveDaysWeather(arguments['cityName'], arguments['countryCode'])
        hourly_forecast = hourleForecast(arguments['cityName'], arguments['countryCode'])
        if weather_data == 0:
            return "Ошибка в получении погодных данных для выбранного города, убедитель в правильности выбранного города"
    return render_template('weather.html',
                           city=weather_data[-4],
                           description=weather_data[0],
                           temp_now=weather_data[1],
                           temp_max=weather_data[2],
                           temp_min=weather_data[3],
                           temp_feels_like=weather_data[4],
                           sunrise_time=weather_data[5],
                           sunset_time=weather_data[6],
                           windspeed=weather_data[-3],
                           pressure=weather_data[-2],
                           humidity=weather_data[-1],
                           five_day_weather=five_day_weather,
                           labels=hourly_forecast[0],
                           temp_data=hourly_forecast[1])


@app.route("/find_city", methods=["POST"])
def findCity():
    data = unquote(str(request.data).split("=")[1][:-1])
    cities_dict = {}
    if len(data) == 0:
        return "Введите название города"

    responce = requests.get(
        f"http://api.openweathermap.org/geo/1.0/direct?lang=ru&q={data}&limit=4&appid={os.getenv('API_KEY')}").json()

    for i in responce:
        if 'local_names' in i:
            if 'ru' in i['local_names']:
                cities_dict[f"{i['local_names']['ru']}-{i['country']}"] = {'cityName': i['name'],
                                                                           'countryCode': i['country']}

    return jsonify(cities_dict)


if "__main__" == __name__:
    app.run()

# lat 139.7595 lon 35.6828
