# Thread Management Cog

## Overview
The `ThreadCloser` (or `thread.py`) cog manages thread interactions, primarily focused on closing/archiving threads and pinning messages. It allows for "ticket-style" management of threads even if they aren't part of the formal ticket system, often used in forum channels.

## Commands

### 1. Close Thread
- **Command**: `?close` (Aliases: `?close_thread`, `?archive`)
- **Usage**: 
    - Inside a thread: `?close`
    - Outside: `?close <thread_id>`
- **Description**: Archives the specified thread.
- **Logic**:
    - If the thread is a ticket from the ticket system, it updates the database and logs the closure.
    - If it's a regular thread, it simply archives it.

### 2. Pin Message
- **Command**: `?pin <message_id>`
- **Permissions**: `Manage Messages`
- **Description**: Pins a message in the current thread or channel. If `message_id` is provided, pins that specific message. If referenced in a reply, pins the replied-to message.

### 3. Unpin Message
- **Command**: `?unpin <message_id>`
- **Permissions**: `Manage Messages`
- **Description**: Unpins a message in the current thread or channel.

## Dependencies
- Interacts with the `tickets` table if the thread being closed is identified as a ticket.

## Implementation Details
- **Class**: `ThreadCloser(commands.Cog)`
- **Thread Resolution**: Helper method `_resolve_thread` safely identifies the target thread from context or arguments.
