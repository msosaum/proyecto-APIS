import os
import unittest

os.environ.pop("HF_TOKEN", None)

import agente_viaje


class TestAgenteViaje(unittest.TestCase):
    def test_ejecutar_agente_sin_token(self):
        respuesta = agente_viaje.ejecutar_agente(
            "Cuanto llevamos gastado en total y cuanto nos falta pagar?"
        )
        self.assertIsInstance(respuesta, str)
        self.assertIn("gastado", respuesta.lower())
        self.assertIn("falta pagar", respuesta.lower())


if __name__ == "__main__":
    unittest.main()
