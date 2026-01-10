# Accounting & Valuation

This document covers the modules that integrate Inventory with Accounting, handling stock valuation and landed costs.

## Business Overview
These modules bridge the gap between warehouse operations and the finance department. They ensure that every physical stock move is reflected in the company's balance sheet in real-time, providing accurate asset valuation.

### Key Features
*   **Perpetual Inventory Valuation**: Automatically posts journal entries for every stock receipt and delivery.
*   **Landed Costs**: Allocate additional costs (freight, insurance, customs duties) to the cost of the products, ensuring accurate profit margin calculations.
*   **Valuation Reports**: View the value of your inventory at any specific date in the past.
*   **Invoice from Picking**: Generate customer invoices directly based on what was actually shipped.

### Common Use Cases
*   **Importers** distributing the cost of a shipping container and customs fees across all received products to calculate the true "Landed Cost".
*   **Public Companies** requiring real-time, audit-ready inventory valuation on their balance sheet.
*   **Distributors** using "Average Cost" or "Standard Cost" methods for inventory valuation.

## Modules
*   `stock_account`
*   `stock_landed_costs`

## 1. Stock Account (`stock_account`)

**Purpose**: Bridges Inventory and Accounting. It introduces the concept of "Perpetual Inventory Valuation" (Automated Valuation), where every stock move generates a Journal Entry.

### Key Models & Extensions

#### `stock.move` (Extension)
*   **New Fields**:
    *   `account_move_ids`: Links the stock move to generated Journal Entries (`account.move`).
    *   `stock_valuation_layer_ids`: Links to the valuation layers created by this move.
    *   `to_refund`: Flag for handling refunds/returns.
*   **Key Logic**:
    *   `_account_entry_move()`: Triggered when a move is done. It creates the Journal Entry (Debit Stock, Credit Input/Output Account).
    *   `_get_price_unit()`: Calculates the cost of the move based on FIFO/AVCO rules.

#### `stock.valuation.layer` (Stock Valuation Layer)
*   **Purpose**: Records the value of stock moves and manages inventory valuation over time (FIFO/Average Cost).
*   **Fields**:
    *   `company_id` (**Many2one**, Required): The company associated with this valuation layer.
    *   `product_id` (**Many2one**, Required): The product being valued.
    *   `quantity` (**Float**): The quantity of the product in this layer.
    *   `uom_id` (**Many2one**, Required): The unit of measure for the product.
    *   `currency_id` (**Many2one**, Required): The currency used for the valuation.
    *   `unit_cost` (**Float**): The unit cost of the product in this layer.
    *   `value` (**Monetary**): The total value of the layer (Quantity * Unit Cost).
    *   `remaining_qty` (**Float**): The quantity remaining in this layer that hasn't been consumed by outgoing moves.
    *   `remaining_value` (**Monetary**): The value remaining in this layer.
    *   `description` (**Char**): A description of the valuation layer.
    *   `stock_valuation_layer_id` (**Many2one**): Link to another valuation layer (e.g., for returns or corrections).
    *   `stock_move_id` (**Many2one**): The stock move that created this valuation layer.
    *   `account_move_id` (**Many2one**): The accounting journal entry associated with this layer.
    *   `account_move_line_id` (**Many2one**): The specific invoice line related to this layer (if applicable).
    *   `price_diff_value` (**Float**): Correction value for invoice currency differences.
    *   `warehouse_id` (**Many2one**): The warehouse where the receipt occurred.

#### `product.template` / `product.category` (Extension)
*   **New Fields**:
    *   `property_valuation`: `manual_periodic` (Periodic) or `real_time` (Automated).
    *   `property_cost_method`: `standard`, `average`, or `fifo`.

## 2. Stock Landed Costs (`stock_landed_costs`)

**Purpose**: Allows allocating additional costs (freight, duties, insurance) to the value of products already in stock.

### Key Models

#### `stock.landed.cost` (Stock Landed Cost)
*   **Purpose**: Allows allocating additional costs (freight, insurance, customs) to stock pickings to update product valuation.
*   **Fields**:
    *   `name` (**Char**): The name or reference of the landed cost.
    *   `date` (**Date**, Required): The date of the landed cost.
    *   `target_model` (**Selection**, Required): Defines what the cost applies to (e.g., 'Transfers').
    *   `picking_ids` (**Many2many**): The specific transfers (pickings) to which the costs are applied.
    *   `cost_lines` (**One2many**): The list of specific cost lines to be allocated.
    *   `valuation_adjustment_lines` (**One2many**): The calculated adjustments applied to products.
    *   `description` (**Text**): Internal notes or description.
    *   `amount_total` (**Monetary**): The total amount of the landed cost.
    *   `state` (**Selection**): The status of the record (Draft, Posted, Cancelled).
    *   `account_move_id` (**Many2one**): The journal entry created when the cost is validated.
    *   `account_journal_id` (**Many2one**, Required): The journal used for the accounting entry.
    *   `company_id` (**Many2one**, Required): The company associated with the record.
    *   `vendor_bill_id` (**Many2one**): The vendor bill related to these costs.

#### `stock.landed.cost.lines` (Stock Landed Cost Line)
*   **Purpose**: Represents a specific cost item (e.g., "Freight") within a Landed Cost record.
*   **Fields**:
    *   `name` (**Char**): Description of the cost line.
    *   `cost_id` (**Many2one**, Required): The parent Landed Cost record.
    *   `product_id` (**Many2one**, Required): The service product representing the cost type.
    *   `price_unit` (**Monetary**, Required): The cost amount to be allocated.
    *   `split_method` (**Selection**, Required): How the cost is divided (Equal, By Quantity, By Current Cost, By Weight, By Volume).
    *   `account_id` (**Many2one**): The specific account for this cost line.
