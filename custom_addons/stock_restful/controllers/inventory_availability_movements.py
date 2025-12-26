# -*- coding: utf-8 -*-
from odoo import fields, http
from odoo.http import request

from .inventory_base import InventoryBaseController


class InventoryAvailabilityMovementsController(InventoryBaseController):
    """Controller for availability and movements endpoints."""

    # -----------------
    # 3) Availability
    # -----------------

    @http.route('/api/v1/inventory/availability', type='http', auth='user', methods=['GET'], csrf=False, save_session=False, readonly=True)
    def inventory_availability(self, **_kwargs):
        self._require_api_group()
        self._require_capability('read')

        warehouse_id = self._get_int_param('warehouse_id')
        location_id = self._get_int_param('location_id')
        if warehouse_id and location_id:
            self._bad_request('Provide either warehouse_id or location_id, not both')

        product_ids = self._get_csv_ints('product_ids')
        limit = self._get_int_param('limit', default=200)
        if limit < 1 or limit > 2000:
            self._bad_request('limit must be between 1 and 2000')

        Product = request.env['product.product']
        if product_ids:
            products = Product.browse(product_ids).exists().filtered(lambda p: p.type != 'service')
        else:
            products = Product.search([('type', '!=', 'service')], limit=limit, order='id')

        ctx = dict(request.env.context)
        scope = {}
        if warehouse_id:
            wh = self._resolve_warehouse(warehouse_id)
            ctx['warehouse_id'] = wh.id
            scope['warehouse'] = {'id': wh.id, 'name': wh.name, 'code': wh.code}
        elif location_id:
            loc = self._resolve_internal_location(location_id)
            wh = self._current_warehouse()
            allowed = self._allowed_internal_locations(wh)
            self._ensure_allowed_location(loc, allowed)
            ctx['location'] = loc.id
            scope['location'] = {'id': loc.id, 'name': loc.complete_name}
        else:
            wh = self._current_warehouse()
            scope['warehouse'] = {'id': wh.id, 'name': wh.name, 'code': wh.code}

        products_ctx = products.with_context(**ctx)
        quantities = products_ctx._compute_quantities_dict(None, None, None)

        items = []
        for p in products_ctx:
            q = quantities.get(p.id, {})
            on_hand = q.get('qty_available', 0.0)
            available = q.get('free_qty', 0.0)
            reserved = on_hand - available
            items.append({
                'product': {
                    'id': p.id,
                    'name': p.display_name,
                    'code': p.default_code,
                    'barcode': p.barcode,
                    'tracking': p.tracking or 'none',
                    'uom': {'id': p.uom_id.id, 'name': p.uom_id.name},
                },
                'on_hand_qty': on_hand,
                'available_qty': available,
                'reserved_qty': reserved,
            })

        return self._json({'scope': scope, 'items': items})

    # -----------------
    # 4) Movements (read-only)
    # -----------------

    @http.route('/api/v1/inventory/movements', type='http', auth='user', methods=['GET'], csrf=False, save_session=False, readonly=True)
    def inventory_movements(self, **_kwargs):
        self._require_api_group()
        self._require_capability('read')

        limit = self._get_int_param('limit', default=100)
        if limit < 1 or limit > 1000:
            self._bad_request('limit must be between 1 and 1000')

        warehouse_id = self._get_int_param('warehouse_id')
        location_id = self._get_int_param('location_id')
        if warehouse_id and location_id:
            self._bad_request('Provide either warehouse_id or location_id, not both')

        product_ids = self._get_csv_ints('product_ids')

        Move = request.env['stock.move']
        domain = []
        if product_ids:
            domain.append(('product_id', 'in', product_ids))

        scope_locations = None
        scope = {}
        if warehouse_id:
            wh = self._resolve_warehouse(warehouse_id)
            scope_locations = request.env['stock.location'].search([
                ('id', 'child_of', wh.view_location_id.id),
            ])
            scope['warehouse'] = {'id': wh.id, 'name': wh.name, 'code': wh.code}
        elif location_id:
            wh = self._current_warehouse()
            allowed = self._allowed_internal_locations(wh)
            loc = self._resolve_internal_location(location_id)
            self._ensure_allowed_location(loc, allowed)
            scope_locations = request.env['stock.location'].search([
                ('id', 'child_of', loc.id),
            ])
            scope['location'] = {'id': loc.id, 'name': loc.complete_name}

        if scope_locations is not None:
            domain += ['|', ('location_id', 'in', scope_locations.ids), ('location_dest_id', 'in', scope_locations.ids)]

        moves = Move.search(domain, order='date desc, id desc', limit=limit)

        items = []
        for m in moves:
            qty = m.quantity if m.state == 'done' else m.product_uom_qty
            items.append({
                'id': m.id,
                'date': fields.Datetime.to_string(m.date),
                'direction': self._direction(m.location_id, m.location_dest_id),
                'product': {
                    'id': m.product_id.id,
                    'name': m.product_id.display_name,
                    'code': m.product_id.default_code,
                    'barcode': m.product_id.barcode,
                    'tracking': m.product_id.tracking or 'none',
                    'uom': {'id': m.product_uom.id, 'name': m.product_uom.name},
                },
                'quantity': qty,
                'source': {'id': m.location_id.id, 'name': m.location_id.complete_name},
                'destination': {'id': m.location_dest_id.id, 'name': m.location_dest_id.complete_name},
                'state': m.state,
                'reference': m.reference or (m.picking_id.name if m.picking_id else None) or m.origin,
                'picking': {
                    'id': m.picking_id.id,
                    'name': m.picking_id.name,
                } if m.picking_id else None,
            })

        return self._json({'scope': scope, 'items': items})