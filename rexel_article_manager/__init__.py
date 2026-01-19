# -*- coding: utf-8 -*-

from . import models
from . import wizard


def _post_init_hook(env):
    """
    Hook exécuté après l'installation du module.
    Initialise les correspondances conditionnement → unité par défaut.
    """
    env['rexel.unit.mapping'].init_default_mappings()
