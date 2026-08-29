from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.models.document import Document
from app.models.attachment import DocumentAttachment
from app.models.document_type import DocumentType
from app.models.phase import Phase
from app.models.circonscription import Circonscription

from app.security.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ============================================================
    # DOCUMENTS ACTIFS
    # ============================================================

    total_documents = (
        db.query(func.count(Document.id))
        .filter(
            Document.is_deleted == False
        )
        .scalar()
        or 0
    )


    # ============================================================
    # PIECES JOINTES
    # ============================================================

    total_attachments = (
        db.query(
            func.count(DocumentAttachment.id)
        )
        .scalar()
        or 0
    )


    # ============================================================
    # TYPES
    # ============================================================

    total_types = (
        db.query(
            func.count(DocumentType.id)
        )
        .scalar()
        or 0
    )


    # ============================================================
    # NATURES
    # ============================================================

    total_phases = (
        db.query(
            func.count(Phase.id)
        )
        .scalar()
        or 0
    )


    # ============================================================
    # CIRCONSCRIPTIONS
    # ============================================================

    total_circonscriptions = (
        db.query(
            func.count(Circonscription.id)
        )
        .scalar()
        or 0
    )


    # ============================================================
    # DOCUMENTS PAR TYPE
    # ============================================================

    documents_by_type = (

        db.query(
            DocumentType.id,
            DocumentType.libelle,
            func.count(Document.id).label(
                "total"
            ),
        )

        .outerjoin(
            Document,
            (
                Document.type_document_id
                == DocumentType.id
            )
            & (
                Document.is_deleted == False
            ),
        )

        .group_by(
            DocumentType.id,
            DocumentType.libelle,
        )

        .order_by(
            DocumentType.id
        )

        .all()

    )


    # ============================================================
    # DOCUMENTS PAR NATURE
    # ============================================================

    documents_by_nature = (

        db.query(
            Phase.id,
            Phase.libelle,
            func.count(Document.id).label(
                "total"
            ),
        )

        .outerjoin(
            Document,
            (
                Document.phase_id
                == Phase.id
            )
            & (
                Document.is_deleted == False
            ),
        )

        .group_by(
            Phase.id,
            Phase.libelle,
        )

        .order_by(
            Phase.id
        )

        .all()

    )


    # ============================================================
    # DOCUMENTS PAR CIRCONSCRIPTION
    # ============================================================

    documents_by_circonscription = (

        db.query(
            Circonscription.id,
            Circonscription.nom,
            func.count(Document.id).label(
                "total"
            ),
        )

        .outerjoin(
            Document,
            (
                Document.circonscription_id
                == Circonscription.id
            )
            & (
                Document.is_deleted == False
            ),
        )

        .group_by(
            Circonscription.id,
            Circonscription.nom,
        )

        .order_by(
            Circonscription.id
        )

        .all()

    )


    # ============================================================
    # DERNIERS DOCUMENTS
    # ============================================================

    recent_documents = (

        db.query(Document)

        .filter(
            Document.is_deleted == False
        )

        .order_by(
            Document.created_at.desc()
        )

        .limit(5)

        .all()

    )


    # ============================================================
    # REPONSE
    # ============================================================

    return {

        "summary": {

            "total_documents":
                total_documents,

            "total_attachments":
                total_attachments,

            "total_types":
                total_types,

            "total_natures":
                total_phases,

            "total_circonscriptions":
                total_circonscriptions,

        },


        "documents_by_type": [

            {
                "id": item.id,
                "libelle": item.libelle,
                "total": item.total,
            }

            for item in documents_by_type

        ],


        "documents_by_nature": [

            {
                "id": item.id,
                "libelle": item.libelle,
                "total": item.total,
            }

            for item in documents_by_nature

        ],


        "documents_by_circonscription": [

            {
                "id": item.id,
                "nom": item.nom,
                "total": item.total,
            }

            for item in documents_by_circonscription

        ],


        "recent_documents": [

            {
                "id": document.id,

                "reference_archive":
                    document.reference_archive,

                "nom_document":
                    document.nom_document,

                "date_creation":
                    document.date_creation,

                "created_at":
                    document.created_at,

                "type_document_id":
                    document.type_document_id,

                "phase_id":
                    document.phase_id,

                "circonscription_id":
                    document.circonscription_id,

            }

            for document in recent_documents

        ],

    }