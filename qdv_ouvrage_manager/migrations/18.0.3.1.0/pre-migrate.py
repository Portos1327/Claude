# -*- coding: utf-8 -*-
"""
Migration 3.0 → 3.1 : suppression des vues obsolètes/corrompues en base.
Exécuté AVANT le chargement des vues pour éviter les erreurs de validation.

Vues supprimées :
- qdv_picker_article_wizard_view  : contenait tarif_result_ids (modèle externe)
- qdv_ouvrage_minute_list         : manquait is_new pour decoration-info
- qdv.article.catalogue / qdv.article : modèles supprimés en v3.1
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):

    # 1. Toutes les vues du module qdv_ouvrage_manager — Odoo les recrée depuis les fichiers
    cr.execute("""
        SELECT COUNT(*) FROM ir_ui_view
        WHERE module = 'qdv_ouvrage_manager'
    """)
    total = cr.fetchone()[0]

    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE module = 'qdv_ouvrage_manager'
    """)
    deleted = cr.rowcount
    _logger.info(
        "Migration 3.1: %d/%d vue(s) supprimée(s) — seront recrées depuis les fichiers",
        deleted, total
    )

    # 2. Supprimer aussi les vues des modèles supprimés (pas de module tag)
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model IN ('qdv.article.catalogue', 'qdv.article')
    """)
    deleted2 = cr.rowcount
    if deleted2:
        _logger.info("Migration 3.1: %d vue(s) catalogue obsolète(s) supprimée(s)", deleted2)

    # 3. Supprimer les droits des modèles supprimés
    cr.execute("""
        DELETE FROM ir_model_access
        WHERE name IN (
            'qdv.article.catalogue user',
            'qdv.article user',
            'qdv.import.catalogue.wizard'
        )
    """)
