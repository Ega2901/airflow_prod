import unittest
import warnings
from unittest.mock import patch, MagicMock, PropertyMock
from airflow.models import DagBag


class TestDagIntegrity(unittest.TestCase):
    def setUp(self):
        # Полное подавление всех предупреждений
        warnings.filterwarnings("ignore")
        warnings.simplefilter("ignore", category=DeprecationWarning)

        # Создаем реалистичный мок подключения
        self.conn_mock = MagicMock()
        type(self.conn_mock).host = PropertyMock(return_value="test_host")
        type(self.conn_mock).port = PropertyMock(return_value=1234)
        type(self.conn_mock).login = PropertyMock(return_value="test_user")
        type(self.conn_mock).password = PropertyMock(return_value="test_pass")
        type(self.conn_mock).extra_dejson = PropertyMock(
            return_value={"param": "value"}
        )

        # Патчим все внешние зависимости
        self.patches = [
            patch(
                "airflow.hooks.base.BaseHook.get_connection",
                return_value=self.conn_mock,
            ),
            patch("clickhouse_connect.get_client", return_value=MagicMock()),
            patch("sqlalchemy.create_engine", return_value=MagicMock()),
            patch("psycopg2.connect", return_value=MagicMock()),
            patch("requests.Session", return_value=MagicMock()),
        ]

        for p in self.patches:
            p.start()

        # Инициализируем DagBag с обработкой ошибок
        self.dagbag = DagBag(
            dag_folder="dags",
            include_examples=False,
            read_dags_from_db=False,
            load_op_links=False,
        )

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_dag_import_errors(self):
        """Проверка отсутствия критических ошибок импорта"""
        error_count = len(self.dagbag.import_errors)
        if error_count > 0:
            print("\nFound DAG import errors:")
            for fn, err in self.dagbag.import_errors.items():
                print(f"\n{fn}:\n{'-'*50}\n{err}")
        self.assertEqual(error_count, 0, f"Found {error_count} DAG import errors")

    def test_dags_loaded(self):
        """Проверка загрузки хотя бы одного DAG"""
        self.assertGreater(len(self.dagbag.dags), 0, "No DAGs loaded")


if __name__ == "__main__":
    unittest.main(failfast=True, verbosity=2)
