# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools import float_compare

from .inventory_base import InventoryBaseController


class InventoryTransferAdjustController(InventoryBaseController):
    """Controller for transfer and adjust endpoints."""

    # -----------------
    # 7) Internal Transfer
    # -----------------

    @http.route('/api/v1/inventory/transfer', type='http', auth='user', methods=['POST'], csrf=False, save_session=False)
    def inventory_transfer(self, **_kwargs):
        self._require_api_group()
        self._require_capability('move')

        body = self._get_json_body()
        lines = body.get('lines')
        if not isinstance(lines, list) or not lines:
            self._bad_request('lines must be a non-empty list')

        warehouse = self._resolve_warehouse(body.get('warehouse_id'))
        source_location = self._resolve_internal_location(body.get('source_location_id'))
        dest_location = self._resolve_internal_location(body.get('destination_location_id'))

        allowed = self._allowed_internal_locations(warehouse)
        self._ensure_allowed_location(source_location, allowed)
        self._ensure_allowed_location(dest_location, allowed)

        picking_type = warehouse.int_type_id
        if not picking_type:
            self._bad_request('Warehouse has no internal picking type configured')

        reference = (body.get('reference') or body.get('origin') or '').strip() or None

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'origin': reference,
        }

        move_vals_list = []
        tracking_lines = []
        for line in lines:
            product = self._resolve_product(line.get('product_id'))
            qty = self._float_qty(line.get('quantity'), 'quantity')
            uom = self._uom_from_line(product, line)
            self._validate_available_qty(product, source_location, qty, uom=uom)
            move_vals_list.append({
                'name': product.display_name,
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': uom.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
            })
            tracking_lines.append((product, line))

        picking, moves = self._create_and_done_picking(
            picking_vals,
            move_vals_list,
            tracking_lines,
            allow_create_lot=False,
        )

        return self._json({
            'picking': {'id': picking.id, 'name': picking.name, 'state': picking.state},
            'moves': [{'id': m.id, 'product_id': m.product_id.id, 'state': m.state} for m in moves],
        }, status=201)

    # -----------------
    # 8) Inventory Adjust
    # -----------------

    @http.route('/api/v1/inventory/adjust', type='http', auth='user', methods=['POST'], csrf=False, save_session=False)
    def inventory_adjust(self, **_kwargs):
        self._require_api_group()
        self._require_capability('adjust')

        body = self._get_json_body()
        reason = (body.get('reason') or '').strip()
        if not reason:
            self._bad_request('reason is required')

        warehouse = self._resolve_warehouse(body.get('warehouse_id'))
        location = self._resolve_internal_location(body.get('location_id'))
        allowed = self._allowed_internal_locations(warehouse)
        self._ensure_allowed_location(location, allowed)

        product = self._resolve_product(body.get('product_id'))
        new_qty = self._float_qty_allow_zero(body.get('new_quantity'), 'new_quantity')

        # Compute current on-hand at this location.
        current_qty = product.with_context(location=location.id).qty_available
        diff = new_qty - current_qty

        if float_compare(diff, 0.0, precision_rounding=product.uom_id.rounding) == 0:
            return self._json({
                'message': 'No adjustment needed',
                'current_quantity': current_qty,
                'new_quantity': new_qty,
            })

        picking_type = warehouse.int_type_id
        if not picking_type:
            self._bad_request('Warehouse has no internal picking type configured')

        inventory_loc = request.env.ref('stock.stock_location_inventory')

        if diff > 0:
            src = inventory_loc
            dst = location
            qty = diff
        else:
            src = location
            dst = inventory_loc
            qty = abs(diff)
            self._validate_available_qty(product, location, qty)

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': src.id,
            'location_dest_id': dst.id,
            'origin': reason,
        }

        move_vals_list = [{
            'name': f"Inventory adjustment: {reason}",
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dst.id,
        }]

        tracking_lines = [(product, {'quantity': qty} | ({'lot_name': body.get('lot_name')} if body.get('lot_name') else {}) | ({'serials': body.get('serials')} if body.get('serials') else {}))]

        picking, moves = self._create_and_done_picking(
            picking_vals,
            move_vals_list,
            tracking_lines,
            allow_create_lot=False,
        )

        return self._json({
            'picking': {'id': picking.id, 'name': picking.name, 'state': picking.state},
            'move': {'id': moves[0].id, 'state': moves[0].state},
            'current_quantity': current_qty,
            'new_quantity': new_qty,
        }, status=201)