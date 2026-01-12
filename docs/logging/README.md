# CodeVerse Bot Logging System

Welcome to the comprehensive documentation for the CodeVerse Bot Logging System. This system is designed to provide detailed, real-time tracking of server events, ensuring moderation transparency and server security.

## 📚 Documentation Structure

The documentation is split into specialized sections for clarity:

1.  **[Configuration & Setup](CONFIGURATION.md)**
    *   Learn how to configure log channels.
    *   View the current channel mapping for The CodeVerse Hub.
    *   Understand how to customize the logging environment.

2.  **[Event Reference](EVENTS_REFERENCE.md)**
    *   A complete list of all events tracked by the bot.
    *   Details on what information is captured for each event (Member, Channel, Role, Voice, Moderation).
    *   Examples of log output.

3.  **[Developer Guide](DEVELOPER_GUIDE.md)**
    *   Architectural overview (Mixins, Core, Config).
    *   How to add new event listeners.
    *   How to use the internal `log_event` API for other cogs.
    *   Customizing log formats.

## 🚀 Key Features

*   **Modular Architecture**: Split into specialized mixins (Members, Voice, Channels, etc.) for easier maintenance.
*   **Granular Logging**: Events are routed to specific channels based on their type (e.g., Kicks/Bans go to Moderation logs, Voice moves go to Voice logs).
*   **Robust Audit Log Linking**: Automatically attempts to fetch the responsible moderator for events via Discord Audit Logs.
*   **Webhook Integration**: Uses Webhooks for reliable delivery and custom user/avatar presentation.
*   **Database Persistence**: All logs are stored in a local SQLite database for permanent record-keeping.

## 🔗 Quick Links
*   [Return to Main Documentation](../README.md)
*   [Command Reference](../COMMAND_REFERENCE.md)
