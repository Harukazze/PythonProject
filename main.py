from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response
import time
import pandas as pd
from urllib.parse import unquote
from dotenv import load_dotenv
import requests
import os
import matplotlib
matplotlib.use('Agg') #Обязательно ДО pyplot
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.debug = True
load_dotenv()
app.config['DOWNLOAD_FOLDER'] = 'uploads'
app.secret_key = os.getenv("SECRET_KEY")

df = pd.read_csv("weather_data.csv", sep=",", encoding="utf-8", encoding_errors='replace')


def calculateWeatherQuality(temp, humidity, windspeed, pressure):
    weight = {
        'temp': 0.3,
        'humidity': 0.25,
        'wind': 0.2,
        'pressure': 0.25,
    }
    # print(temp, humidity, windspeed, pressure)
    if 18 <= temp <= 24:  # Оптимальная температура - от 18 до 24
        temp_score = 1
    else:
        temp_score = round(1 - min(abs(temp - 18), abs(temp - 24)) / 10, 2)
    # print(temp_score)

    if 40 <= humidity <= 60:
        humidity_score = 1
    else:
        humidity_score = round(1 - min(abs(humidity - 40), abs(humidity - 60)) / 100, 2)
    # print(humidity_score)

    if 0 <= windspeed <= 5:  # от 0 до 5 м/c
        wind_score = 1
    else:
        wind_score = round(1 - min(windspeed, abs(windspeed - 5)) / 10, 2)
    # print(wind_score)

    if 1013 <= pressure <= 1067:
        pressure_score = 1
    else:
        pressure_score = round(1 - min(abs(pressure - 1013), abs(pressure - 1067)) / 10, 2)
    # print(pressure_score)

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

    # print(df_unique)
    df_unique.to_csv('weather_data.csv', encoding='utf-8', index=False)
    sunrise_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunrise']))
    sunset_time = time.strftime("%H:%M:%S", time.localtime(weather_responce['sys']['sunset']))
    return {"description": description, "temp_now": temp_now, "temp_max": temp_max, "temp_min": temp_min,
            "temp_feels_like": temp_feels_like,
            "sunrise_time": sunrise_time, "sunset_time": sunset_time, "name": name, "windspeed": windspeed,
            "pressure": pressure, "humidity": humidity, "temp_score": calculated_weather_scores["temp_score"],
            "humidity_score": calculated_weather_scores["humidity_score"],
            "wind_score": calculated_weather_scores["wind_score"],
            "pressure_score": calculated_weather_scores["pressure_score"],
            "weather_score": calculated_weather_scores["weather_score"]}


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
    print(hourly_forecast_response.json(), hourly_forecast_response.url)
    for i in range(len(hourly_forecast_response.json()['list'])):
        labels.append(
            time.strftime("%b %d %H:%M", time.localtime(hourly_forecast_response.json()['list'][i]['dt'])))
        temp_data.append(hourly_forecast_response.json()['list'][i]['main']['temp'])
    return [labels, temp_data]


def createQualityCSV(cityName, countryCode):
    df_quality = pd.DataFrame(columns=["city", "weather_type", "count", "frequency"])
    city_rows = df[df['city'].isin([f'{cityName}']) & df['country'].isin([f'{countryCode}'])]
    value_counts = city_rows['description'].value_counts()
    all_count = sum(value_counts)
    print(dict(value_counts))
    for i in dict(value_counts):
        df_quality.loc[len(df_quality)] = [cityName, i, int(dict(value_counts)[i]),
                                           int(dict(value_counts)[i]) / all_count]
    print(df_quality)
    df_quality = df_quality.drop_duplicates()
    df_quality.to_csv(f"uploads/{cityName}_{countryCode}_Quality.csv", encoding='utf-8', index=False)
    return os.path.join(app.config['DOWNLOAD_FOLDER'], f'{cityName}_{countryCode}_Quality.csv')


def createQuantitativeCSV(cityName, countryCode):
    a = ["temp", "humidity", "pressure"]
    cols = []
    for i in a:
        cols.append(f"max_{i}")
        cols.append(f"min_{i}")
        cols.append(f"average_{i}")
        cols.append(f"dis_{i}")
        cols.append(f"stand_{i}_dev")

    df_quantitative = pd.DataFrame(
        columns=cols)

    city_rows = df[df['city'].isin([f'{cityName}']) & df['country'].isin([f'{countryCode}'])]
    all_data = []
    for i in a:
        all_data.append(city_rows[f"{i}"].max())
        all_data.append(city_rows[f"{i}"].min())
        all_data.append(city_rows[f"{i}"].mean())
        all_data.append(city_rows[f"{i}"].var())
        all_data.append(city_rows[f"{i}"].std())

    df_quantitative.loc[0] = all_data

    df_quantitative.to_csv(f"uploads/{cityName}_{countryCode}_Quantitative.csv", encoding='utf-8', index=False)

    return os.path.join(app.config['DOWNLOAD_FOLDER'], f"{cityName}_{countryCode}_Quantitative.csv")

def prepare_weather_data(cities, weather_conditions):
    import pprint
    pprint.pprint(f'Погодные условия: {weather_conditions}')

    categories = list(weather_conditions.keys())
    weather_counts = list(weather_conditions.values())

    display_names = cities[0]

    return display_names, categories, weather_counts

@app.route('/', methods=["GET", "POST"])
def index():
    arguments = dict(request.args)
    # print(arguments)
    print(dict(request.form))
    # print(request.form.getlist("CSVData"))
    if len(arguments) == 0:
        weather_data = getWeather('Токио', 'JP')
        five_day_weather = fiveDaysWeather('Токио', 'JP')
        hourly_forecast = hourleForecast('Токио', 'JP')
    else:
        weather_data = getWeather(arguments['cityName'], arguments['countryCode'])
        print(weather_data)
        five_day_weather = fiveDaysWeather(arguments['cityName'], arguments['countryCode'])
        hourly_forecast = hourleForecast(arguments['cityName'], arguments['countryCode'])
        if weather_data == 0:
            return "Ошибка в получении погодных данных для выбранного города, убедитель в правильности выбранного города"

    if len(dict(request.form)) != 0:
        if "getCityData" in dict(request.form):
            if len(arguments) == 0:
                if len(request.form.getlist("CSVData")) == 0:
                    return "Выберите столбцы, которые нужно оставить"
                else:
                    city_rows = df[df['city'].isin(['Токио']) & df['country'].isin(['JP'])]
                city_rows.to_csv('uploads/Токио_JP_data.csv', encoding='utf-8', index=False)
                file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f'Токио_JP_data.csv')

            else:
                data = dict(request.form)["getCityData"]
                city_rows = df[df['city'].isin([f'{data}']) & df['country'].isin([f'{arguments["countryCode"]}'])]
                city_rows.to_csv(f'uploads/{data}_{arguments['countryCode']}_data.csv', encoding='utf-8', index=False)
                file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], f'{data}_{arguments['countryCode']}_data.csv')

            print(file_path)
            return send_file(file_path, mimetype='text/csv', as_attachment=True)

        if "downloadQualityReport" in dict(request.form):
            if len(arguments) == 0:
                file_path = createQualityCSV("Токио", "JP")
            else:
                data = dict(request.form)["downloadQualityReport"]
                file_path = createQualityCSV(data, arguments['countryCode'])
            return send_file(file_path, mimetype='text/csv', as_attachment=True)

        elif "downloadQuantitativeReport" in dict(request.form):
            if len(arguments) == 0:
                file_path = createQuantitativeCSV("Токио", "JP")
            else:
                data = dict(request.form)["downloadQuantitativeReport"]
                file_path = createQuantitativeCSV(data, arguments['countryCode'])
            print(file_path)
            return send_file(file_path, mimetype='text/csv', as_attachment=True)
            
    # ДИАГРАММА 1
    # Данные
    categories = ['Минимальная', 'Средняя', 'Максимальная']
    values = [weather_data['temp_min'], weather_data['temp_now'], weather_data['temp_max']]  # min, avg, max

    plt.figure(figsize=(6, 6))
    bars = plt.bar(categories, values, color=['#66c2a5', '#8da0cb', '#e78ac3'], edgecolor='black')

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height + 0.3, f'{height}°C', ha='center')

    plt.title('Температура за день', fontsize=14, pad=15)
    plt.ylabel('Температура (°C)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Сохранение в буфер
    img = BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
    img.seek(0)
    plt.close()

    img_base64_1 = base64.b64encode(img.getvalue()).decode('utf-8')

    # ДИАГРАММА 2
    # Данные

    if len(arguments) == 0:
        city = 'Токио'
        c_code = 'JP'
    else:
        city = arguments['cityName']
        c_code = arguments['countryCode']

    city_rows = df[df['city'].isin([f'{city}']) & df['country'].isin([f'{c_code}'])]
    value_counts = dict(city_rows['description'].value_counts())

    display_names, categories, data_values = prepare_weather_data([weather_data['name']], value_counts)
    '''
    display_names: Города
    categories: Описания погоды
    data_values: Количество описаний погоды (string)
    '''

    data_values = [int(x) for x in data_values]

    # Визуализация (вертикальный график)
    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.arange(len(categories))  # Категории на оси X
    bar_width = 0.6

    ax.bar(x, data_values, width=bar_width, color=['#1f77b4', '#ff7f0e', '#2ca02c'])

    # Настройки
    ax.set_xlabel("Тип погоды")
    ax.set_ylabel("Количество дней")
    ax.set_title(f"Погода в {display_names[0]}")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45)
    plt.tight_layout()

    # Сохранение
    img = BytesIO()
    plt.savefig(img, format="png", dpi=100, bbox_inches="tight")
    img.seek(0)
    plt.close()

    img_base64_2 = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('weather.html',
                           city=weather_data['name'],
                           description=weather_data['description'],
                           temp_now=weather_data['temp_now'],
                           temp_max=weather_data['temp_max'],
                           temp_min=weather_data['temp_min'],
                           temp_feels_like=weather_data['temp_feels_like'],
                           sunrise_time=weather_data['sunrise_time'],
                           sunset_time=weather_data['sunset_time'],
                           windspeed=weather_data['windspeed'],
                           pressure=weather_data['pressure'],
                           humidity=weather_data['humidity'],
                           temp_score=weather_data['temp_score'],
                           humidity_score=weather_data['humidity_score'],
                           wind_score=weather_data['wind_score'],
                           pressure_score=weather_data['pressure_score'],
                           weather_score=weather_data['weather_score'],
                           five_day_weather=five_day_weather,
                           labels=hourly_forecast[0],
                           temp_data=hourly_forecast[1],
                           diagramm_url_1=img_base64_1,
                           diagramm_url_2=img_base64_2)
    
    return render_template('weather.html',
                           city=weather_data['name'],
                           description=weather_data['description'],
                           temp_now=weather_data['temp_now'],
                           temp_max=weather_data['temp_max'],
                           temp_min=weather_data['temp_min'],
                           temp_feels_like=weather_data['temp_feels_like'],
                           sunrise_time=weather_data['sunrise_time'],
                           sunset_time=weather_data['sunset_time'],
                           windspeed=weather_data['windspeed'],
                           pressure=weather_data['pressure'],
                           humidity=weather_data['humidity'],
                           temp_score=weather_data['temp_score'],
                           humidity_score=weather_data['humidity_score'],
                           wind_score=weather_data['wind_score'],
                           pressure_score=weather_data['pressure_score'],
                           weather_score=weather_data['weather_score'],
                           five_day_weather=five_day_weather,
                           labels=hourly_forecast[0],
                           temp_data=hourly_forecast[1],
                           diagramm_url=img_base64)


@app.route("/find_city", methods=["POST"])
def findCity():
    data = unquote(str(request.data).split("=")[1][:-1])
    cities_dict = {}
    if len(data) == 0:
        return "Введите название города"
    print(f"Ищем город {data}")
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
