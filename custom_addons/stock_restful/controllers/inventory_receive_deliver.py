# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from .inventory_base import InventoryBaseController


class InventoryReceiveDeliverController(InventoryBaseController):
    """Controller for receive and deliver endpoints."""

    # -----------------
    # 5) Receive
    # -----------------

    @http.route('/api/v1/inventory/receive', type='http', auth='user', methods=['POST'], csrf=False, save_session=False)
    def inventory_receive(self, **_kwargs):
        self._require_api_group()
        self._require_capability('move')

        body = self._get_json_body()
        lines = body.get('lines')
        if not isinstance(lines, list) or not lines:
            self._bad_request('lines must be a non-empty list')

        warehouse = self._resolve_warehouse(body.get('warehouse_id'))
        dest_location = self._resolve_internal_location(body.get('location_id'))
        allowed = self._allowed_internal_locations(warehouse)
        self._ensure_allowed_location(dest_location, allowed)

        picking_type = warehouse.in_type_id
        if not picking_type:
            self._bad_request('Warehouse has no incoming picking type configured')

        supplier_loc = request.env.ref('stock.stock_location_suppliers')

        reference = (body.get('reference') or body.get('origin') or '').strip() or None

        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': supplier_loc.id,
            'location_dest_id': dest_location.id,
            'origin': reference,
        }

        move_vals_list = []
        tracking_lines = []
        for line in lines:
            product = self._resolve_product(line.get('product_id'))
            qty = self._float_qty(line.get('quantity'), 'quantity')
            uom = self._uom_from_line(product, line)

            move_vals_list.append({
                'name': product.display_name,
                'product_id': product.id,
                'product_uom_qty': qty,
                'product_uom': uom.id,
                'location_id': supplier_loc.id,
                'location_dest_id': dest_location.id,
            })
            tracking_lines.append((product, line))

        picking, moves = self._create_and_done_picking(
            picking_vals,
            move_vals_list,
            tracking_lines,
            allow_create_lot=True,
        )

        return self._json({
            'picking': {'id': picking.id, 'name': picking.name, 'state': picking.state},
            'moves': [{'id': m.id, 'product_id': m.product_id.id, 'state': m.state} for m in moves],
        }, status=201)

    # -----------------
    # 6) Deliver
    # -----------------

    @http.route('/api/v1/inventory/deliver', type='http', auth='user', methods=['POST'], csrf=False, save_session=False)
    def inventory_deliver(self, **_kwargs):
        self._require_api_group()
        self._require_capability('move')

        body = self._get_json_body()
        lines = body.get('lines')
        if not isinstance(lines, list) or not lines:
            self._bad_request('lines must be a non-empty list')

        warehouse = self._resolve_warehouse(body.get('warehouse_id'))
        source_location = self._resolve_internal_location(body.get('location_id'))
        allowed = self._allowed_internal_locations(warehouse)
        self._ensure_allowed_location(source_location, allowed)

        picking_type = warehouse.out_type_id
        if not picking_type:
            self._bad_request('Warehouse has no outgoing picking type configured')

        dest_location_id = body.get('destination_location_id')
        if dest_location_id:
            dest_location = request.env['stock.location'].browse(int(dest_location_id))
            if not dest_location.exists():
                self._not_found('Destination location not found')
        else:
            dest_location = request.env.ref('stock.stock_location_customers')

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