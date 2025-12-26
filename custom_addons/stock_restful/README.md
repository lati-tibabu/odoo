# stock_restful

Minimal, operation-based inventory REST API for Odoo 18.

The controller is implemented across multiple files in `controllers/` for maintainability:
- `inventory_base.py`: Shared helpers and base controller class.
- `inventory_context_products.py`: Context and products endpoints.
- `inventory_availability_movements.py`: Availability and movements endpoints.
- `inventory_receive_deliver.py`: Receive and deliver endpoints.
- `inventory_transfer_adjust.py`: Transfer and adjust endpoints.

## Authentication

All endpoints require:
- `Authorization: Bearer <API_KEY>` (recommended), using Odoo’s built-in API keys (bearer auth)
- User must be in **Stock REST API Access** group (created by this module)

Notes:
- These routes are implemented as `type='http'` endpoints and return JSON.
- Do **not** expose `stock.quant` CRUD, and this module does not.

## Endpoints (v1)

- `GET /api/v1/inventory/context`
- `GET /api/v1/inventory/products`
- `GET /api/v1/inventory/products/<id>`
- `POST /api/v1/inventory/products`
- `PUT /api/v1/inventory/products/<id>`
- `DELETE /api/v1/inventory/products/<id>`
- `GET /api/v1/inventory/availability`
- `GET /api/v1/inventory/movements`
- `POST /api/v1/inventory/receive`
- `POST /api/v1/inventory/deliver`
- `POST /api/v1/inventory/transfer`
- `POST /api/v1/inventory/adjust`

Base URL example:
- `https://your-odoo.example.com`

Common headers:
- `Authorization: Bearer <API_KEY>`
- `Content-Type: application/json`

## 1) Context

### `GET /api/v1/inventory/context`

Returns the current company, a default warehouse, allowed internal locations, and user capabilities.

**curl**
```bash
curl -sS \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/context" | jq
```

## 2) Products (inventory-relevant only)

### `GET /api/v1/inventory/products?limit=200`

Returns stockable/non-service products with inventory-relevant fields only.

Query params:
- `limit` (default 200, max 2000)
- `include_images=1` (optional, default `0`)
- `image_size=128|256|512|1024|1920` (optional, default `128`, used only if `include_images=1`)

**curl**
```bash
curl -sS \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/products?limit=200" | jq
```

Response fields per item (types shown):
- Core:
  - `id` (int), `name` (string), `code` (string|null), `barcode` (string|null), `type` (string: `consu|combo`), `tracking` (string: `none|lot|serial`), `active` (bool)
  - `product_tmpl_id` (int)
  - `uom` (object: `{id:int, name:string}`), `purchase_uom` (object|null: `{id:int, name:string}`)
- Commercial:
  - `sale_ok` (bool), `purchase_ok` (bool), `list_price` (float)
- Physical:
  - `weight` (float), `volume` (float)
- Classification:
  - `category` (object|null: `{id:int, name:string}`), `company` (object|null: `{id:int, name:string}`)
- Optional (only if `include_images=1`):
  - `image` (object): `{ size:int, field:string, data:base64-string|false }`

### `GET /api/v1/inventory/products/<id>`

Returns one product in detail. Same fields as the list endpoint plus optional image data.

Query params:
- `include_images=1` (optional, default `0`)
- `image_size=128|256|512|1024|1920` (optional, default `128`, used only if `include_images=1`)

Extra fields included in the detail payload (in addition to the list fields):
- `standard_price` (float, cost)
- `description` (string|null), `description_sale` (string|null)
- `template` (object): `{ id:int, name:string, default_code:string|null }`
- `attributes` (array of objects): `{ attribute_id:int, attribute_name:string, value_id:int, value_name:string }`
- `tags` (array of objects): `{ id:int, name:string }`

### `POST /api/v1/inventory/products`

Creates a new inventory-relevant product.

Notes:
- Requires **Stock REST API Access** *and* product creation permission.
- Creates a `product.template` and returns the resulting first variant (`product.product`).
- This API intentionally rejects `type=service` (services are not inventory-relevant).

Body (minimum):
```json
{
  "name": "My Product"
}
```

Supported body fields:
- `name` (required)
- `type` (optional: `consu|combo`, default `consu`)
- `default_code` (or `code`)
- `barcode`
- `categ_id`
- `uom_id`, `uom_po_id`
- `sale_ok`, `purchase_ok`, `active`
- `list_price`, `weight`, `volume`
- `company_id` (optional, defaults to current company)
- Image (optional):
  - `image_1920` (base64)
  - or `image` as base64 string
  - or `image: { "data": "<base64>" }`

**curl**
```bash
curl -sS -X POST \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "USB Cable",
    "default_code": "USB-C-1M",
    "barcode": "1234567890123",
    "categ_id": 1,
    "uom_id": 1,
    "uom_po_id": 1,
    "sale_ok": true,
    "purchase_ok": true,
    "list_price": 9.99,
    "weight": 0.05
  }' \
  "${ODOO_BASE_URL}/api/v1/inventory/products" | jq
```

### `PUT /api/v1/inventory/products/<id>`

Updates an existing inventory-relevant product.

Notes:
- Requires **Stock REST API Access** *and* product creation permission.
- Supports `PUT` or `PATCH` methods.
- Updates the product variant (`product.product`).
- This API intentionally rejects `type=service` (services are not inventory-relevant).

Supported body fields (all optional):
- `name`
- `type` (`consu|combo`)
- `default_code` (or `code`)
- `barcode`
- `categ_id`
- `uom_id`, `uom_po_id`
- `sale_ok`, `purchase_ok`, `active`
- `list_price`, `weight`, `volume`
- `company_id`
- Image:
  - `image_1920` (base64)
  - or `image` as base64 string
  - or `image: { "data": "<base64>" }`

**curl**
```bash
curl -sS -X PUT \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "USB Cable (Updated)",
    "list_price": 12.99
  }' \
  "${ODOO_BASE_URL}/api/v1/inventory/products/123" | jq
```

### `DELETE /api/v1/inventory/products/<id>`

Deletes an existing inventory-relevant product.

Notes:
- Requires **Stock REST API Access** *and* product creation permission.
- Deletes the product variant (`product.product`).
- If the product is the only variant of its template, the template may also be deleted.

**curl**
```bash
curl -sS -X DELETE \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/products/123" | jq
```

To include image data in the response:
```bash
curl -sS -X POST \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"USB Cable"}' \
  "${ODOO_BASE_URL}/api/v1/inventory/products?include_images=1&image_size=512" | jq
```

## 3) Availability (computed, read-only truth)

### `GET /api/v1/inventory/availability`

Returns computed quantities (never raw quants).

Query params:
- Optional scope:
  - `warehouse_id=<id>` **or** `location_id=<id>` (not both)
- Product selection:
  - `product_ids=1,2,3` (optional)
  - `limit` (default 200, max 2000) if `product_ids` is omitted

Returned per product:
- `on_hand_qty` (qty available)
- `available_qty` (free qty)
- `reserved_qty` (= on-hand − available)

**curl (by warehouse)**
```bash
curl -sS \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/availability?warehouse_id=1&product_ids=10,11" | jq
```

**curl (by location)**
```bash
curl -sS \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/availability?location_id=25&product_ids=10,11" | jq
```

## 4) Movements (audit trail, read-only)

### `GET /api/v1/inventory/movements`

Returns recent `stock.move` records for “why did it change?” auditing.

Query params:
- `limit` (default 100, max 1000)
- Optional scope:
  - `warehouse_id=<id>` **or** `location_id=<id>`
- Optional filter:
  - `product_ids=1,2,3`

Direction is derived from source/destination usage:
- `in` (external → internal)
- `out` (internal → external)
- `internal` (internal → internal)

**curl**
```bash
curl -sS \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  "${ODOO_BASE_URL}/api/v1/inventory/movements?warehouse_id=1&limit=50" | jq
```

## 5) Receive (incoming stock)

### `POST /api/v1/inventory/receive`

One intention: receive product(s) into an internal location.

Internally:
- create picking (incoming type)
- create moves
- confirm/assign
- set `qty_done` (and lot/serial move lines if needed)
- validate (`_action_done()`)

Body:
```json
{
  "warehouse_id": 1,
  "location_id": 25,
  "reference": "PO00012",
  "lines": [
    {"product_id": 10, "quantity": 5},
    {"product_id": 11, "quantity": 2, "lot_name": "LOT-2025-001"},
    {"product_id": 12, "quantity": 2, "serials": ["SN0001", "SN0002"]}
  ]
}
```

Notes:
- For `tracking=lot`: require `lot_id` or `lot_name`
- For `tracking=serial`: require `serials` and the count must match `quantity`
- Receive allows creating new lots/serials if they don’t exist

**curl**
```bash
curl -sS -X POST \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_id": 1,
    "location_id": 25,
    "reference": "PO00012",
    "lines": [
      {"product_id": 10, "quantity": 5}
    ]
  }' \
  "${ODOO_BASE_URL}/api/v1/inventory/receive" | jq
```

## 6) Deliver (outgoing stock)

### `POST /api/v1/inventory/deliver`

One intention: deliver product(s) from an internal location to an external/customer destination.

Body:
```json
{
  "warehouse_id": 1,
  "location_id": 25,
  "destination_location_id": 8,
  "reference": "SO00045",
  "lines": [
    {"product_id": 10, "quantity": 1}
  ]
}
```

Notes:
- If `destination_location_id` is omitted, it defaults to the Customers location.
- Validates available quantity before executing.
- For tracked products, lots/serials must already exist.

## 7) Transfer (internal)

### `POST /api/v1/inventory/transfer`

Moves product(s) from one internal location to another (no shortcuts; always via moves).

Body:
```json
{
  "warehouse_id": 1,
  "source_location_id": 25,
  "destination_location_id": 26,
  "reference": "Bin move",
  "lines": [
    {"product_id": 10, "quantity": 3}
  ]
}
```

## 8) Adjust (restricted)

### `POST /api/v1/inventory/adjust`

Dangerous endpoint: adjusts on-hand quantity to a target value.

Requirements:
- User must have `adjust` capability (Stock Manager)
- `reason` is mandatory

Body:
```json
{
  "warehouse_id": 1,
  "location_id": 25,
  "product_id": 10,
  "new_quantity": 0,
  "reason": "Cycle count 2025-12-23"
}
```

Notes:
- Adjustment is performed as an inventory gain/loss move (internal ↔ inventory location).
- For tracked products, include `lot_name` (lot) or `serials` (serial) as needed.

## Error behavior

Errors are returned as standard HTTP errors:
- `400` bad request (missing/invalid payload)
- `401` unauthorized (missing/invalid bearer token)
- `403` forbidden (missing group/capability, disallowed location)
- `404` not found (invalid record id)

## Security model

- Group required: **Stock REST API Access**
- Capabilities reported by `/context`:
  - `read`: stock user
  - `move`: stock user
  - `adjust`: stock manager
  - `product_create`: product creation (Product Creation group) or stock manager

## Configuration

- Ensure your `odoo.conf` includes `custom_addons` in `addons_path`.
- Install/upgrade module: `stock_restful`.
