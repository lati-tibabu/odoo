# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from .inventory_base import InventoryBaseController


class InventoryContextProductsController(InventoryBaseController):
    """Controller for context and products endpoints."""

    # -----------------
    # 1) Context
    # -----------------

    @http.route('/api/v1/inventory/context', type='http', auth='user', cors='*', methods=['GET'], csrf=False, save_session=False, readonly=True)
    def inventory_context(self, **_kwargs):
        self._require_api_group()

        company = request.env.company
        warehouse = self._current_warehouse()
        allowed_locations = self._allowed_internal_locations(warehouse)

        payload = {
            'company': {'id': company.id, 'name': company.name},
            'warehouse': {'id': warehouse.id, 'name': warehouse.name, 'code': warehouse.code},
            'allowed_locations': [
                {
                    'id': loc.id,
                    'name': loc.name,
                    'complete_name': loc.complete_name,
                }
                for loc in allowed_locations
            ],
            'capabilities': self._capabilities(),
        }
        return self._json(payload)

    # -----------------
    # 2) Products
    # -----------------

    @http.route('/api/v1/inventory/products', type='http', auth='user', methods=['GET'], csrf=False, save_session=False, readonly=True)
    def inventory_products(self, **_kwargs):
        self._require_api_group()
        self._require_capability('read')

        limit = self._get_int_param('limit', default=200)
        if limit < 1 or limit > 2000:
            self._bad_request('limit must be between 1 and 2000')

        include_images = self._get_bool_param('include_images', default=False)
        image_size = self._get_image_size_param('image_size', default=128)

        Product = request.env['product.product']
        products = Product.search([
            ('type', '!=', 'service'),
        ], limit=limit, order='id')

        payload = {
            'items': [
                self._product_payload(p, include_images=include_images, image_size=image_size)
                for p in products
            ],
        }
        return self._json(payload)

    @http.route('/api/v1/inventory/products/<int:product_id>', type='http', auth='user', methods=['GET'], csrf=False, save_session=False, readonly=True)
    def inventory_product_detail(self, product_id, **_kwargs):
        self._require_api_group()
        self._require_capability('read')

        product = self._resolve_product(product_id)

        include_images = self._get_bool_param('include_images', default=False)
        image_size = self._get_image_size_param('image_size', default=128)

        return self._json({
            'product': self._product_detail_payload(product, include_images=include_images, image_size=image_size),
        })

    @http.route('/api/v1/inventory/products', type='http', auth='user', methods=['POST'], csrf=False, save_session=False)
    def inventory_products_create(self, **_kwargs):
        self._require_api_group()
        self._require_capability('product_create')

        body = self._get_json_body()
        name = self._clean_str(body.get('name'), 'name')
        if not name:
            self._bad_request('name is required')

        product_type = self._clean_str(body.get('type'), 'type') or 'consu'
        if product_type not in {'consu', 'service', 'combo'}:
            self._bad_request("type must be one of: consu, service, combo")
        if product_type == 'service':
            self._bad_request('Service products are not inventory-relevant')

        vals = {
            'name': name,
            'type': product_type,
            'company_id': body.get('company_id') if body.get('company_id') is not None else request.env.company.id,
        }

        # Optional fields
        default_code = self._clean_str(body.get('default_code') or body.get('code'), 'default_code')
        if default_code is not None:
            vals['default_code'] = default_code

        barcode = self._clean_str(body.get('barcode'), 'barcode')
        if barcode is not None:
            vals['barcode'] = barcode

        if body.get('categ_id') is not None:
            vals['categ_id'] = int(body.get('categ_id'))

        if body.get('uom_id') is not None:
            vals['uom_id'] = int(body.get('uom_id'))
        if body.get('uom_po_id') is not None:
            vals['uom_po_id'] = int(body.get('uom_po_id'))

        if body.get('sale_ok') is not None:
            vals['sale_ok'] = bool(body.get('sale_ok'))
        if body.get('purchase_ok') is not None:
            vals['purchase_ok'] = bool(body.get('purchase_ok'))
        if body.get('active') is not None:
            vals['active'] = bool(body.get('active'))

        if body.get('list_price') is not None:
            vals['list_price'] = self._float_qty_allow_zero(body.get('list_price'), 'list_price')
        if body.get('weight') is not None:
            vals['weight'] = self._float_qty_allow_zero(body.get('weight'), 'weight')
        if body.get('volume') is not None:
            vals['volume'] = self._float_qty_allow_zero(body.get('volume'), 'volume')

        image_1920 = body.get('image_1920')
        if image_1920 is None and isinstance(body.get('image'), dict):
            image_1920 = body.get('image', {}).get('data')
        if image_1920 is None and isinstance(body.get('image'), str):
            image_1920 = body.get('image')
        if image_1920 is not None:
            vals['image_1920'] = image_1920

        Template = request.env['product.template']
        template = Template.create(vals)
        product = template.product_variant_id
        if not product:
            self._bad_request('Failed to create product variant')

        include_images = self._get_bool_param('include_images', default=False)
        image_size = self._get_image_size_param('image_size', default=128)

        return self._json(
            {'product': self._product_payload(product, include_images=include_images, image_size=image_size)},
            status=201,
        )
    @http.route('/api/v1/inventory/products/<int:product_id>', type='http', auth='user', methods=['PUT', 'PATCH'], csrf=False, save_session=False)
    def inventory_products_update(self, product_id, **_kwargs):
        self._require_api_group()
        self._require_capability('product_create')

        product = self._resolve_product(product_id)
        body = self._get_json_body()

        vals = {}

        name = self._clean_str(body.get('name'), 'name')
        if name is not None:
            vals['name'] = name

        product_type = self._clean_str(body.get('type'), 'type')
        if product_type:
            if product_type not in {'consu', 'service', 'combo'}:
                self._bad_request("type must be one of: consu, service, combo")
            if product_type == 'service':
                self._bad_request('Service products are not inventory-relevant')
            vals['type'] = product_type

        default_code = self._clean_str(body.get('default_code') or body.get('code'), 'default_code')
        if default_code is not None:
            vals['default_code'] = default_code

        barcode = self._clean_str(body.get('barcode'), 'barcode')
        if barcode is not None:
            vals['barcode'] = barcode

        if body.get('categ_id') is not None:
            vals['categ_id'] = int(body.get('categ_id'))

        if body.get('company_id') is not None:
            vals['company_id'] = int(body.get('company_id'))

        if body.get('uom_id') is not None:
            vals['uom_id'] = int(body.get('uom_id'))
        if body.get('uom_po_id') is not None:
            vals['uom_po_id'] = int(body.get('uom_po_id'))

        if body.get('sale_ok') is not None:
            vals['sale_ok'] = bool(body.get('sale_ok'))
        if body.get('purchase_ok') is not None:
            vals['purchase_ok'] = bool(body.get('purchase_ok'))
        if body.get('active') is not None:
            vals['active'] = bool(body.get('active'))

        if body.get('list_price') is not None:
            vals['list_price'] = self._float_qty_allow_zero(body.get('list_price'), 'list_price')
        if body.get('weight') is not None:
            vals['weight'] = self._float_qty_allow_zero(body.get('weight'), 'weight')
        if body.get('volume') is not None:
            vals['volume'] = self._float_qty_allow_zero(body.get('volume'), 'volume')

        image_1920 = body.get('image_1920')
        if image_1920 is None and isinstance(body.get('image'), dict):
            image_1920 = body.get('image', {}).get('data')
        if image_1920 is None and isinstance(body.get('image'), str):
            image_1920 = body.get('image')
        if image_1920 is not None:
            vals['image_1920'] = image_1920

        if vals:
            product.write(vals)

        include_images = self._get_bool_param('include_images', default=False)
        image_size = self._get_image_size_param('image_size', default=128)

        return self._json({
            'product': self._product_detail_payload(product, include_images=include_images, image_size=image_size),
        })

    @http.route('/api/v1/inventory/products/<int:product_id>', type='http', auth='user', methods=['DELETE'], csrf=False, save_session=False)
    def inventory_products_delete(self, product_id, **_kwargs):
        self._require_api_group()
        self._require_capability('product_create')

        product = self._resolve_product(product_id)
        product.unlink()

        return self._json({'message': 'Product deleted successfully'}, status=200)
