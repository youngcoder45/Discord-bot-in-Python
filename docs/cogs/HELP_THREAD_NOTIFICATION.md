# Help Thread Notification Cog

## Overview
The `HelpThreadNotification` cog is designed to monitor a specific forum channel for new threads. When a new thread is created, it sends a notification to a designated channel to alert staff or helpers. It also sends a confirmation message within the new thread to guide the user.

## Configuration
- **Source Forum ID**: `1388169643234955354` (The forum channel identifying new help requests)
- **Target Channel ID**: `1456979344504258570` (The channel where notifications are posted)

## Features

### 1. New Thread Notification
- **Trigger**: Creation of a new thread in the configured Source Forum.
- **Action**:
    - Generates an embed with the thread title, description (content of the starter message), author, and a link to the thread.
    - If the starter message has an image attachment, it is included in the embed.
    - If the thread has applied tags, they are listed in the embed.
    - Sends the notification to the Target Channel with a ping to `@here`.

### 2. User Guidance Message
- **Trigger**: Successful notification sent.
- **Action**:
    - Automatically replies in the newly created thread.
    - Confirms that help has been pinged.
    - Directs the user to a "How to ask" guide channel (`<#1456009038344093766>`).

## Implementation Details
- **Class**: `HelpThreadNotification(commands.Cog)`
- **Listener**: `on_thread_create(thread)`
- **Key Logic**:
    - Checks `thread.parent_id` to ensure it matches `source_forum_id`.
    - Retries fetching the starter message if it's not immediately available in the cache.
    - Handles potential `discord.NotFound` errors for channels.

## Usage
This cog is automatic and does not have user-invokable commands. It relies on the `on_thread_create` event.
