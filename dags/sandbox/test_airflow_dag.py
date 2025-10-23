from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore


# Функция, которая будет выполняться в задаче
def print_message():
    print("Тест AIRFLOW")


# Определяем DAG
with DAG(
    dag_id="test_airflow_dag",
    start_date=datetime(2025, 1, 1),
    schedule=None,  # запускать вручную
    catchup=False,
    tags=["example"],
) as dag:

    task_print = PythonOperator(
        task_id="print_test_message", python_callable=print_message
    )
