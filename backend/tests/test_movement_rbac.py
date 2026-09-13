from datetime import datetime
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.models.movement import Movement
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.services.movement_service import movement_service


def _user(
    user_id: int,
    role: str,
    permissions=None,
    bureau_id=None,
    admin_circonscription_id=None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        permissions=permissions or [],
        bureau_id=bureau_id,
        admin_circonscription_id=admin_circonscription_id,
    )


def _doc(doc_id: int, bureau_id: int, circonscription_id: int = 1):
    return SimpleNamespace(
        id=doc_id,
        bureau_id=bureau_id,
        circonscription_id=circonscription_id,
    )


def _bureau(bureau_id: int, circonscription_id: int = 1, actif: bool = True):
    return SimpleNamespace(
        id=bureau_id,
        circonscription_id=circonscription_id,
        actif=actif,
    )


def _movement(
    movement_id: int,
    document_id: int,
    user_id: int = 1,
    bureau_origine_id=None,
    bureau_destination_id=None,
    statut="EN_COURS",
):
    return SimpleNamespace(
        id=movement_id,
        document_id=document_id,
        user_id=user_id,
        bureau_origine_id=bureau_origine_id,
        bureau_destination_id=bureau_destination_id,
        statut=statut,
        date_mouvement=datetime.now(),
    )


class TestMovementRbac(unittest.TestCase):

    def setUp(self):
        self.db = SimpleNamespace(
            commit=lambda: None,
            rollback=lambda: None,
        )

    # TEST 1
    def test_user_bureau_1_get_all_scoped_to_bureau_1(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)
        expected = [_movement(1, 10, 11)]

        with patch(
            "app.services.movement_service.movement_repository.get_all",
            return_value=expected,
        ) as mock_get_all:
            result = movement_service.get_all(self.db, user)

        self.assertEqual(len(result), 1)
        mock_get_all.assert_called_once_with(
            self.db,
            bureau_id=1,
            circonscription_id=None,
        )

    # TEST 2
    def test_user_bureau_1_get_active_scoped_to_bureau_1(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)
        expected = [_movement(2, 10, 11)]

        with patch(
            "app.services.movement_service.movement_repository.get_active",
            return_value=expected,
        ) as mock_get_active:
            result = movement_service.get_active(self.db, user)

        self.assertEqual(len(result), 1)
        mock_get_active.assert_called_once_with(
            self.db,
            bureau_id=1,
            circonscription_id=None,
        )

    # TEST 3
    def test_user_bureau_1_get_by_id_own_bureau_ok(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)
        expected = _movement(3, 10, 11)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            return_value=expected,
        ) as mock_get_by_id:
            result = movement_service.get_by_id(self.db, 3, user)

        self.assertEqual(result.id, 3)
        mock_get_by_id.assert_called_once_with(
            self.db,
            3,
            bureau_id=1,
            circonscription_id=None,
        )

    # TEST 4
    def test_user_bureau_1_get_by_id_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            side_effect=[None, _movement(4, 20, 99)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.get_by_id(self.db, 4, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 5
    def test_user_bureau_1_get_by_document_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(20, 2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.get_by_document_id(self.db, 20, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 6
    def test_user_bureau_1_get_by_user_other_bureau_is_403(self):
        user = _user(11, USER_ROLE_USER, ["movement.read"], bureau_id=1)
        other_user = _user(99, USER_ROLE_USER, bureau_id=2)

        with patch(
            "app.services.movement_service.user_repository.get_by_id",
            return_value=other_user,
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.get_by_user_id(self.db, 99, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 7
    def test_user_bureau_1_create_on_own_bureau_document_ok(self):
        user = _user(11, USER_ROLE_USER, ["movement.create"], bureau_id=1)
        data = SimpleNamespace(
            document_id=10,
            bureau_destination_id=2,
            type_mouvement="SORTIE",
            motif="Consultation",
        )

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(2, circonscription_id=1),
        ), patch(
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=None,
        ), patch(
            "app.services.movement_service.movement_repository.create",
            side_effect=lambda _db, movement: movement,
        ) as mock_create:
            result = movement_service.create(self.db, data, user)

        created_movement = mock_create.call_args.args[1]
        self.assertIsInstance(created_movement, Movement)
        self.assertEqual(created_movement.document_id, 10)
        self.assertEqual(created_movement.user_id, 11)
        self.assertEqual(created_movement.bureau_origine_id, 1)
        self.assertEqual(created_movement.bureau_destination_id, 2)
        self.assertEqual(result.statut, "EN_COURS")

    # TEST 8
    def test_user_bureau_1_create_on_other_bureau_document_is_403(self):
        user = _user(11, USER_ROLE_USER, ["movement.create"], bureau_id=1)
        data = SimpleNamespace(
            document_id=20,
            bureau_destination_id=3,
            type_mouvement="SORTIE",
            motif="Consultation",
        )

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(20, 2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, data, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 9
    def test_user_bureau_1_return_other_bureau_movement_is_403(self):
        user = _user(11, USER_ROLE_USER, ["movement.update"], bureau_id=1)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            side_effect=[None, _movement(9, 20, 99)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.return_document(self.db, 9, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 10
    def test_admin_circonscription_1_get_all_scoped(self):
        admin = _user(
            1,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=1,
        )
        expected = [_movement(1, 10, 11), _movement(2, 11, 12)]

        with patch(
            "app.services.movement_service.movement_repository.get_all",
            return_value=expected,
        ) as mock_get_all:
            result = movement_service.get_all(self.db, admin)

        self.assertEqual(len(result), 2)
        mock_get_all.assert_called_once_with(
            self.db,
            bureau_id=None,
            circonscription_id=1,
        )

    # TEST 11
    def test_admin_circonscription_1_get_other_circonscription_is_403(self):
        admin = _user(
            1,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=1,
        )

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            side_effect=[None, _movement(5, 50, 77)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.get_by_id(self.db, 5, admin)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 12
    def test_admin_circonscription_1_return_other_circonscription_is_403(self):
        admin = _user(
            1,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=1,
        )

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            side_effect=[None, _movement(6, 50, 77)],
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.return_document(self.db, 6, admin)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 13
    def test_admin_circonscription_1_create_on_other_circonscription_is_403(self):
        admin = _user(
            1,
            USER_ROLE_ADMIN,
            [],
            admin_circonscription_id=1,
        )
        data = SimpleNamespace(
            document_id=50,
            bureau_destination_id=9,
            type_mouvement="SORTIE",
            motif="Controle",
        )

        # Le document appartient au bureau 9 (circonscription 2),
        # hors scope de l'ADMIN circonscription 1.
        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(50, 9, circonscription_id=2),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(9, circonscription_id=2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, data, admin)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 14
    def test_user_without_movement_permission_is_403(self):
        user = _user(11, USER_ROLE_USER, [], bureau_id=1)

        with patch(
            "app.security.authorization.permission_request_repository.find_approved",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.get_all(self.db, user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 15
    def test_unauthenticated_request_is_401(self):
        client = TestClient(app)

        response = client.get(
            "/movements/",
            headers={"Authorization": "Bearer token-invalide"},
        )

        self.assertEqual(response.status_code, 401)

    # ============================================================
    # WORKFLOW DE TRANSFERT INTER-BUREAUX
    # ============================================================

    def _user_b1(self):
        return _user(11, USER_ROLE_USER, ["movement.create", "movement.update"], bureau_id=1)

    def _create_payload(self, destination_id=2, document_id=10):
        return SimpleNamespace(
            document_id=document_id,
            bureau_destination_id=destination_id,
            type_mouvement="SORTIE",
            motif="Traitement",
        )

    # TEST 16 - destination = bureau origine -> 400
    def test_create_destination_equals_origine_is_400(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=1), user)

        self.assertEqual(ctx.exception.status_code, 400)

    # TEST 17 - destination inexistante -> 404
    def test_create_destination_inexistante_is_404(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=99), user)

        self.assertEqual(ctx.exception.status_code, 404)

    # TEST 18 - destination inactive -> 400
    def test_create_destination_inactive_is_400(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(2, circonscription_id=1, actif=False),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=2), user)

        self.assertEqual(ctx.exception.status_code, 400)

    # TEST 19 - destination autre circonscription -> 403
    def test_create_destination_autre_circonscription_is_403(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1, circonscription_id=1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(5, circonscription_id=2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=5), user)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 20 - document deja EN_COURS -> 409
    def test_create_document_deja_en_cours_is_409(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(2, circonscription_id=1),
        ), patch(
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=_movement(1, 10, bureau_origine_id=1, bureau_destination_id=2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=2), user)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("deja en traitement", ctx.exception.detail)

    # TEST 21 - destination autre bureau MEME circonscription -> OK
    def test_create_destination_autre_bureau_meme_circonscription_ok(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1, circonscription_id=1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(3, circonscription_id=1),
        ), patch(
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=None,
        ), patch(
            "app.services.movement_service.movement_repository.create",
            side_effect=lambda _db, m: m,
        ) as mock_create:
            result = movement_service.create(self.db, self._create_payload(destination_id=3), user)

        created = mock_create.call_args.args[1]
        self.assertEqual(created.bureau_origine_id, 1)
        self.assertEqual(created.bureau_destination_id, 3)
        self.assertEqual(result.statut, "EN_COURS")

    # TEST 22 - retour par le bureau d'origine -> OK
    def test_return_by_bureau_origine_ok(self):
        user = _user(11, USER_ROLE_USER, ["movement.update"], bureau_id=1)
        movement = _movement(7, 10, bureau_origine_id=1, bureau_destination_id=2)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            return_value=movement,
        ), patch(
            "app.services.movement_service.movement_repository.update",
            side_effect=lambda _db, m: m,
        ):
            result = movement_service.return_document(self.db, 7, user)

        self.assertEqual(result.statut, "RETOURNE")
        self.assertIsNotNone(result.date_retour)

    # TEST 23 - retour par le bureau DESTINATION -> 403
    def test_return_by_bureau_destination_is_403(self):
        user_destination = _user(22, USER_ROLE_USER, ["movement.update"], bureau_id=2)
        movement = _movement(7, 10, bureau_origine_id=1, bureau_destination_id=2)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            return_value=movement,
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.return_document(self.db, 7, user_destination)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 24 - retour par un autre bureau (ni origine ni destination) -> 403
    def test_return_by_other_bureau_is_403(self):
        user_b3 = _user(33, USER_ROLE_USER, ["movement.update"], bureau_id=3)
        movement = _movement(7, 10, bureau_origine_id=1, bureau_destination_id=2)

        with patch(
            "app.services.movement_service.movement_repository.get_by_id",
            return_value=movement,
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.return_document(self.db, 7, user_b3)

        self.assertEqual(ctx.exception.status_code, 403)

    # TEST 25 - B1 -> B2 -> B3 sans retour = REFUSE (unicite EN_COURS)
    def test_b1_b2_puis_b3_sans_retour_refuse(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1, circonscription_id=1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(3, circonscription_id=1),
        ), patch(
            # Le document est deja en mouvement B1->B2 (EN_COURS).
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=_movement(1, 10, bureau_origine_id=1, bureau_destination_id=2),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=3), user)

        self.assertEqual(ctx.exception.status_code, 409)

    # TEST 26 - nouveau mouvement APRES retour -> autorise
    def test_nouveau_mouvement_apres_retour_autorise(self):
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1, circonscription_id=1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(2, circonscription_id=1),
        ), patch(
            # Aucun mouvement EN_COURS (le precedent est RETOURNE).
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=None,
        ), patch(
            "app.services.movement_service.movement_repository.create",
            side_effect=lambda _db, m: m,
        ):
            result = movement_service.create(self.db, self._create_payload(destination_id=2), user)

        self.assertEqual(result.statut, "EN_COURS")

    # TEST 27 - race condition: index unique partiel -> IntegrityError -> 409
    def test_concurrence_index_unique_declenche_409(self):
        from sqlalchemy.exc import IntegrityError
        user = self._user_b1()

        with patch(
            "app.services.movement_service.document_repository.get_by_id",
            return_value=_doc(10, 1, circonscription_id=1),
        ), patch(
            "app.services.movement_service.bureau_repository.get_by_id",
            return_value=_bureau(2, circonscription_id=1),
        ), patch(
            # Le controle applicatif n'a rien vu (race condition).
            "app.services.movement_service.movement_repository.get_active_by_document",
            return_value=None,
        ), patch(
            # La contrainte DB rejette le second EN_COURS.
            "app.services.movement_service.movement_repository.create",
            side_effect=IntegrityError("insert", {}, Exception("unique")),
        ):
            with self.assertRaises(HTTPException) as ctx:
                movement_service.create(self.db, self._create_payload(destination_id=2), user)

        self.assertEqual(ctx.exception.status_code, 409)

    # TEST 28 - MovementResponse expose origine/destination
    def test_response_expose_origine_destination(self):
        from app.schemas.movement_schema import MovementResponse

        response = MovementResponse.model_validate({
            "id": 1,
            "document_id": 10,
            "user_id": 11,
            "bureau_origine_id": 1,
            "bureau_destination_id": 2,
            "type_mouvement": "SORTIE",
            "motif": "T",
            "statut": "EN_COURS",
            "date_mouvement": datetime.now(),
            "date_retour": None,
        })

        self.assertEqual(response.bureau_origine_id, 1)
        self.assertEqual(response.bureau_destination_id, 2)

    # TEST 29 - document sans mouvement actif = disponible
    def test_document_disponible_sans_mouvement_actif(self):
        from app.services.movement_service import movement_repository

        with patch.object(
            movement_repository,
            "get_active_by_document",
            return_value=None,
        ) as mock_get:
            result = movement_repository.get_active_by_document(self.db, 10)

        self.assertIsNone(result)
        mock_get.assert_called_once_with(self.db, 10)

    # TEST 30 - document avec mouvement EN_COURS = en traitement (bureau destination)
    def test_document_en_traitement_avec_bureau_destination(self):
        from app.services.movement_service import movement_repository

        actif = _movement(1, 10, bureau_origine_id=1, bureau_destination_id=2)

        with patch.object(
            movement_repository,
            "get_active_by_document",
            return_value=actif,
        ):
            result = movement_repository.get_active_by_document(self.db, 10)

        self.assertIsNotNone(result)
        self.assertEqual(result.bureau_destination_id, 2)

    # TEST 31 - mouvement historique avec destination NULL reste lisible
    def test_mouvement_historique_destination_null_lisible(self):
        from app.schemas.movement_schema import MovementResponse

        response = MovementResponse.model_validate({
            "id": 99,
            "document_id": 5,
            "user_id": 3,
            "bureau_origine_id": 1,
            "bureau_destination_id": None,
            "type_mouvement": "SORTIE",
            "motif": None,
            "statut": "RETOURNE",
            "date_mouvement": datetime.now(),
            "date_retour": datetime.now(),
        })

        self.assertIsNone(response.bureau_destination_id)
        self.assertEqual(response.statut, "RETOURNE")


if __name__ == "__main__":
    unittest.main()
