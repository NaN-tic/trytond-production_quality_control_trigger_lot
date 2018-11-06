# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta

from trytond.modules.quality_control_trigger.quality import QualityControlTriggerMixin

__all__ = ['QualityTemplate', 'Production']


class QualityTemplate(metaclass=PoolMeta):
    __name__ = 'quality.template'

    @classmethod
    def _get_trigger_generation_models_by_trigger_models(cls):
        models = super(QualityTemplate,
            cls)._get_trigger_generation_models_by_trigger_models()
        generated_models = models.setdefault('production', [])
        if 'stock.lot' not in generated_models:
            generated_models.append('stock.lot')
        return models


class Production(QualityControlTriggerMixin, metaclass=PoolMeta):
    __name__ = 'production'

    @classmethod
    def done(cls, productions):
        super(Production, cls).done(productions)
        cls.create_quality_tests(productions, 'stock.lot')

    def _get_quality_trigger_generation_instances(self, template):
        if template.trigger_generation_model != 'stock.lot':
            return super(Production,
                self)._get_quality_trigger_generation_instances(template)
        return set(m.lot for m in self.outputs
            if m.state == 'done' and m.product == template.document and m.lot)
