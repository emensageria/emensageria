from django.test import SimpleTestCase

from adminlteui.core import MenuItem
from adminlteui_custom.adminlte_config import MyAdminlteConfig


class MyAdminlteConfigTests(SimpleTestCase):

    def test_main_menu_and_static_attributes_are_defined(self):
        self.assertEqual(MyAdminlteConfig.copyright, "Marcelo Vasconcellos")
        self.assertFalse(MyAdminlteConfig.search_form)
        self.assertEqual(MyAdminlteConfig.welcome_sign, "Seja bem-vindo")
        self.assertEqual(len(MyAdminlteConfig.main_menu), 8)

        first_item = MyAdminlteConfig.main_menu[0]
        last_item = MyAdminlteConfig.main_menu[-1]

        self.assertIsInstance(first_item, MenuItem)
        self.assertEqual(first_item.label, "esocial.Eventos")
        self.assertEqual(first_item.menu_type, "model")

        self.assertIsInstance(last_item, MenuItem)
        self.assertEqual(last_item.name, "API")
        self.assertEqual(last_item.url, "/esocial/api/")
