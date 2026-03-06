from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase

from apps.esocial.models import Certificados
from apps.users.models import User
from config import mixins


class _FakeQuerySet:

    def __init__(self, model=None):
        self.model = model
        self.filtered_args = ()
        self.filtered_kwargs = {}

    def filter(self, *args, **kwargs):
        self.filtered_args = args
        self.filtered_kwargs = kwargs
        return self


class _DummyUser:

    def __init__(self, user_id=1, is_superuser=False, has_perm_result=False):
        self.id = user_id
        self.is_superuser = is_superuser
        self._has_perm_result = has_perm_result

    def has_perm(self, _perm):
        return self._has_perm_result


class MixinsTests(SimpleTestCase):

    def test_eventos_manager_get_queryset_all_obj_returns_queryset(self):
        manager = mixins.EventosManager(all_obj=True)
        manager.model = type("AnyModel", (), {})

        with patch("config.mixins.QuerySet", _FakeQuerySet), \
                patch("config.mixins.get_current_user", return_value=None):
            queryset = manager.get_queryset()

        self.assertIsInstance(queryset, _FakeQuerySet)
        self.assertEqual(queryset.model, manager.model)

    def test_eventos_manager_get_queryset_filters_non_special_model(self):
        manager = mixins.EventosManager()
        manager.model = type("EventoGenerico", (), {})
        user = _DummyUser(user_id=10, is_superuser=False)

        with patch("config.mixins.QuerySet", _FakeQuerySet), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertEqual(queryset.filtered_kwargs, {"created_by_id": 10})

    def test_eventos_manager_get_queryset_filters_special_model(self):
        manager = mixins.EventosManager()
        manager.model = type("Certificados", (), {})
        user = _DummyUser(user_id=11, is_superuser=False)

        with patch("config.mixins.QuerySet", _FakeQuerySet), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertEqual(queryset.filtered_kwargs, {})
        self.assertEqual(len(queryset.filtered_args), 1)

    def test_auditoria_manager_get_queryset_all_obj_returns_super_queryset(self):
        manager = mixins.AuditoriaManager(all_obj=True)
        manager.model = type("Modelo", (), {})
        fake_queryset = _FakeQuerySet()

        with patch("config.mixins.models.Manager.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=None):
            queryset = manager.get_queryset()

        self.assertIs(queryset, fake_queryset)

    def test_auditoria_manager_get_queryset_filters_non_special_model(self):
        manager = mixins.AuditoriaManager(all_obj=False)
        manager.model = type("EventoGenerico", (), {})
        fake_queryset = _FakeQuerySet()
        user = _DummyUser(user_id=21, has_perm_result=False)

        with patch("config.mixins.models.Manager.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertEqual(queryset.filtered_kwargs, {"created_by": user})

    def test_auditoria_manager_get_queryset_filters_special_model(self):
        manager = mixins.AuditoriaManager(all_obj=False)
        manager.model = type("Certificados", (), {})
        fake_queryset = _FakeQuerySet()
        user = _DummyUser(user_id=22, has_perm_result=False)

        with patch("config.mixins.models.Manager.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertEqual(queryset.filtered_kwargs, {})
        self.assertEqual(len(queryset.filtered_args), 1)

    def test_auditoria_manager_get_queryset_returns_base_for_non_special_model(self):
        manager = mixins.AuditoriaManager(all_obj=False)
        manager.model = type("EventoGenerico", (), {})
        fake_queryset = _FakeQuerySet()
        user = _DummyUser(user_id=30, has_perm_result=True)

        with patch("config.mixins.models.Manager.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertIs(queryset, fake_queryset)

    def test_auditoria_manager_get_queryset_returns_base_for_special_model(self):
        manager = mixins.AuditoriaManager(all_obj=False)
        manager.model = type("Certificados", (), {})
        fake_queryset = _FakeQuerySet()
        user = _DummyUser(user_id=31, has_perm_result=True)

        with patch("config.mixins.models.Manager.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = manager.get_queryset()

        self.assertIs(queryset, fake_queryset)

    def test_auditoria_admin_eventos_has_view_permission_denies_other_owner(self):
        admin_obj = mixins.AuditoriaAdminEventos(User, AdminSite())
        current_user = _DummyUser(user_id=7, has_perm_result=False)
        other_user = _DummyUser(user_id=8, has_perm_result=False)
        obj = SimpleNamespace(created_by=other_user)

        with patch("config.mixins.get_current_user", return_value=current_user), \
                patch("config.mixins.FILTER_BY_USER", True):
            allowed = admin_obj.has_view_permission(
                request=SimpleNamespace(user=current_user),
                obj=obj,
            )

        self.assertFalse(allowed)

    def test_auditoria_admin_eventos_has_view_permission_falls_back_to_super(self):
        admin_obj = mixins.AuditoriaAdminEventos(User, AdminSite())
        current_user = _DummyUser(user_id=7, has_perm_result=True)

        with patch("config.mixins.get_current_user", return_value=current_user), \
                patch("config.mixins.admin.ModelAdmin.has_view_permission", return_value=True), \
                patch("config.mixins.FILTER_BY_USER", True):
            allowed = admin_obj.has_view_permission(
                request=SimpleNamespace(user=current_user),
                obj=None,
            )

        self.assertTrue(allowed)

    def test_auditoria_admin_eventos_get_queryset_filters_special_models(self):
        admin_obj = mixins.AuditoriaAdminEventos(Certificados, AdminSite())
        fake_queryset = _FakeQuerySet()
        current_user = _DummyUser(user_id=9, has_perm_result=False)

        with patch("config.mixins.admin.ModelAdmin.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=current_user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = admin_obj.get_queryset(request=SimpleNamespace(user=current_user))

        self.assertEqual(queryset.filtered_kwargs, {})
        self.assertEqual(len(queryset.filtered_args), 1)

    def test_auditoria_admin_eventos_get_queryset_filters_non_special_models(self):
        admin_obj = mixins.AuditoriaAdminEventos(User, AdminSite())
        fake_queryset = _FakeQuerySet()
        current_user = _DummyUser(user_id=9, has_perm_result=False)

        with patch("config.mixins.admin.ModelAdmin.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=current_user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = admin_obj.get_queryset(request=SimpleNamespace(user=current_user))

        self.assertEqual(queryset.filtered_kwargs, {"created_by": current_user})

    def test_auditoria_admin_eventos_get_queryset_returns_base_queryset(self):
        admin_obj = mixins.AuditoriaAdminEventos(User, AdminSite())
        fake_queryset = _FakeQuerySet()
        current_user = _DummyUser(user_id=9, has_perm_result=True)

        with patch("config.mixins.admin.ModelAdmin.get_queryset", return_value=fake_queryset), \
                patch("config.mixins.get_current_user", return_value=current_user), \
                patch("config.mixins.FILTER_BY_USER", True):
            queryset = admin_obj.get_queryset(request=SimpleNamespace(user=current_user))

        self.assertIs(queryset, fake_queryset)

    def test_auditoria_admin_eventos_get_readonly_fields_for_special_model_with_perm(self):
        admin_obj = mixins.AuditoriaAdminEventos(Certificados, AdminSite())
        request = SimpleNamespace(user=_DummyUser(has_perm_result=True))

        with patch(
            "config.mixins.admin.ModelAdmin.get_readonly_fields",
            return_value=("base_field",),
        ):
            readonly = admin_obj.get_readonly_fields(request=request)

        self.assertEqual(readonly, ("base_field",))

    def test_auditoria_admin_eventos_get_readonly_fields_for_special_model_without_perm(self):
        admin_obj = mixins.AuditoriaAdminEventos(Certificados, AdminSite())
        request = SimpleNamespace(user=_DummyUser(has_perm_result=False))

        readonly = admin_obj.get_readonly_fields(request=request)
        self.assertIn("users", readonly)

    def test_auditoria_admin_eventos_get_readonly_fields_for_non_special_model(self):
        admin_obj = mixins.AuditoriaAdminEventos(User, AdminSite())
        request = SimpleNamespace(user=_DummyUser(has_perm_result=False))

        with patch(
            "config.mixins.admin.ModelAdmin.get_readonly_fields",
            return_value=("x", "y"),
        ):
            readonly = admin_obj.get_readonly_fields(request=request)

        self.assertEqual(readonly, ("x", "y"))
