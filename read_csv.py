import csv

def read_csv_file(file_path):
    """
    Читает данные из CSV файла.

    :param file_path: Путь к CSV файлу.
    :return: Список строк, каждая строка - список значений.
    """
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data
