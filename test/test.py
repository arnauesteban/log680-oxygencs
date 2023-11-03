import pytest
from src.main import Main


# Test unitaire pour vérifier que send_event_to_database()
# insère des événements dans la base de données
def test_send_event_to_database(main_instance):
    """
    Test unitaire pour vérifier que send_event_to_database()
    insère des événements dans la base de données
    """
    timestamp = "2023-11-01T12:34:56"
    event = "TurnOnAc"
    main_instance.send_event_to_database(timestamp, event)

    try:
        cursor = main_instance.DATABASE.cursor()
        cursor.execute("SELECT * FROM eventoxygencs WHERE event = %s", (event,))
        result = cursor.fetchone()
        cursor.close()
        assert (
            result
        ), f"Prueba fallida: Evento '{event}' no se insertó en la base de datos."
    # pylint: disable = broad-exception-caught
    except Exception as error:
        pytest.fail(f"ERROR CON LA BASE DE DATOS: {error}")


if __name__ == "__main__":
    main = Main()
    test_send_event_to_database(main)
