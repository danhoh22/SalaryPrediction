import os

import requests
import pandas as pd

# Функция для получения номеров областей из запроса к API HeadHunter
def get_area_ids():
    url = "https://api.hh.ru/areas"
    response = requests.get(url)
    if response.status_code == 200:
        areas = response.json()
        russian_areas = [area for area in areas if area['name'] == 'Россия'][0]['areas']
        area_ids = [area['id'] for area in russian_areas]
        return area_ids
    else:
        print("Ошибка при получении данных об областях")
        return []

# Функция для получения данных о вакансиях из определенной области
def get_vacancies_from_area(area_id):
    url = "https://api.hh.ru/vacancies"
    params = {'area': area_id, 'per_page': 100}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['items']
    else:
        print(f"Ошибка при получении данных о вакансиях для области с ID {area_id}")
        return []

# Функция для обработки данных и записи в CSV
def process_and_save_to_csv(vacancies, filename):
    data = {'Location': [], 'Vacancy Name': [], 'Experience Required': [], 'Average Salary': [], 'Industry': [], 'Schedule': []}
    for vacancy_data in vacancies:
        if vacancy_data['salary']:
            salary_from = vacancy_data['salary']['from']
            salary_to = vacancy_data['salary']['to']
            if salary_from and salary_to:
                average_salary = (salary_from + salary_to) / 2
            elif salary_from:
                average_salary = salary_from
            elif salary_to:
                average_salary = salary_to
            else:
                average_salary = None
        else:
            average_salary = None

        location = vacancy_data['area']['name']
        vacancy_name = vacancy_data['name']
        experience = vacancy_data['experience']['name']
        industry = vacancy_data['professional_roles'][0]['name']
        schedule = vacancy_data['schedule']['name']
        if all([location, vacancy_name, experience, industry]):
            data['Location'].append(location)
            data['Vacancy Name'].append(vacancy_name)
            data['Experience Required'].append(experience)
            data['Average Salary'].append(average_salary)
            data['Industry'].append(industry)
            data['Schedule'].append(schedule)
    df = pd.DataFrame.from_dict(data)
    df.to_csv(filename, mode='a', index=False, header=not os.path.exists(filename))
    print(f"Все вакансии были успешно добавлены в файл '{filename}'.")

# Получаем номера областей
area_ids = get_area_ids()

# Если удалось получить номера областей, выполняем запросы по вакансиям и сохраняем в CSV
if area_ids:
    filename = "all_vacancies.csv"
    for area_id in area_ids:
        area_vacancies = get_vacancies_from_area(area_id)
        if area_vacancies:
            process_and_save_to_csv(area_vacancies, filename)
        else:
            print(f"Нет доступных вакансий для области с ID {area_id}.")
else:
    print("Не удалось получить номера областей.")
