"""Стартовые тесты клиента из предыдущего спринта."""

import os

import pytest
import requests
from dotenv import load_dotenv

from api_client import CourierAPIClient
from models import CourierModel

load_dotenv()


@pytest.fixture(scope="session")
def client():
    """Создаёт клиент API один раз на весь прогон."""
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:5001/api")
    token = os.getenv("AUTH_TOKEN", "test_token_123")
    return CourierAPIClient(base_url, token)


@pytest.fixture
def new_courier_data():
    """Возвращает данные для создания курьера."""
    return {
        "first_name": "Мария",
        "last_name": "Сидорова",
        "phone": "+79997654321",
    }


@pytest.mark.usefixtures("fake_server")
class TestCourierClient:
    """Проверяет получение, создание и удаление курьера."""

    def test_get_courier_by_id(self, client):
        """Получает курьера, который уже есть на сервере."""
        courier = client.get_courier_by_id(1)
        validated = CourierModel(**courier)

        assert validated.id == 1, "Убедитесь, что получен курьер с id=1."
        assert validated.first_name == "Иван", (
            "Убедитесь, что API вернул правильное имя курьера."
        )

    def test_create_courier(self, client, new_courier_data):
        """Создаёт курьера с переданными данными."""
        result = client.create_courier(new_courier_data)
        assert "id" in result, "Убедитесь, что у созданного курьера есть id."
        assert result["first_name"] == new_courier_data["first_name"], (
            "Убедитесь, что имя созданного курьера совпадает с переданным."
        )

    def test_get_nonexistent_courier_raises(self, client):
        """Ожидает HTTPError при запросе несуществующего курьера."""
        with pytest.raises(requests.exceptions.HTTPError):
            client.get_courier_by_id(99999)

    def test_delete_courier(self, client):
        """Удаляет курьера, который уже есть на сервере."""
        result = client.delete_courier(2)
        assert result == {"status": "deleted"}, (
            "Убедитесь, что API подтвердил удаление курьера."
        )
    
    def test_update_courier(self, client, new_courier_data):
        """Обновляет имя созданного курьера."""
        # Arrange
        created = client.create_courier(new_courier_data)
        courier_id = created["id"]
        new_name = "Анна"

        # Act
        updated = client.update_courier(courier_id, {"first_name": new_name})

        # Assert
        validated = CourierModel(**updated)
        assert validated.first_name == new_name, (
            f"Ожидали имя '{new_name}', получили '{validated.first_name}'"
        )

    def test_delete_then_get_returns_404(self, client, new_courier_data):
        # Arrange
        created = client.create_courier(new_courier_data)
        courier_id = created["id"]

        # Act
        client.delete_courier(courier_id)

        # Assert
        with pytest.raises(requests.exceptions.HTTPError) as error:
            client.get_courier_by_id(courier_id)

        assert error.value.response.status_code == 404, (
            f"Ожидали 404, получили {error.value.response.status_code}"
        )

    def test_create_courier_without_first_name_returns_400(self, client):
        """Создание курьера без обязательного имени возвращает 400."""
        # Arrange
        invalid_data = {
            "last_name": "Сидорова",
            "phone": "+79997654321",
        }

        # Act
        with pytest.raises(requests.exceptions.HTTPError) as error:
            client.create_courier(invalid_data)

        # Assert
        assert error.value.response.status_code == 400, (
            f"Ожидали 400, получили {error.value.response.status_code}"
        )

    def test_update_nonexistent_courier_returns_404(self, client):
        """Обновление несуществующего курьера возвращает 404."""
        # Arrange
        nonexistent_id = 99999

        # Act
        with pytest.raises(requests.exceptions.HTTPError) as error:
            client.update_courier(nonexistent_id, {"first_name": "Анна"})

        # Assert
        assert error.value.response.status_code == 404, (
            f"Ожидали 404, получили {error.value.response.status_code}"
        )