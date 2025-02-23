import psycopg2


class DBManager:
    def __init__(self, database_name: str, params: dict):
        self.database_name = database_name
        self.params = params

    def connect(self):
        """Метод для создания соединения с базой данных"""
        return psycopg2.connect(dbname=self.database_name, **self.params)

    def get_companies_and_vacancies_count(self):
        """Метод получения списка всех компаний и количество вакансий у каждой компании"""
        query = """SELECT employer_name, COUNT(vacancy_name) AS vacancies_count
                FROM employers
                JOIN vacancies USING (employer_id)
                GROUP BY employer_name
                ORDER BY employer_name ASC;
                """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()

        return result

    def get_all_vacancies(self):
        """Метод получения списка всех вакансий"""
        query = """SELECT employer_name, vacancy_name, salary_from, salary_to, vacancy_url
                FROM vacancies
                JOIN employers USING (employer_id)
                ORDER BY employer_name ASC;
                """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()

        return result

    def get_avg_salary(self):
        """Метод получения средней зарплаты по вакансиям"""
        query = """SELECT CAST(AVG(salary_avg) AS INTEGER)
                FROM vacancies;
                """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()

        return result

    def get_vacancies_with_higher_salary(self):
        """Метод получения списка вакансий с зарплатой выше средней по всем вакансиям"""
        query = """SELECT employer_name, vacancy_name, salary_from, salary_to, vacancy_url
                FROM vacancies
                JOIN employers USING (employer_id)
                WHERE vacancies.salary_avg > (SELECT CAST(AVG(salary_avg) AS INTEGER) FROM vacancies);
                """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchall()

        return result

    def get_vacancies_with_keyword(self, keyword):
        """Метод получения списка вакансий по ключевому слову в названии"""
        query = """SELECT employer_name, vacancy_name, salary_from, salary_to, vacancy_url
                FROM vacancies
                JOIN employers USING (employer_id)
                WHERE vacancies.vacancy_name ILIKE %s;
                """
        like_pattern = f"%{keyword}%"
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (like_pattern,))
                result = cur.fetchall()

        return result
