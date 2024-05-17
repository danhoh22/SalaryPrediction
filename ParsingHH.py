from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import URLError
import json
import pandas as pd
import re

def create_soup(link):
    '''Возвращает экземпляр BeautifulSoup для соответсвующей ссылки'''
    page = urlopen(link)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")
    return BeautifulSoup(html, "html.parser")

def process_page(vacancies, vac_dict):
    '''
    Обходит все вакансии на странице и добавляет извлеченные
    данные в соотвествующий список
    '''
    # Создаем регулярное выражение для парсинга данных о ЗП
    regex = re.compile('vacancy-salary-compensation-type-.*')
    # Итерируем по списку вакансий
    for vacancy in vacancies:
        link = vacancy.find('a')['href']
        # Подготавливаем soup
        vac_soup = create_soup(link)
        # Извлекаем местоположение и отрасль
        js = json.loads("".join(vac_soup.find("script", {"type":"application/ld+json"}).contents))
        vac_dict['location'].append(js['jobLocation']['address']['addressLocality'])
        vac_dict['title'].append(js['title'])
        # Извлекаем ЗП
        try:
            min_value = int(js['baseSalary']['value'].get('minValue'))
            max_value = js['baseSalary']['value'].get('maxValue')
            if max_value:
                max_value = int(max_value)
                avg_salary = (min_value + max_value) / 2
                vac_dict['salary'].append(avg_salary)
            else:
                vac_dict['salary'].append(min_value)
        except (KeyError, TypeError):
            vac_dict['salary'].append(None)
        # Извлекаем навыки
        try:
            skills_divs = vac_soup.findAll('div', {'class': 'bloko-tag-list'})
            # Найдем все теги <span> внутри тега <div> с классом "bloko-tag-list"
            # Создадим пустой список для хранения текста навыков
            skills = []

            # Итерируем по каждому элементу списка skills_divs
            for div in skills_divs:
                # Найдем все теги <span> внутри текущего элемента div
                span_elements = div.find_all('span', class_='bloko-tag__section_text')
                # Для каждого найденного тега <span> добавим его текст в список skills
                for span in span_elements:
                    skills.append(span.get_text())

            # Объединим список в строку, разделяя элементы точкой с запятой
            skills_string = '; '.join(skills)

            # Добавим строку с навыками в словарь vac_dict
            vac_dict['skills'].append(skills_string)
        except:
            vac_dict['skills'].append(None)
        # Извлекаем опыт
        try:
            vac_dict['experience'].append(vac_soup.find('span',{'data-qa':'vacancy-experience'}).get_text())
        except:
            vac_dict['experience'].append(None)

url = 'https://kirov.hh.ru/search/vacancy?text=&area=49&hhtmFrom=main&hhtmFromLabel=vacancy_search_line'
vac_dict = {'location': [], 'title': [], 'experience': [], 'skills': [], 'salary': []}
pages = 39
# Итерируем по страницам
for page in range(pages):
    page_link = url + '&page=' + str(page)
    try:
        # Подготавливаем soup
        page_soup = create_soup(page_link)
        # Извлекаем все вакансии на странице
        vacancies = page_soup.find_all('div', class_='vacancy-serp-item-body')
        # Передаем полученный список в функцию для сбора данных о каждой вакансии
        process_page(vacancies, vac_dict)
        print('Страница ', page, 'завершена.')
    except Exception as e:
        print('Произошла ошибка при обработке страницы', page, ':', e)
        print('URL страницы:', page_link)
        print('Пропуск страницы...')

# Заполнение отсутствующих данных в словаре до одинаковой длины
max_len = max(map(len, vac_dict.values()))
for key, value in vac_dict.items():
    vac_dict[key] += [None] * (max_len - len(value))

# Преобразовываем словарь в DataFrame
vacancies = pd.DataFrame.from_dict(vac_dict)

# Создаем список всех уникальных навыков
unique_skills = set()
for skills_string in vac_dict['skills']:
    if skills_string:
        # Разделяем строку навыков по точке с запятой и добавляем каждый навык во множество уникальных навыков
        for skill in skills_string.split('; '):
            unique_skills.add(skill)

# Создаем DataFrame для навыков с нулевыми значениями по умолчанию
skills_df = pd.DataFrame(0, index=vacancies.index, columns=list(unique_skills))

# Проходим по каждой записи в DataFrame и устанавливаем значение 1 в соответствующем столбце, если у записи есть этот навык
for index, row in vacancies.iterrows():
    if row['skills']:
        for skill in row['skills'].split('; '):
            skills_df.at[index, skill] = 1

# Объединяем исходный DataFrame с DataFrame навыков
vacancies = pd.concat([vacancies, skills_df], axis=1)

# Удаляем столбец 'skills', так как он больше не нужен
vacancies.drop('skills', axis=1, inplace=True)

# Записываем DataFrame в CSV файл
vacancies.to_csv('vacancies.csv', index=False)
