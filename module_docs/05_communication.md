# Communication & UX

This document covers modules that enhance communication and user experience in inventory operations.

## Business Overview
This module improves customer experience by keeping them informed about the status of their physical shipments via text message.

### Key Features
*   **Automated SMS Notifications**: Trigger text messages automatically when a delivery leaves the warehouse.
*   **SMS Templates**: Customizable message content for different stages of delivery.
*   **Confirmation Requests**: Send SMS to confirm delivery receipt.

### Common Use Cases
*   **Logistics Companies** sending a text "Your package has left our facility" to reduce customer support inquiries.
*   **Food Delivery** services notifying customers the moment an order is out for delivery.

## Modules
*   `stock_sms`

## 1. Stock SMS (`stock_sms`)

**Purpose**: Automates sending SMS notifications to customers when their delivery is processed.

### Key Models & Extensions

#### `stock.picking` (Extension)
*   **Key Logic**:
    *   `_pre_action_done_hook()`: Intercepts the validation of a picking.
    *   `_check_warn_sms()`: Checks if the picking is an outgoing delivery, if the partner has a phone number, and if the company is configured to send SMS.
    *   `_action_generate_warn_sms_wizard()`: Opens a wizard to confirm sending the SMS.

#### `res.company` (Extension)
*   **New Fields**:
    *   `stock_move_sms_validation`: Boolean setting to enable SMS on delivery validation.
    *   `has_received_warning_stock_sms`: Tracks if the warning has been shown.
