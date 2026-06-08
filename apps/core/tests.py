from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.core.forms import validar_cpf


class CpfValidationTestCase(TestCase):
    def test_valid_cpfs(self):
        # List of mathematically valid CPFs for testing
        valid_cpfs = [
            "12345678909",
            "52998224725",
        ]
        for cpf in valid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertTrue(validar_cpf(cpf))

    def test_invalid_cpfs(self):
        # List of mathematically invalid CPFs for testing
        invalid_cpfs = [
            "11111111111",
            "12345678900",
            "12345678901",
            "00000000000",
            "123",
        ]
        for cpf in invalid_cpfs:
            with self.subTest(cpf=cpf):
                self.assertFalse(validar_cpf(cpf))
