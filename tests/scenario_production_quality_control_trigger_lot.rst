=============================================
Quality Control by Lot on Production Scenario
=============================================

=============
General Setup
=============

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()

Install stock_number_of_packages Module::

    >>> config = activate_modules('production_quality_control_trigger_lot')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> product1 = Product()
    >>> template1 = ProductTemplate()
    >>> template1.name = 'Product 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal('20')
    >>> template1.producible = True
    >>> template1.save()
    >>> product1.template = template1
    >>> product1.cost_price = Decimal('8')
    >>> product1.save()
    >>> product2 = Product()
    >>> template2 = ProductTemplate()
    >>> template2.name = 'Product 2'
    >>> template2.default_uom = unit
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal('20')
    >>> template2.producible = True
    >>> template2.save()
    >>> product2.template = template2
    >>> product2.cost_price = Decimal('8')
    >>> product2.save()

Create Components::

    >>> component1 = Product()
    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> template1.save()
    >>> component1.template = template1
    >>> component1.cost_price = Decimal(1)
    >>> component1.save()

    >>> meter, = ProductUom.find([('name', '=', 'Meter')])
    >>> centimeter, = ProductUom.find([('name', '=', 'centimeter')])
    >>> component2 = Product()
    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> template2.save()
    >>> component2.template = template2
    >>> component2.cost_price = Decimal(5)
    >>> component2.save()

Create Bill of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 150
    >>> input2.uom = centimeter
    >>> output1 = BOMOutput()
    >>> bom.outputs.append(output1)
    >>> output1.product = product1
    >>> output1.quantity = 1
    >>> #output2 = BOMOutput()
    >>> #bom.outputs.append(output2)
    >>> #output2.product = product2
    >>> #output2.quantity = 1
    >>> bom.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product1.boms.append(ProductBom(bom=bom))
    >>> product1.save()

Create Quality Configuration::

    >>> Sequence = Model.get('ir.sequence')
    >>> Configuration = Model.get('quality.configuration')
    >>> ConfigLine = Model.get('quality.configuration.line')
    >>> IrModel = Model.get('ir.model')
    >>> sequence = Sequence.find([('code','=','quality.test')])[0]
    >>> product_model, = IrModel.find([('model','=','product.product')])
    >>> lot_model, = IrModel.find([('model','=','stock.lot')])
    >>> configuration = Configuration()
    >>> product_config_line = ConfigLine()
    >>> configuration.allowed_documents.append(product_config_line)
    >>> product_config_line.quality_sequence = sequence
    >>> product_config_line.document = product_model
    >>> lot_config_line = ConfigLine()
    >>> configuration.allowed_documents.append(lot_config_line)
    >>> lot_config_line.quality_sequence = sequence
    >>> lot_config_line.document = lot_model
    >>> configuration.save()

Create Templates related to Product 1 with Production as Trigger model and
Lot as generated model::

    >>> Template = Model.get('quality.template')
    >>> template = Template()
    >>> template.name = 'Template Productions'
    >>> template.document = product1
    >>> template.internal_description='Quality Control on Productions'
    >>> template.external_description='External description'
    >>> template.trigger_model = 'production'
    >>> template.trigger_generation_model = 'stock.lot'
    >>> template.save()

Create an Inventory for components::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 10
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 5
    >>> inventory.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    'done'

Create a production and set to waiting and then try to assign::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product1
    >>> production.bom = bom
    >>> production.quantity = 2
    >>> sorted([i.quantity for i in production.inputs]) == [10, 300]
    True
    >>> production.save()
    >>> Production.wait([production.id], config.context)
    >>> production.state
    'waiting'
    >>> Production.assign_try([production.id], config.context)
    True
    >>> production.reload()
    >>> all(i.state == 'assigned' for i in production.inputs)
    True

Create two Lots, one for each output products, and set to output moves::

    >>> Lot = Model.get('stock.lot')
    >>> lot_by_product = {}
    >>> for i, move in enumerate(production.outputs):
    ...     lot = Lot(number='%s' % i)
    ...     lot.product = move.product
    ...     lot.save()
    ...     move.lot = lot
    ...     move.save()
    ...     lot_by_product[move.product.id] = lot

Run and set to done state the production::

    >>> Production.run([production.id], config.context)
    >>> production.reload()
    >>> all(i.state == 'done' for i in production.inputs)
    True
    >>> Production.done([production.id], config.context)
    >>> production.reload()
    >>> all(o.state == 'done' for o in production.outputs)
    True

Check the created Quality Tests::

    >>> QualityTest = Model.get('quality.test')
    >>> tests = QualityTest.find([])
    >>> len(tests)
    1
    >>> tests[0].document == lot_by_product[product1.id]
    True
