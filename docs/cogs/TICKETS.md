# Tickets System Cog

## Overview
The `Tickets` cog provides a comprehensive ticket system using Discord Threads. It supports multiple categories, persistent creation panels, team roles for different categories, and logging.

## Features

### 1. Ticket Categories
The system supports specific categories for organizing requests:
- **Partnership**
- **General Support**
- **Role Issues**
- **Reports**
- **Warn Appeals**
- **Other Issues**

### 2. Ticket Lifecycle
- **Creation**: Users interact with a persistent "Create Ticket" button on a panel. They select a category via a dropdown.
- **Thread Creation**: A private thread (or public if private not supported) is created.
- **Management**: 
    - **Claiming**: Staff can generic "Claim" the ticket.
    - **Closing**: Tickets can be closed, which logs the closure and archives the thread.

### 3. Views
- `TicketPanelView`: The persistent "Create Ticket" button.
- `TicketCategoryView`: Dropdown to select the ticket type.
- `TicketConfirmationView`: Final confirmation before creating the thread.
- `TicketControlView`: Persistent buttons inside the ticket thread (`Close`, `Claim`).

### 4. Database
- **`tickets`**: Stores active and closed tickets.
- **`ticket_panels`**: Tracks where creation panels are posted to restore views on restart.
- **`ticket_log_channels`**: Custom log channels per guild.
- **Team Tables**: `ticket_support_roles`, `ticket_report_roles`, `ticket_partner_roles` specific roles that get pinged/access for different categories.

## Commands (Deduced)
While explicit commands weren't fully visible in the snippet, the system implies:
- Setup commands to place the `TicketPanelView`.
- Commands to configure support roles (`tickets_support_roles`, etc.).

## Startup Logic
- `_restore_persistent_views()`: Runs on bot startup. Queries the database for existing panels and re-attaches the `TicketPanelView` to ensure buttons work after a reboot.

## Configuration
- **Staff Role ID**: Hardcoded default `1417900662053671073` (Configurable via code).
