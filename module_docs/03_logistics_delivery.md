# Logistics & Delivery

This document covers the modules responsible for shipping, carrier integration, and fleet management.

## Business Overview
This suite of modules manages the outbound logistics process, from calculating shipping costs to organizing the physical dispatch. It connects your warehouse to external carriers or your own internal fleet.

### Key Features
*   **Carrier Integration**: Connect with external carriers (e.g., FedEx, UPS, DHL) or define custom internal carriers.
*   **Shipping Cost Calculation**: Automatically compute shipping prices based on rules (Weight, Volume, Price) or fixed rates.
*   **Free Shipping Rules**: Set conditions for free delivery (e.g., "Free if order total > $300").
*   **Fleet Integration**: Organize packages and dispatch orders using the company's own vehicle fleet.
*   **Shipping Labels**: Generate and print carrier-compliant shipping labels.

### Common Use Cases
*   **E-commerce Stores** offering "Free Shipping on orders over $50" to incentivize larger purchases.
*   **Wholesalers** charging customers shipping fees based on the total weight of the pallet.
*   **Local Businesses** using their own vans for delivery and managing the dispatch queue via the Fleet module.

## Modules
*   `delivery` (Base Shipping)
*   `stock_delivery` (Inventory Integration)
*   `stock_fleet` (Fleet Integration)

## 1. Delivery (`delivery`)

**Purpose**: The base module for managing shipping methods and calculating shipping costs.

### Key Models

#### `delivery.carrier` (Shipping Methods)
*   **Purpose**: Defines shipping methods and integration with external shipping providers (FedEx, UPS, etc.).
*   **Fields**:
    *   `name` (**Char**, Required): The name of the delivery method displayed to users.
    *   `active` (**Boolean**): Whether the shipping method is active.
    *   `sequence` (**Integer**): Sorting order for display.
    *   `delivery_type` (**Selection**, Required): The provider type (e.g., Fixed Price, Based on Rules, or external provider).
    *   `integration_level` (**Selection**): Level of integration (Get Rate, Get Rate and Create Shipment).
    *   `prod_environment` (**Boolean**): If true, uses the production environment for external providers.
    *   `product_id` (**Many2one**, Required): The service product used for invoicing the shipping cost.
    *   `tracking_url_template` (**Char**): URL template for tracking shipments.
    *   `invoice_policy` (**Selection**, Required): Policy for invoicing (e.g., Estimated cost).
    *   `margin` (**Float**): Percentage margin added to the shipping price.
    *   `fixed_margin` (**Float**): Fixed amount added to the shipping price.
    *   `free_over` (**Boolean**): If true, shipping is free if the order amount exceeds a certain value.
    *   `amount` (**Float**): The order amount threshold for free shipping.
    *   `shipping_insurance` (**Integer**): Percentage for shipping insurance calculation.

## 2. Stock Delivery (`stock_delivery`)

**Purpose**: Connects `stock.picking` with `delivery.carrier` to handle shipping labels and tracking numbers during the picking process.

### Key Models & Extensions

#### `stock.picking` (Extension)
*   **New Fields**:
    *   `carrier_id`: The selected shipping method.
    *   `carrier_tracking_ref`: The tracking number returned by the carrier API.
    *   `carrier_price`: The actual cost charged by the carrier.
    *   `weight`: Computed total weight of the picking.
*   **Key Logic**:
    *   `send_to_shipper()`: Calls the carrier's API to generate the label and tracking number.
    *   `print_return_label()`: Generates a return label if supported.

#### `stock.package.type` (Stock Package Type)
*   **Purpose**: Defines standard packaging types (boxes, pallets) with specific dimensions and weight limits.
*   **Fields**:
    *   `name` (**Char**, Required): The name of the package type.
    *   `sequence` (**Integer**): Sorting order.
    *   `height` (**Float**): Height of the package.
    *   `width` (**Float**): Width of the package.
    *   `packaging_length` (**Float**): Length of the package.
    *   `max_weight` (**Float**): Maximum weight the package can hold.
    *   `barcode` (**Char**): Barcode associated with this package type.

## 3. Stock Fleet (`stock_fleet`)

**Purpose**: Integrates Inventory with the Fleet module, allowing internal vehicles to be assigned to deliveries.

### Key Models & Extensions

#### `stock.picking` (Extension)
*   **New Fields**:
    *   `zip`: Destination zip code (for route optimization).

#### `fleet.vehicle.model` (Extension)
*   **Purpose**: Used to define the vehicle capacity if managing an internal fleet.
