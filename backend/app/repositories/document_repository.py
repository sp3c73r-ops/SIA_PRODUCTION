from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models.document import Document
from app.models.document_field_value import DocumentFieldValue


class DocumentRepository:

    # ============================================================
    # CREATION
    # ============================================================

    def create(
        self,
        db: Session,
        document: Document,
        commit: bool = True,
    ):
        db.add(document)

        if commit:
            db.commit()
            db.refresh(document)
        else:
            db.flush()

        return document

    # ============================================================
    # LISTE
    # ============================================================

    def get_all(
        self,
        db: Session,
        bureau_id: Optional[int] = None,
    ):
        query = (
            db.query(Document)
            .options(
                selectinload(Document.encodeur),
                selectinload(Document.custom_field_values)
                .selectinload(DocumentFieldValue.document_field)
            )
            .filter(
                Document.is_deleted == False
            )
        )

        if bureau_id is not None:
            query = query.filter(
                Document.bureau_id == bureau_id
            )

        return (
            query
            .order_by(
                Document.id.desc()
            )
            .all()
        )

    # ============================================================
    # RECHERCHE AVANCEE
    # ============================================================

    def search(
        self,
        db: Session,
        bureau_id: Optional[int] = None,
        reference_archive: Optional[str] = None,
        nom_document: Optional[str] = None,
        code_foncier: Optional[str] = None,
        numero_ordre: Optional[str] = None,
        type_document_id: Optional[int] = None,
        phase_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        scope_circonscription_id: Optional[int] = None,
        date_debut=None,
        date_fin=None,
    ):

        query = (
            db.query(Document)
            .options(
                selectinload(Document.encodeur),
                selectinload(Document.custom_field_values)
                .selectinload(DocumentFieldValue.document_field)
            )
            .filter(
                Document.is_deleted == False
            )
        )

        if bureau_id is not None:
            query = query.filter(
                Document.bureau_id == bureau_id
            )

        # --------------------------------------------------------
        # REFERENCE ARCHIVE
        # --------------------------------------------------------

        if reference_archive:
            query = query.filter(
                Document.reference_archive.ilike(
                    f"%{reference_archive}%"
                )
            )

        # --------------------------------------------------------
        # NOM DOCUMENT
        # --------------------------------------------------------

        if nom_document:
            query = query.filter(
                Document.nom_document.ilike(
                    f"%{nom_document}%"
                )
            )

        # --------------------------------------------------------
        # COTE FONCIER
        # --------------------------------------------------------

        if code_foncier:
            query = query.filter(
                Document.code_foncier.ilike(
                    f"%{code_foncier}%"
                )
            )

        # --------------------------------------------------------
        # NUMCAD / REFERENCE / INDICE
        # --------------------------------------------------------

        if numero_ordre:
            query = query.filter(
                Document.numero_ordre.ilike(
                    f"%{numero_ordre}%"
                )
            )

        # --------------------------------------------------------
        # TYPE
        # --------------------------------------------------------

        if type_document_id is not None:
            query = query.filter(
                Document.type_document_id
                == type_document_id
            )

        # --------------------------------------------------------
        # NATURE
        # --------------------------------------------------------

        if phase_id is not None:
            query = query.filter(
                Document.phase_id
                == phase_id
            )

        # --------------------------------------------------------
        # CIRCONSCRIPTION
        # --------------------------------------------------------

        if circonscription_id is not None:
            query = query.filter(
                Document.circonscription_id
                == circonscription_id
            )

        # --------------------------------------------------------
        # SCOPE CIRCONSCRIPTION (ADMIN)
        # --------------------------------------------------------

        if scope_circonscription_id is not None:
            query = query.filter(
                Document.circonscription_id
                == scope_circonscription_id
            )

        # --------------------------------------------------------
        # DATE DEBUT
        # --------------------------------------------------------

        if date_debut:
            query = query.filter(
                Document.date_creation
                >= date_debut
            )

        # --------------------------------------------------------
        # DATE FIN
        # --------------------------------------------------------

        if date_fin:
            query = query.filter(
                Document.date_creation
                <= date_fin
            )

        return (
            query
            .order_by(
                Document.id.desc()
            )
            .all()
        )

    # ============================================================
    # PAR ID
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        document_id: int,
        bureau_id: Optional[int] = None,
    ):

        query = (
            db.query(Document)
            .options(
                selectinload(Document.custom_field_values)
                .selectinload(DocumentFieldValue.document_field)
            )
            .filter(
                Document.id == document_id
            )
        )

        if bureau_id is not None:
            query = query.filter(
                Document.bureau_id == bureau_id
            )

        return query.first()

    # ============================================================
    # MODIFICATION
    # ============================================================

    def update(
        self,
        db: Session,
        document: Document,
    ):

        db.commit()
        db.refresh(document)

        return document

    # ============================================================
    # SUPPRESSION LOGIQUE
    # ============================================================

    def delete(
        self,
        db: Session,
        document: Document,
    ):

        document.is_deleted = True

        db.commit()

        return True


document_repository = DocumentRepository()