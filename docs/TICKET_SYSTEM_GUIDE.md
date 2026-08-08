# Ticket System - Complete Guide

**Last Updated:** December 26, 2025

## Overview

The CodeVerse Bot ticket system provides a professional support mechanism using Discord threads. Users can create private tickets for support, reports, appeals, and more.

---

## Features

- ✅ Private thread-based tickets
- ✅ Category-based routing
- ✅ Role-specific notifications
- ✅ Ticket claiming system
- ✅ Automatic transcripts
- ✅ Persistent panels (survive bot restarts)
- ✅ Full logging integration
- ✅ Statistics tracking

---

## For Users

### How to Create a Ticket

1. Find the ticket panel (usually in #support or #tickets channel)
2. Click the **"Create Ticket"** button
3. Select a category from the dropdown menu:
   - **General Support** - Help with features, questions
   - **Role Issues** - Problems with roles or permissions
   - **Warn Appeals** - Appeal warnings or moderation actions
   - **Partnership** - Server partnership applications
   - **Reports** - Report rule violations or users
   - **Other Issues** - Anything else

4. Read the information about your selected category
5. Click **"Create This Ticket"** to confirm
6. A private thread will be created for you

### After Creating a Ticket

**What you'll see:**
- A new private thread with your ticket
- Only you and staff can see the thread
- Relevant staff members are pinged based on category
- Control buttons at the bottom (Close/Claim)

**What to do:**
- Explain your issue clearly
- Provide any relevant screenshots or links
- Be patient while staff review your ticket
- Respond to staff questions
- Close ticket when resolved (or staff will close it)

### Ticket Categories Explained

#### General Support
**Use for:**
- Questions about bot features
- Help using server features
- General assistance
- Account questions

**What to include:**
- Clear description of your question
- What you've already tried
- Relevant error messages

---

#### Role Issues
**Use for:**
- Missing roles
- Can't access channels
- Role color/icon problems
- Level-up role issues

**What to include:**
- Which role(s) are affected
- What you expected to happen
- Screenshots if applicable

---

#### Warn Appeals
**Use for:**
- Appealing a warning
- Disputing moderation action
- Explaining context of situation

**What to include:**
- Case ID (if known)
- Why you're appealing
- Any evidence supporting your appeal
- Understanding of rules

---

#### Partnership
**Use for:**
- Server partnership applications
- Community collaborations

**What to include:**
- Your server name and invite
- Member count and activity
- Server focus/topic
- Why partnership would benefit both communities

**Requirements (if any):**
- Check partnership terms in ticket info
- Meet minimum member/activity requirements
- SFW content only

---

#### Reports
**Use for:**
- Reporting rule violations
- Reporting inappropriate behavior
- Reporting spam or harassment

**What to include:**
- Username and ID of reported user
- What rule was violated
- Evidence (screenshots, message links)
- When it happened

---

#### Other Issues
**Use for:**
- Anything not covered above
- Feedback or suggestions
- Complex multi-category issues

---

## For Moderators

### Ticket Panel Setup

#### Creating a Panel

**Command:**
```
/ticket panel [channel] [support_role] [report_role] [partner_role] [color]
```

**Parameters:**
- `channel` - Channel to send panel (default: current channel)
- `support_role` - Role to ping for general tickets
- `report_role` - Role to ping for report tickets
- `partner_role` - Role to ping for partnership tickets
- `color` - Panel embed color: a hex code (`#00ff00`) or a named color (`blue`, `red`, `green`, ...) (default: blurple)

**Examples:**
```
/ticket panel channel:#support support_role:@Support report_role:@Moderator partner_role:@Manager
/ticket panel color:#00ff00
/ticket panel color:red
```

**What happens:**
- Panel embed is posted in channel
- "Create Ticket" button is added
- Panel is saved to database
- Roles are configured for pinging

---

### Managing Tickets

#### Claiming Tickets

**How to claim:**
1. Open the ticket thread
2. Click **"📌 Claim Ticket"** button
3. You're now assigned to the ticket

**Why claim:**
- Shows you're handling it
- Prevents duplicate responses
- Tracks who helped
- Looks professional

---

#### Closing Tickets

**How to close:**
1. Click **"🔒 Close Ticket"** button in thread
2. Provide close reason (optional)
3. Confirm closure

**What happens:**
- Thread is archived and locked
- User is notified
- Transcript is generated
- Ticket channel stays available for 24 hours after close so staff can review it without downloading the transcript
- Action is logged
- Ticket marked as closed in database

**When to close:**
- Issue is resolved
- User confirmed satisfaction
- User stopped responding
- Ticket is spam/invalid

---

### Ticket Commands

#### `/ticket list` - View All Tickets
**Usage:**
```
/ticket list [status] [user]
```

**Examples:**
```
/ticket list - All tickets
/ticket list open - Only open tickets
/ticket list closed - Only closed tickets
/ticket list open @user - User's open tickets
```

**Shows:**
- Ticket ID
- User who created it
- Category
- Status (open/closed)
- Created date
- Thread link

---

#### `/ticket stats` - Statistics
**Usage:**
```
/ticket stats
```

**Shows:**
- Total tickets created
- Currently open
- Closed tickets
- Tickets by category
- Average resolution time (if tracked)

---

#### `/ticket forceclose` - Force Close Ticket
**Usage:**
```
/ticket forceclose <ticket_id> [reason]
```

**When to use:**
- User deleted/left server
- Ticket is abandoned
- Spam ticket
- Thread manually deleted

**Example:**
```
/ticket forceclose 42 User left server
```

---

#### `/ticket log` - Configure Log Channel
**Usage:**
```
/ticket log [channel]
```

**Examples:**
```
/ticket log - View current log channel
/ticket log #ticketlog - Set log channel
```

**What's logged:**
- Ticket creation
- Ticket claims
- Ticket closures
- Force closures

---

#### `/ticket support` - Set Support Role
**Usage:**
```
/ticket support [role]
```

**Examples:**
```
/ticket support - View current role
/ticket support @Support - Set support role
```

**Purpose:** Role to ping for general support tickets

---

#### `/ticket report` - Set Report Team Role
**Usage:**
```
/ticket report [role]
```

**Purpose:** Role to ping for report tickets

---

#### `/ticket partner` - Set Partner Team Role
**Usage:**
```
/ticket partner [role]
```

**Purpose:** Role to ping for partnership tickets

---

### Responding to Tickets

#### Best Practices

**1. Acknowledge Quickly**
```
Thanks for creating a ticket! I'll look into this for you.
```

**2. Claim if Handling**
- Click claim button immediately
- Prevents confusion

**3. Ask Clarifying Questions**
```
Can you provide more details about [specific aspect]?
When did this start happening?
Do you have any screenshots?
```

**4. Provide Clear Solutions**
```
Here's how to fix this:
1. [Step one]
2. [Step two]
3. [Step three]

Let me know if this works!
```

**5. Confirm Resolution**
```
Has this resolved your issue?
Is there anything else you need help with?
```

**6. Close Properly**
- Always close resolved tickets
- Provide close reason
- Thank user for patience

---

### Handling Different Ticket Types

#### General Support Tickets
- Be patient and friendly
- Provide step-by-step instructions
- Offer to help if they get stuck
- Link to guides if available

#### Role Issue Tickets
- Check user's roles first
- Verify they meet requirements
- Add/fix roles if needed
- Explain role system if confused

#### Warn Appeal Tickets
- Stay objective and professional
- Review warning history
- Check evidence from both sides
- Consult other mods if needed
- Provide clear decision
- Explain reasoning

#### Partnership Tickets
- Review requirements
- Check server activity/members
- Verify content is appropriate
- Consult partnership team
- Provide feedback if denied

#### Report Tickets
- Take seriously
- Gather all evidence
- Investigate thoroughly
- Take appropriate action
- Update reporter
- Keep reporter anonymous if needed

---

## Database Structure

Tickets are stored with:
- Unique ticket ID
- Thread ID
- User ID
- Category
- Status (open/closed)
- Claimed by (moderator ID)
- Created timestamp
- Closed timestamp
- Close reason

---

## Troubleshooting

### Ticket Button Not Working
**Cause:** Bot restarted, view lost  
**Fix:** Run `/ticket panel` again or wait for bot to restore views

### User Can't Create Ticket
**Possible causes:**
- Already has open ticket
- No permissions in channel
- Bot missing permissions

**Check:**
- Verify user doesn't have open ticket
- Check channel permissions
- Verify bot has thread creation permissions

### Ticket Not Closing
**Possible causes:**
- Missing permissions
- Thread already archived
- Database error

**Fix:**
- Use `/ticket forceclose <ticket_id>`
- Check bot permissions
- Check logs for errors

### Roles Not Being Pinged
**Cause:** Roles not configured  
**Fix:** Use `/ticket support`, `/ticket report`, `/ticket partner` commands

---

## Tips for Admins

### Optimal Setup

**1. Create dedicated ticket channel**
```
#tickets or #support
```

**2. Set up roles**
- @Support - General tickets
- @Moderator - Reports
- @Manager - Partnerships

**3. Configure bot**
```
/ticket panel channel:#tickets support_role:@Support report_role:@Moderator partner_role:@Manager
/ticket log #ticketlog
```

**4. Set permissions**
- Users: View channel only
- Bot: All permissions
- Staff: Manage threads

### Maintenance

- **Weekly:** Check open tickets
- **Monthly:** Review ticket stats
- **As needed:** Update panel if roles change

### Monitoring

Use `/ticket stats` regularly to:
- Track ticket volume
- Identify busy categories
- Monitor response times
- Adjust staffing if needed

---

## FAQ

**Q: Can users create multiple tickets?**  
A: No, one open ticket at a time per user.

**Q: Are ticket transcripts saved?**  
A: Yes, transcripts are generated immediately on close (if configured), and the closed ticket channel remains available for 24 hours before it is deleted.

**Q: Can tickets be reopened?**  
A: No, user must create new ticket. Staff can reference old tickets.

**Q: Do panels survive bot restarts?**  
A: Yes, panels are stored in database and restored on startup.

**Q: Can I customize categories?**  
A: Currently, categories are hardcoded. Contact developer for changes.

**Q: What if thread is manually deleted?**  
A: Use `/ticket forceclose <ticket_id>` to mark as closed in database.

---

## Summary

The ticket system provides:
- ✅ Professional support experience
- ✅ Private, organized communication
- ✅ Full logging and tracking
- ✅ Role-based routing
- ✅ Easy management for staff

For additional help, create a ticket or contact an administrator!

**Last Updated:** December 26, 2025
