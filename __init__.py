# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .production import *


def register():
    Pool.register(
        QualityTemplate,
        Production,
        module='production_quality_control_trigger_lot', type_='model')
