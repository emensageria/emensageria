from unittest.mock import patch

from django.test import SimpleTestCase

from adminlteui_custom.templatetags import custom_fieldset


class _Paginator:
    num_pages = 10


class _ChangeList:
    page_num = 2
    paginator = _Paginator()

    @staticmethod
    def get_query_string(params):
        return f'?p={params["p"]}'


class _NoDict:
    __slots__ = ()


class _WithDict:
    pass


class _WithTabTrue:
    tab = True


class _WithTabFalse:
    tab = False


class _ModelWithCols:
    cols = {"field_a": 8}


class _ModelWithoutCols:
    pass


class _MetaWithCols:
    model = _ModelWithCols


class _MetaWithoutCols:
    model = _ModelWithoutCols


class _FormWithCols:
    Meta = _MetaWithCols


class _FormWithoutCols:
    Meta = _MetaWithoutCols


class _InnerFieldWithCols:
    form = _FormWithCols()
    name = "field_a"


class _InnerFieldWithoutCols:
    form = _FormWithoutCols()
    name = "field_a"


class _EditableFieldWithCols:
    is_readonly = False
    field = _InnerFieldWithCols()


class _EditableFieldWithoutCols:
    is_readonly = False
    field = _InnerFieldWithoutCols()


class _ReadonlyModelWithCols:
    cols = {"field_b": 6}


class _ReadonlyModelWithoutCols:
    pass


class _ReadonlyModelAdminWithCols:
    model = _ReadonlyModelWithCols


class _ReadonlyModelAdminWithoutCols:
    model = _ReadonlyModelWithoutCols


class _ReadonlyFieldWithCols:
    is_readonly = True
    field = {"name": "field_b"}
    model_admin = _ReadonlyModelAdminWithCols()


class _ReadonlyFieldWithoutCols:
    is_readonly = True
    field = {"name": "field_b"}
    model_admin = _ReadonlyModelAdminWithoutCols()


class CustomFieldsetTests(SimpleTestCase):

    def test_adminlte_paginator_number_handles_ellipsis(self):
        html_dot = str(
            custom_fieldset.adminlte_paginator_number(_ChangeList(), custom_fieldset.DOT)
        )
        html_unicode = str(custom_fieldset.adminlte_paginator_number(_ChangeList(), "…"))

        self.assertIn("…", html_dot)
        self.assertIn("…", html_unicode)

    def test_adminlte_paginator_number_handles_current_and_regular_pages(self):
        html_current = str(custom_fieldset.adminlte_paginator_number(_ChangeList(), 2))
        html_regular = str(custom_fieldset.adminlte_paginator_number(_ChangeList(), 3))
        html_last = str(custom_fieldset.adminlte_paginator_number(_ChangeList(), 9))

        self.assertIn("active", html_current)
        self.assertIn(">2<", html_current)
        self.assertIn("?p=3", html_regular)
        self.assertNotIn('class="end"', html_regular)
        self.assertIn('class="end"', html_last)

    def test_div_name_filter(self):
        self.assertEqual(custom_fieldset.div_name("Meu Nome"), "meu_nome_div")
        self.assertEqual(custom_fieldset.div_name(""), "main_div")

    def test_not_none_filter(self):
        self.assertEqual(custom_fieldset.not_none(None), "-")
        self.assertEqual(custom_fieldset.not_none("valor"), "valor")

    def test_test_filter_handles_objects_and_exceptions(self):
        with patch("builtins.print") as print_mock:
            self.assertEqual(custom_fieldset.test(_WithDict()), "")
            self.assertEqual(custom_fieldset.test(_NoDict()), "")
            self.assertGreaterEqual(print_mock.call_count, 2)

    def test_tab_organize_filter_branches(self):
        with patch("builtins.print") as print_mock:
            self.assertFalse(custom_fieldset.tab_organize(_WithTabTrue()))
            self.assertIsNone(custom_fieldset.tab_organize(_WithTabFalse()))
            self.assertTrue(custom_fieldset.tab_organize(object()))
            print_mock.assert_called()

    def test_to_slug_and_to_str_filters(self):
        self.assertEqual(custom_fieldset.to_slug("Olá Mundo"), "ola-mundo")
        self.assertEqual(custom_fieldset.to_str(123), "123")

    def test_bootstrap_cols_number_for_editable_fields(self):
        self.assertEqual(custom_fieldset.bootstrap_cols_number(_EditableFieldWithCols()), 8)
        self.assertEqual(custom_fieldset.bootstrap_cols_number(_EditableFieldWithoutCols()), 4)

    def test_bootstrap_cols_number_for_readonly_fields(self):
        self.assertEqual(custom_fieldset.bootstrap_cols_number(_ReadonlyFieldWithCols()), 6)
        self.assertEqual(custom_fieldset.bootstrap_cols_number(_ReadonlyFieldWithoutCols()), 4)
