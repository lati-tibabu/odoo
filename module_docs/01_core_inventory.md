# Core Inventory Architecture

This document outlines the core architecture of the Odoo 18 Inventory system, primarily based on the `stock` module.

## Business Overview
The **Core Inventory** module (`stock`) is the central hub for all inventory operations. It digitizes your warehouse, allowing you to track every product move from receipt to delivery. It handles the "physical" reality of stock management, ensuring you know exactly what you have and where it is.

### Key Features
*   **Multi-Warehouse & Location Management**: Define multiple warehouses and granular locations (shelves, bins, rows) within them.
*   **Traceability**: Track products using **Lots** (batches) or **Serial Numbers** (unique items) for full upstream/downstream traceability.
*   **Reordering Rules**: Set minimum and maximum stock levels to automatically trigger replenishment orders.
*   **Removal Strategies**: Define how stock is picked (FIFO - First In First Out, LIFO, Closest Location, or Least Packages).
*   **Inventory Adjustments**: Perform cycle counts or full physical inventories to correct stock levels.

### Common Use Cases
*   **Retailers** ensuring the oldest stock is sold first (FIFO) to prevent spoilage.
*   **Electronics Manufacturers** tracking individual components via Serial Numbers for warranty purposes.
*   **Warehouses** organizing stock into specific zones (e.g., "Cold Storage", "Zone A - Bin 4").

## 1. Structural Models (The "Where")

These models define the physical and logical topology of the inventory.

### `stock.warehouse` (Warehouse)
*   **Purpose**: Represents a physical place where goods are stored and operations (receipts, deliveries) are performed.
*   **Fields**:
    *   `name` (**Char**, Required): The name of the warehouse.
    *   `code` (**Char**, Required): Short name used to identify your warehouse (e.g., WH).
    *   `company_id` (**Many2one**, Required): The company this warehouse belongs to.
    *   `partner_id` (**Many2one**): The address of the warehouse.
    *   `view_location_id` (**Many2one**, Required): The parent view location that aggregates all locations of this warehouse.
    *   `lot_stock_id` (**Many2one**, Required): The default stock location (Shelf 1) of this warehouse.
    *   `reception_steps` (**Selection**, Required): Defines the incoming route (e.g., 'one_step', 'two_steps', 'three_steps').
    *   `delivery_steps` (**Selection**, Required): Defines the outgoing route (e.g., 'ship_only', 'pick_ship', 'pick_pack_ship').
    *   `resupply_wh_ids` (**Many2many**): Warehouses that can resupply this warehouse.

### `stock.location` (Inventory Locations)
*   **Purpose**: Represents a specific space within a warehouse (shelf, floor, etc.) or a virtual location (partner, production).
*   **Fields**:
    *   `name` (**Char**, Required): The name of the location.
    *   `complete_name` (**Char**): The full hierarchical name (e.g., WH/Stock/Shelf 1).
    *   `usage` (**Selection**, Required): The type of location (e.g., 'internal', 'customer', 'supplier', 'inventory', 'production', 'view').
    *   `location_id` (**Many2one**): The parent location.
    *   `company_id` (**Many2one**): The company owning this location.
    *   `scrap_location` (**Boolean**): Check this box to allow using this location to put scrapped/damaged goods.
    *   `replenish_location` (**Boolean**): Activate this function to get all quantities to replenish at this particular location.
    *   `removal_strategy_id` (**Many2one**): Defines the default method used for suggesting the exact location/lot (FIFO, LIFO, FEFO, etc.).
    *   `cyclic_inventory_frequency` (**Integer**): Frequency (in days) for the cyclic inventory count.

## 2. Operational Models (The "Flow")

These models handle the planning and execution of stock movements.

### `stock.picking` (Transfer)
*   **Purpose**: Represents a shipment or transfer of goods, grouping multiple stock moves.
*   **Fields**:
    *   `name` (**Char**): The reference of the transfer (e.g., WH/OUT/0001).
    *   `picking_type_id` (**Many2one**, Required): The operation type (e.g., Receipts, Delivery Orders).
    *   `location_id` (**Many2one**, Required): The source location for the transfer.
    *   `location_dest_id` (**Many2one**, Required): The destination location for the transfer.
    *   `state` (**Selection**): The status of the transfer (draft, waiting, confirmed, assigned, done, cancel).
    *   `scheduled_date` (**Datetime**): Scheduled time for the first part of the shipment to be processed.
    *   `date_deadline` (**Datetime**): The deadline for the transfer validation.
    *   `partner_id` (**Many2one**): The contact (customer or vendor) associated with the transfer.
    *   `move_ids` (**One2many**): The list of stock moves (products) in this transfer.
    *   `move_line_ids` (**One2many**): The detailed operations (packs, lots/serials).
    *   `origin` (**Char**): Reference of the document that generated this transfer (e.g., Sale Order).
    *   `priority` (**Selection**): Priority of the transfer (Normal, Urgent).

### `stock.move` (Stock Move)
*   **Purpose**: Represents the planned movement of a specific product from one location to another.
*   **Fields**:
    *   `name` (**Char**, Required): Description of the move.
    *   `product_id` (**Many2one**, Required): The product being moved.
    *   `product_uom_qty` (**Float**, Required): The demand quantity in the product's Unit of Measure.
    *   `quantity` (**Float**): The quantity currently marked as done/picked.
    *   `product_uom` (**Many2one**, Required): The Unit of Measure for the move.
    *   `location_id` (**Many2one**, Required): The source location.
    *   `location_dest_id` (**Many2one**, Required): The destination location.
    *   `picking_id` (**Many2one**): The transfer this move belongs to.
    *   `state` (**Selection**): The status of the move (draft, confirmed, assigned, done, cancel).
    *   `date` (**Datetime**, Required): Scheduled date for the move.
    *   `company_id` (**Many2one**, Required): The company.
    *   `procure_method` (**Selection**, Required): Supply method ('make_to_stock' or 'make_to_order').

### `stock.move.line` (Product Moves / Detailed Operations)
*   **Purpose**: Represents the actual execution of a stock move, including specific lots, serial numbers, or packages.
*   **Fields**:
    *   `move_id` (**Many2one**): The parent stock move.
    *   `picking_id` (**Many2one**): The parent transfer.
    *   `product_id` (**Many2one**): The product being moved.
    *   `product_uom_id` (**Many2one**, Required): The Unit of Measure.
    *   `quantity` (**Float**): The quantity actually moved.
    *   `location_id` (**Many2one**, Required): The actual source location.
    *   `location_dest_id` (**Many2one**, Required): The actual destination location.
    *   `lot_id` (**Many2one**): The Lot/Serial Number moved.
    *   `lot_name` (**Char**): Text field for entering a new Lot/Serial Number.
    *   `package_id` (**Many2one**): The source package.
    *   `result_package_id` (**Many2one**): The destination package (if packing).
    *   `date` (**Datetime**, Required): The date of the operation.

## 3. State Models (The "Truth")

### `stock.quant` (Quants)
*   **Purpose**: Represents the physical stock currently on hand at a specific location.
*   **Fields**:
    *   `product_id` (**Many2one**, Required): The product.
    *   `location_id` (**Many2one**, Required): The location where the product is stored.
    *   `quantity` (**Float**): The total quantity on hand.
    *   `reserved_quantity` (**Float**, Required): The quantity reserved for pending transfers.
    *   `available_quantity` (**Float**): The quantity available for new reservations (Quantity - Reserved).
    *   `lot_id` (**Many2one**): The specific Lot/Serial Number (if tracked).
    *   `package_id` (**Many2one**): The package containing this quant.
    *   `owner_id` (**Many2one**): The owner of the stock (for consignment).
    *   `inventory_quantity` (**Float**): The counted quantity (used during inventory adjustments).
    *   `in_date` (**Datetime**, Required): The incoming date (used for FIFO).

## 4. Logic & Configuration (The "Brain")

### `stock.location.route` (Inventory Routes)
*   **Purpose**: A collection of rules that define how products move through the warehouse.
*   **Fields**:
    *   `name` (**Char**, Required): The name of the route.
    *   `active` (**Boolean**): Whether the route is active.
    *   `sequence` (**Integer**): The priority of the route.
    *   `rule_ids` (**One2many**): The list of rules belonging to this route.
    *   `product_selectable` (**Boolean**): If checked, the route can be selected on products.
    *   `product_categ_selectable` (**Boolean**): If checked, the route can be selected on product categories.
    *   `warehouse_selectable` (**Boolean**): If checked, the route can be selected on warehouses.
    *   `supplied_wh_id` (**Many2many**): The warehouses where this route is applicable.

### `stock.rule` (Stock Rule)
*   **Purpose**: Defines how products are procured or moved between locations (e.g., Buy, Pull from Stock).
*   **Fields**:
    *   `name` (**Char**, Required): The name of the rule.
    *   `action` (**Selection**, Required): The action to perform (pull, push, pull_push).
    *   `picking_type_id` (**Many2one**, Required): The operation type used for the created transfer.
    *   `location_src_id` (**Many2one**): The source location (for Pull rules).
    *   `location_id` (**Many2one**, Required): The destination location.
    *   `route_id` (**Many2one**, Required): The route this rule belongs to.
    *   `procure_method` (**Selection**, Required): Supply method ('make_to_stock', 'make_to_order', 'mts_else_mto').
    *   `delay` (**Integer**): Lead time in days.
    *   `warehouse_id` (**Many2one**): The warehouse this rule applies to.
