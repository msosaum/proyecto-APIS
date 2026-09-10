import os
import unittest

os.environ.pop("HF_TOKEN", None)

import agente_viaje


class TestAgenteViaje(unittest.TestCase):
    def test_ejecutar_agente_sin_token_falla_explicitamente(self):
        with self.assertRaises(RuntimeError) as contexto:
            agente_viaje.ejecutar_agente(
                "Cuanto llevamos gastado en total y cuanto nos falta pagar?"
            )
        self.assertIn("HF_TOKEN", str(contexto.exception))


if __name__ == "__main__":
    unittest.main()
