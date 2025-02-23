import psycopg2
import requests


def get_employer_data_from_api(employers_ids: list[str]) -> list[dict]:
    """Функция получения данных от API о работодателях и их вакансиях из переданного списка"""
    employer_data_list = []
    for employer_id in employers_ids:
        url = f"https://api.hh.ru/employers/{employer_id}"
        headers = {"User-Agent": "HH-User-Agent"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            response_from_api = response.json()  # Возвращаем JSON-ответ
            employer_data = {
                "employer_name": response_from_api.get("name"),
                "vacancies_url": response_from_api.get("vacancies_url"),
            }
            employer_data_list.append(employer_data)

        except requests.exceptions.RequestException as e:
            print(f"Произошла ошибка при запросе: {e}")
            return []

    return employer_data_list


def get_vacancies_data_from_api(employer_data: dict) -> list[dict]:
    """Функция для получения данных о вакансиях от API"""
    url = employer_data.get("vacancies_url")
    headers = {"User-Agent": "HH-User-Agent"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        response_from_api = response.json()
        vacancies_data_list = []
        if isinstance(response_from_api, dict):
            vacancies = response_from_api.get("items")
            if vacancies:
                for vacancy in vacancies:
                    if vacancy.get("salary") is not None and vacancy.get("salary").get("currency") == "RUR":
                        salary_from = vacancy.get("salary").get("from") or 0
                        salary_to = vacancy.get("salary").get("to") or 0
                        salary_avg = (
                            (salary_from + salary_to) // 2
                            if salary_from and salary_to
                            else max(salary_from, salary_to)
                        )

                        vacancy_data = {
                            "vacancy_name": vacancy.get("name"),
                            "salary_from": salary_from,
                            "salary_to": salary_to,
                            "salary_avg": salary_avg,
                            "vacancy_url": vacancy.get("alternate_url"),
                        }
                        vacancies_data_list.append(vacancy_data)
        return vacancies_data_list
    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при запросе: {e}")
        return []


def get_data_for_database(employer_data_list: list[dict]) -> list[dict]:
    """Функция формирования данных о работодателях и их вакансиях для передачи в БД"""
    data_for_database = []
    for employer_data in employer_data_list:
        vacancies = get_vacancies_data_from_api(employer_data)
        data_dict = {"employer_name": employer_data["employer_name"], "vacancies": vacancies}
        data_for_database.append(data_dict)
    return data_for_database


def create_database(database_name: str, params: dict) -> None:
    """Создание базы данных и таблиц для сохранения данных о работодателях и вакансиях"""
    conn = psycopg2.connect(dbname="postgres", **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
    cur.execute(f"CREATE DATABASE {database_name}")

    cur.close()
    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE employers (
                employer_id SERIAL PRIMARY KEY,
                employer_name VARCHAR(255) NOT NULL
                )
        """
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE vacancies (
                vacancy_id SERIAL PRIMARY KEY,
                vacancy_name VARCHAR(200) NOT NULL,
                salary_from INT,
                salary_to INT,
                salary_avg INT,
                vacancy_url TEXT,
                employer_id INT REFERENCES employers(employer_id)
            )
        """
        )

    conn.commit()
    conn.close()


def save_data_to_database(data: list[dict], database_name: str, params: dict) -> None:
    """Функция для внесения данных о работодателях и вакансиях в базу данных"""
    conn = psycopg2.connect(dbname=database_name, **params)
    with conn.cursor() as cur:
        for employer in data:
            cur.execute(
                """
                INSERT INTO employers (employer_name)
                VALUES (%s)
                RETURNING employer_id
                """,
                (employer["employer_name"],),
            )
            employer_id = cur.fetchone()[0]
            vacancies = employer["vacancies"]
            for vacancy in vacancies:
                cur.execute(
                    """
                    INSERT INTO vacancies (vacancy_name, salary_from, salary_to, salary_avg, vacancy_url, employer_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING vacancy_id
                    """,
                    (
                        vacancy["vacancy_name"],
                        vacancy["salary_from"],
                        vacancy["salary_to"],
                        vacancy["salary_avg"],
                        vacancy["vacancy_url"],
                        employer_id,
                    ),
                )

        conn.commit()
        conn.close()
