# Advanced Operations

This document covers modules that enable complex inventory workflows like Batch Picking and Dropshipping.

## Business Overview
These modules optimize workflows for high-volume environments or specific fulfillment models that bypass the warehouse entirely. They are designed to increase efficiency and reduce handling time.

### Key Features
*   **Batch Picking**: Group multiple orders into a single picking list to reduce worker travel time in the warehouse.
*   **Wave Picking**: Advanced grouping of transfers to optimize logistics operations.
*   **Dropshipping**: A specialized route where products are shipped directly from the vendor to the customer, never entering your warehouse.
*   **Route Management**: Configure products to automatically default to dropship based on supplier rules.

### Common Use Cases
*   **High-Volume Warehouses** where a picker collects items for 10 different orders in one pass through the aisles (Batching).
*   **Online Retailers** selling bulky items (like furniture) that are shipped directly from the manufacturer to the consumer (Dropshipping).

## Modules
*   `stock_picking_batch`
*   `stock_dropshipping`

## 1. Batch Picking (`stock_picking_batch`)

**Purpose**: Allows grouping multiple transfers (`stock.picking`) into a single Batch Transfer to optimize the picking process (e.g., picking multiple orders at once).

### Key Models

#### `stock.picking.batch` (Batch Transfer)
*   **Purpose**: Groups multiple transfers (pickings) together to be processed at the same time.
*   **Fields**:
    *   `name` (**Char**, Required): The reference name of the batch.
    *   `description` (**Char**): Short description of the batch.
    *   `user_id` (**Many2one**): The user responsible for the batch.
    *   `company_id` (**Many2one**, Required): The company associated with the batch.
    *   `picking_ids` (**One2many**): The list of transfers included in this batch.
    *   `state` (**Selection**, Required): The status of the batch (Draft, In progress, Done, Cancelled).
    *   `picking_type_id` (**Many2one**): The operation type (e.g., Delivery Orders) common to the batch.
    *   `scheduled_date` (**Datetime**): The scheduled date for processing the batch.
    *   `is_wave` (**Boolean**): Indicates if this batch is a "Wave" transfer (advanced batching).

#### `stock.picking` (Extension)
*   **New Fields**:
    *   `batch_id`: Link to the parent batch.

## 2. Dropshipping (`stock_dropshipping`)

**Purpose**: Enables the "Dropship" route, where products are shipped directly from the Vendor to the Customer, bypassing the warehouse.

### Key Models & Extensions

#### `stock.picking` (Extension)
*   **New Fields**:
    *   `is_dropship`: Boolean flag indicating if the transfer is a dropship operation (Vendor -> Customer).
*   **Key Logic**:
    *   `_compute_is_dropship()`: Checks if Source is Supplier and Destination is Customer.

#### `stock.rule` (Extension)
*   **Purpose**: Adds logic to handle the specific Dropship route.
*   **Key Logic**:
    *   `_get_partner_id()`: Ensures the correct address is used for the Purchase Order (Customer's address).

#### `res.company` (Extension)
*   **Purpose**: Configuration to enable/disable dropshipping globally.
