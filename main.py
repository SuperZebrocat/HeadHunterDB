from config import config
from src.db_manager import DBManager
from src.utils import create_database, get_data_for_database, get_employer_data_from_api, save_data_to_database

EMPLOYERS_LIST = ["67611", "701365", "4334427", "906557", "2324020", "8997092", "2265728", "3202190", "3177", "640251"]


def main():
    keyword = input("Введите ключевое слово для поиска вакансий: ")

    params = config()

    employer_data_list = get_employer_data_from_api(EMPLOYERS_LIST)
    data_for_database = get_data_for_database(employer_data_list)

    create_database("hh_database", params)
    save_data_to_database(data_for_database, "hh_database", params)

    db_manager = DBManager("hh_database", params)

    vacancies_with_keyword = db_manager.get_vacancies_with_keyword(keyword)
    vacancies_counter = 0
    print(f'\nПо ключевому слову "{keyword}" найдено {len(vacancies_with_keyword)} вакансий')
    for employer_name, vacancy_name, salary_from, salary_to, vacancy_url in vacancies_with_keyword:
        vacancies_counter += 1
        salary = ""
        if (salary_from and salary_to) != 0:
            salary = f"{salary_to}-{salary_to} руб."
        elif salary_from != 0 and salary_to == 0:
            salary = f"{salary_from} руб."
        elif salary_from == 0 and salary_to != 0:
            salary = f"{salary_to} руб."
        print(
            f"{vacancies_counter}. Название компании: {employer_name}\nНазвание вакансии: {vacancy_name}\n"
            f"Зарплата: {salary}\nСсылка на вакансию: {vacancy_url}\n"
        )


if __name__ == "__main__":
    main()
