# -*- coding: utf-8 -*-
import math

import werkzeug

from odoo import fields, http
from odoo.http import request
from odoo.tools import float_compare


class InventoryBaseController(http.Controller):
    """Base controller with shared helpers for inventory API (v1)."""

    API_GROUP = 'stock_restful.group_stock_restful_api'

    def _json(self, payload, status=200):
        return request.make_json_response(payload, status=status)

    def _bad_request(self, message):
        raise werkzeug.exceptions.BadRequest(message)

    def _forbidden(self, message="Forbidden"):
        raise werkzeug.exceptions.Forbidden(message)

    def _not_found(self, message="Not Found"):
        raise werkzeug.exceptions.NotFound(message)

    def _require_api_group(self):
        if not request.env.user.has_group(self.API_GROUP):
            self._forbidden("Missing Stock REST API Access")

    def _get_int_param(self, name, default=None, required=False):
        raw = request.httprequest.args.get(name)
        if raw is None or raw == '':
            if required:
                self._bad_request(f"Missing query param: {name}")
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise werkzeug.exceptions.BadRequest(f"Invalid integer for {name}") from exc

    def _get_bool_param(self, name, default=False):
        raw = request.httprequest.args.get(name)
        if raw is None or raw == '':
            return bool(default)
        raw = str(raw).strip().lower()
        if raw in {'1', 'true', 't', 'yes', 'y', 'on'}:
            return True
        if raw in {'0', 'false', 'f', 'no', 'n', 'off'}:
            return False
        raise werkzeug.exceptions.BadRequest(f"Invalid boolean for {name}")

    def _get_image_size_param(self, name='image_size', default=128):
        size = self._get_int_param(name, default=default)
        allowed = {128, 256, 512, 1024, 1920}
        if size not in allowed:
            self._bad_request(f"{name} must be one of: {', '.join(str(s) for s in sorted(allowed))}")
        return size

    def _product_payload(self, product, include_images=False, image_size=128):
        payload = {
            'id': product.id,
            'name': product.display_name,
            'code': product.default_code,
            'barcode': product.barcode,
            'type': product.type,
            'tracking': product.tracking or 'none',
            'active': bool(product.active),
            'product_tmpl_id': product.product_tmpl_id.id,
            'category': {
                'id': product.categ_id.id,
                'name': product.categ_id.complete_name or product.categ_id.display_name,
            } if product.categ_id else None,
            'company': {
                'id': product.company_id.id,
                'name': product.company_id.name,
            } if product.company_id else None,
            'uom': {'id': product.uom_id.id, 'name': product.uom_id.name},
            'purchase_uom': {'id': product.uom_po_id.id, 'name': product.uom_po_id.name} if product.uom_po_id else None,
            'sale_ok': bool(product.sale_ok),
            'purchase_ok': bool(product.purchase_ok),
            'list_price': product.lst_price,
            'weight': product.weight,
            'volume': product.volume,
        }

        if include_images:
            field_name = f"image_{int(image_size)}"
            payload['image'] = {
                'size': int(image_size),
                'field': field_name,
                'data': getattr(product, field_name, False),
            }

        return payload

    def _product_detail_payload(self, product, include_images=False, image_size=128):
        base = self._product_payload(product, include_images=include_images, image_size=image_size)

        # Cost and descriptions
        base.update({
            'standard_price': product.standard_price,
            'description': product.product_tmpl_id.description or None,
            'description_sale': product.product_tmpl_id.description_sale or None,
        })

        # Template reference
        base['template'] = {
            'id': product.product_tmpl_id.id,
            'name': product.product_tmpl_id.name,
            'default_code': product.product_tmpl_id.default_code,
        }

        # Attributes (variant values)
        base['attributes'] = [
            {
                'attribute_id': ptav.attribute_id.id,
                'attribute_name': ptav.attribute_id.name,
                'value_id': ptav.product_attribute_value_id.id,
                'value_name': ptav.product_attribute_value_id.name,
            }
            for ptav in product.product_template_attribute_value_ids
        ]

        # Tags
        base['tags'] = [
            {'id': tag.id, 'name': tag.name}
            for tag in product.all_product_tag_ids
        ]

        return base

    def _get_csv_ints(self, name):
        raw = request.httprequest.args.get(name)
        if not raw:
            return []
        values = []
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(int(part))
            except ValueError as exc:
                raise werkzeug.exceptions.BadRequest(f"Invalid integer in {name}") from exc
        return values

    def _get_json_body(self):
        try:
            return request.get_json_data() or {}
        except ValueError as exc:
            raise werkzeug.exceptions.BadRequest("Invalid JSON body") from exc

    def _current_warehouse(self):
        # Pick the first active warehouse in the current company.
        wh = request.env['stock.warehouse'].search([
            ('company_id', '=', request.env.company.id),
            ('active', '=', True),
        ], limit=1)
        if not wh:
            self._not_found("No warehouse configured for current company")
        return wh

    def _allowed_internal_locations(self, warehouse):
        # Keep it conservative: only internal locations under the warehouse view.
        domain = [
            ('id', 'child_of', warehouse.view_location_id.id),
            ('usage', '=', 'internal'),
        ]
        return request.env['stock.location'].search(domain)

    def _ensure_allowed_location(self, location, allowed_locations):
        if location.usage != 'internal':
            self._bad_request("Location must be an internal location")
        if location.id not in allowed_locations.ids:
            self._forbidden("Location not allowed")

    def _capabilities(self):
        user = request.env.user
        can_read = user.has_group('stock.group_stock_user')
        can_move = user.has_group('stock.group_stock_user')
        can_adjust = user.has_group('stock.group_stock_manager')
        can_create_product = user.has_group('product.group_product_manager') or user.has_group('stock.group_stock_manager')
        return {
            'read': bool(can_read),
            'move': bool(can_move),
            'adjust': bool(can_adjust),
            'product_create': bool(can_create_product),
        }

    def _require_capability(self, cap_key):
        caps = self._capabilities()
        if not caps.get(cap_key):
            self._forbidden(f"Missing capability: {cap_key}")

    def _resolve_product(self, product_id):
        product = request.env['product.product'].browse(int(product_id))
        if not product.exists():
            self._not_found("Product not found")
        if product.type == 'service':
            self._bad_request("Product is not inventory-relevant")
        return product

    def _resolve_internal_location(self, location_id):
        location = request.env['stock.location'].browse(int(location_id))
        if not location.exists():
            self._not_found("Location not found")
        return location

    def _resolve_warehouse(self, warehouse_id=None):
        if warehouse_id:
            wh = request.env['stock.warehouse'].browse(int(warehouse_id))
            if not wh.exists():
                self._not_found("Warehouse not found")
            return wh
        return self._current_warehouse()

    def _direction(self, src_loc, dst_loc):
        if src_loc.usage != 'internal' and dst_loc.usage == 'internal':
            return 'in'
        if src_loc.usage == 'internal' and dst_loc.usage != 'internal':
            return 'out'
        if src_loc.usage == 'internal' and dst_loc.usage == 'internal':
            return 'internal'
        return 'internal'

    def _uom_from_line(self, product, line):
        uom_id = line.get('uom_id')
        if not uom_id:
            return product.uom_id
        uom = request.env['uom.uom'].browse(int(uom_id))
        if not uom.exists():
            self._bad_request("Invalid uom_id")
        return uom

    def _float_qty(self, value, field_name='quantity'):
        try:
            qty = float(value)
        except (TypeError, ValueError) as exc:
            raise werkzeug.exceptions.BadRequest(f"Invalid {field_name}") from exc
        if not math.isfinite(qty) or qty <= 0:
            self._bad_request(f"{field_name} must be > 0")
        return qty

    def _float_qty_allow_zero(self, value, field_name='quantity'):
        try:
            qty = float(value)
        except (TypeError, ValueError) as exc:
            raise werkzeug.exceptions.BadRequest(f"Invalid {field_name}") from exc
        if not math.isfinite(qty) or qty < 0:
            self._bad_request(f"{field_name} must be >= 0")
        return qty

    def _clean_str(self, value, field_name):
        if value is None:
            return None
        if not isinstance(value, str):
            raise werkzeug.exceptions.BadRequest(f"Invalid {field_name}")
        value = value.strip()
        return value or None

    def _prepare_move_line_vals(self, move, qty_done, lot=None, lot_name=None):
        vals = {
            'move_id': move.id,
            'product_id': move.product_id.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'product_uom_id': move.product_uom.id,
            'qty_done': qty_done,
        }
        if lot:
            vals['lot_id'] = lot.id
        if lot_name:
            vals['lot_name'] = lot_name
        return vals

    def _apply_tracking(self, move, product, line, allow_create_lot=False):
        tracking = product.tracking or 'none'
        qty = self._float_qty(line.get('quantity'), 'quantity')

        if tracking == 'none':
            return

        Lot = request.env['stock.lot']

        if tracking == 'lot':
            lot_name = (line.get('lot') or line.get('lot_name') or '').strip()
            lot_id = line.get('lot_id')
            if not lot_name and not lot_id:
                self._bad_request("Lot-tracked products require lot_name or lot_id")

            lot = None
            if lot_id:
                lot = Lot.browse(int(lot_id))
                if not lot.exists() or lot.product_id.id != product.id:
                    self._bad_request("Invalid lot_id for product")
            elif lot_name:
                lot = Lot.search([('name', '=', lot_name), ('product_id', '=', product.id)], limit=1)
                if not lot and not allow_create_lot:
                    self._bad_request("Unknown lot_name for product")

            move_line_vals = self._prepare_move_line_vals(
                move,
                qty_done=qty,
                lot=lot,
                lot_name=(lot_name if (allow_create_lot and not lot) else None),
            )
            request.env['stock.move.line'].create(move_line_vals)
            return

        if tracking == 'serial':
            serials = line.get('serials') or line.get('serial_numbers')
            if not isinstance(serials, list) or not serials:
                self._bad_request("Serial-tracked products require serials as a non-empty list")
            if float_compare(qty, float(len(serials)), precision_rounding=product.uom_id.rounding) != 0:
                self._bad_request("Serial quantity must match the number of serials")

            for serial in serials:
                serial = (serial or '').strip()
                if not serial:
                    self._bad_request("Empty serial value")
                lot = Lot.search([('name', '=', serial), ('product_id', '=', product.id)], limit=1)
                if not lot:
                    if not allow_create_lot:
                        self._bad_request("Unknown serial for product")
                    move_line_vals = self._prepare_move_line_vals(move, qty_done=1.0, lot_name=serial)
                else:
                    move_line_vals = self._prepare_move_line_vals(move, qty_done=1.0, lot=lot)
                request.env['stock.move.line'].create(move_line_vals)
            return

        self._bad_request("Unsupported tracking type")

    def _validate_available_qty(self, product, location, qty, uom=None):
        available = product.with_context(location=location.id).free_qty
        qty_in_product_uom = qty
        if uom and uom.id != product.uom_id.id:
            qty_in_product_uom = uom._compute_quantity(qty, product.uom_id)
        if float_compare(available, qty_in_product_uom, precision_rounding=product.uom_id.rounding) < 0:
            self._bad_request("Insufficient available quantity")

    def _create_and_done_picking(self, picking_vals, move_vals_list, tracking_lines, allow_create_lot=False):
        Picking = request.env['stock.picking']
        picking = Picking.create(picking_vals)

        Move = request.env['stock.move']
        moves = Move.create([
            dict(vals, picking_id=picking.id) for vals in move_vals_list
        ])

        picking.action_confirm()
        picking.action_assign()

        # Apply tracking lines (qty_done in move lines)
        for move, (product, line) in zip(moves, tracking_lines):
            self._apply_tracking(move, product, line, allow_create_lot=allow_create_lot)
            if (product.tracking or 'none') == 'none':
                qty = self._float_qty(line.get('quantity'), 'quantity')
                if move.move_line_ids:
                    move.move_line_ids[0].qty_done = qty
                    if len(move.move_line_ids) > 1:
                        (move.move_line_ids - move.move_line_ids[0]).qty_done = 0.0
                else:
                    request.env['stock.move.line'].create(self._prepare_move_line_vals(move, qty_done=qty))

        picking._action_done()
        return picking, moves