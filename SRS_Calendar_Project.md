# Calendar

## Software Requirement Specification

**Spring 2026**

**Version 2.0**

**Project Manager:** Dominic

**Software Engineer:** Charlize

**Software Engineer:** Owen

**Software Engineer:** Hector

**Software Engineer:** Eric

**Software Engineer:** Nathan

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [1.1. Purpose](#11-purpose)
   - [1.2. Scope](#12-scope)
   - [1.3. Definitions, Acronyms, Abbreviations](#13-definitions-acronyms-abbreviations)
   - [1.4. References](#14-references)
2. [Overall Description](#2-overall-description)
   - [2.1. Product Perspectives](#21-product-perspectives)
     - [2.1.1. System Interfaces](#211-system-interfaces-deployment-diagram)
     - [2.1.2. User Interfaces](#212-user-interfaces)
     - [2.1.3. Software Interfaces](#213-software-interfaces)
   - [2.2. Product Functions](#22-product-functions-use-case-diagram)
   - [2.3. User Characteristics](#23-user-characteristics)
   - [2.4. Constraints](#24-constraints)
   - [2.5. Assumptions and Dependencies](#25-assumptions-and-dependencies)
3. [Specific Requirements](#3-specific-requirements)
   - [3.1. External Interface Requirements](#31-external-interface-requirements)
     - [3.1.1. User Interfaces](#311-user-interfaces)
     - [3.1.2. Hardware Interfaces](#312-hardware-interfaces)
     - [3.1.3. Software Interfaces](#313-software-interfaces)
     - [3.1.4. Communication Interfaces](#314-communication-interfaces)
   - [3.2. Functional Requirements](#32-functional-requirements)
     - [3.2.1. User is Signed Out](#321-user-is-signed-out)
     - [3.2.2. User is Signed In](#322-user-is-signed-in)
     - [3.2.3. Admin is Signed In](#323-admin-is-signed-in)
     - [3.2.4. Guest User](#324-guest-user)
     - [3.2.5. Mis-Use Cases](#325-mis-use-cases)
   - [3.3. Performance Requirements](#33-performance-requirements)
   - [3.4. Design Constraints](#34-design-constraints)

---

## 1. Introduction

### 1.1. Purpose

This SRS (Software Requirements Specification) document outlines the specific software needs and requirements for the Calendar web application. The requirements described in this document must be met and tested by the end of the CPSC 362 Software Engineering course in Spring 2026.

### 1.2. Scope

Calendar is a web based calendar management application. Users can organize events, share calendars with friends, and connect to external calendar providers like Google Calendar. The app has a full user interface for regular browsing and also a REST API for syncing data. Everything is stored in a Supabase database and the app is deployed to Vercel.

For a full overview of what the system can do, refer to the Use Case Diagram in Section 2.2.

**Prototype 1:**

- **Authentication:** Users can register with an email and password, log in to an existing account, and log out. Email verification is required before a user can log in.
- **Calendar Management:** Authenticated users can create calendars, view events on each calendar, and delete calendars they own.

**Final Product:**

- **Event Management:** Users can create, view, edit, and delete events on calendars they own or are a member of.
- **Friends:** Users can view a friends list and add or remove friends from their account.
- **Guest Links:** Calendar owners can generate a shareable guest link. The link can be set to viewer or editor role. This lets people without an account access a calendar. Guest editors can also create, edit, and delete events on the shared calendar.
- **External Calendar Integration:** Users can link a Google Calendar account or an Outlook (Microsoft) account. They can pull events from either provider into a local synced calendar, push local calendars back to the provider, and disconnect the account at any time.
- **Settings:** Users can manage their connected external calendar providers from the settings page.
- **Admin Panel:** Administrators can view system logs, suspend user accounts, send system wide notifications, and unlink all external calendars.

### 1.3. Definitions, Acronyms, Abbreviations

**Program** -- A set of steps a computer runs to complete a task.

**Application** -- A program that lets users interact with a GUI and a server over the internet to do something useful.

**Software** -- Programs and other information used by a computer.

**Computer** -- A device for processing and storing data.

**GUI or UI** -- Graphical User Interface. It is the visual part of the app that users click and interact with.

**SRS** -- Software Requirements Specification. That is this document.

**Home Page** -- The web page users see after they log in.

**Web Application** -- A program that runs on a server and is accessed through a web browser. Usually written with HTML, CSS, and JavaScript.

**HTML** -- Hypertext Markup Language. Used to build the structure of web pages.

**CSS** -- Cascading Style Sheets. Used to style HTML elements so the site looks good.

**Python** -- A programming language. We use it for the server side backend.

**Flask** -- A Python web framework. It handles routing and request processing.

**Database** -- A structured collection of data stored on a computer.

**User Credentials** -- A user's email address and password used to sign in.

**Supabase** -- An open source backend platform that gives us a PostgreSQL database and authentication. We use it instead of Firebase.

**JWT** -- JSON Web Token. A token used to represent an authenticated session.

**RLS** -- Row Level Security. A Supabase feature that restricts database rows so users can only see their own data.

**Bearer Token** -- An access token sent in the HTTP Authorization header to authenticate API requests.

**REST** -- Representational State Transfer. An architectural style for building HTTP APIs.

**OAuth** -- An open authorization standard. It lets our app get access to a user's data on a third party service like Google Calendar.

**CRUD** -- Create, Read, Update, Delete. The four basic things you can do with data.

**UUID** -- Universally Unique Identifier. We use these as primary keys throughout the database.

**Vercel** -- A cloud platform we use to deploy the Calendar app as a serverless function.

**Guest Link** -- A shareable URL token that lets unauthenticated users access a specific calendar.

**UID** -- User ID. Uniquely identifies a user in the system.

**Front End** -- The part of the app that users see and interact with directly.

**Back End** -- The server side part of the app. Users do not see this. It handles data, logic, and authentication.

### 1.4. References

Supabase. "Supabase Documentation." Supabase, 2025, supabase.com/docs.

Pallets Projects. "Flask Documentation." Flask, 2025, flask.palletsprojects.com.

GitHub. "GitHub." GitHub, 2025, github.com.

Vercel. "Vercel Documentation." Vercel, 2025, vercel.com/docs.

Google. "Google Calendar API." Google Developers, 2025, developers.google.com/calendar.

Microsoft. "Microsoft Graph API." Microsoft Docs, 2025, learn.microsoft.com/en-us/graph/overview.

---

## 2. Overall Description

### 2.1. Product Perspectives

#### 2.1.1. System Interfaces (Deployment Diagram)

For the front end, Calendar uses Jinja2 server rendered HTML pages that are styled with CSS. All pages are generated by the Flask server and sent to the user's browser. We chose this approach to keep things simple and avoid having a separate JavaScript framework.

The back end is a Python Flask application that has three main parts: an auth blueprint, a REST API blueprint, and a UI blueprint. The app is deployed to Vercel as a Python serverless function. Supabase handles user authentication and the PostgreSQL database. Flask communicates with Supabase over HTTPS using the Supabase Python client library.

*(Figure 1: Deployment Diagram showing Web Client to Flask on Vercel to Supabase Auth and PostgreSQL Database)*

#### 2.1.2. User Interfaces

**User is signed out:**

- When a user first visits the site they are sent to the login page. If they do not have an account they can click the "Register" link to create one.
- To register, they just need a valid email address and a password. The form will show an error if a field is empty or if the passwords do not match.
- After registering, a verification email is sent and the user has to verify it before they can log in.

**User is signed in:**

- After logging in, the user is taken to the home page which shows their calendars and events.
- Users can create and delete calendars, and also create, edit, and delete events on those calendars.
- Users can manage friends, connect external calendar providers through the settings page, and log out from the navigation menu.

**Admin is signed in:**

- Admins have access to an admin panel. From there they can view system logs, suspend users, send notifications to everyone, and unlink external calendars.

**Guest user:**

- A guest user with a valid guest link can view a shared calendar and its events. If the link is set to editor role they can also create, edit, and delete events on that calendar.

#### 2.1.3. Software Interfaces

1. **Visual Studio Code** -- The main code editor we used to write the application.
   - **Front End** -- Jinja2 templates, HTML, and CSS for the server rendered UI.
   - **Back End** -- Python and Flask for routing, business logic, and database communication.

2. **Supabase** -- Used to handle authentication and data storage.
   - **Authentication** -- Stores user credentials, creates JWTs, and validates sessions.
   - **Database** -- PostgreSQL database with tables for calendars, events, externals, users, and logs.

3. **Vercel** -- Hosts the Flask app as a serverless Python function and handles HTTPS.

4. **Google Calendar API** -- Used for the Google external calendar integration. The app requests access to the user's Google Calendar to pull and push events.

5. **Microsoft Graph API** -- Used for the Outlook external calendar integration. The app requests access to the user's Outlook calendar through Microsoft's Graph API to pull and push events.

### 2.2. Product Functions (Use Case Diagram)

Calendar lets authenticated users manage calendars and events, connect external calendar accounts (Google or Outlook), manage friends, and create shareable guest links. Calendar owners can share calendars publicly using a guest link that grants either viewer or editor access. Admins have extra tools for managing the whole system. The Use Case Diagram (Figure 2) shows all the use cases across all three actors.

*(Figure 2: Use Case Diagram -- See Section 3.2 for full use case specifications)*

The diagram includes the following numbered use cases:

**User Signed Out:** AU 01 Register Account, AU 02 Login to Account

**User Signed In:** AU 03 Log Out, UA 01 Remove Account, VC 01 View Calendar, VE 01 View Event, CM 01 Manage Calendars (includes CM 02 Create Calendar, CM 03 Add Member, CM 04 Remove Member, CM 05 Remove Calendar, CM 06 Manage Events (includes EM 01 Create Event, EM 02 Edit Event, EM 03 Remove Event)), EX 01 Manage Externals (includes EX 02 Pull Data from External Calendar, EX 03 Push Data to External Calendar, EX 04 Link External Calendar, EX 05 Unlink External Calendar), FM 01 Manage Friends (includes FM 02 View Friends List, FM 03 Add Friend, FM 04 Remove Friend), GL 01 Generate Guest Link

**Admin Signed In (extends User Signed In):** AD 01 Suspend User Account, AD 02 View System Logs, AD 03 Send System Wide Notification, AD 04 Unlink All External Calendars

**Guest User (via Guest Link):** GL 02 View Shared Calendar, GL 03 Create Event on Shared Calendar, GL 04 Edit Event on Shared Calendar, GL 05 Delete Event on Shared Calendar

### 2.3. User Characteristics

The Use Case Diagram (Figure 2) shows three actors:

- **Guest User** -- An unauthenticated user who either has not made an account yet or is accessing a shared calendar through a guest link token. If they are accessing a shared calendar, they can view events. If the guest link has an editor role they can also create, edit, and delete events on that calendar.
- **User** -- A registered and logged in user. They can log in and out, manage calendars and events, add and remove calendar members, generate guest links, connect external calendar providers, manage friends, and delete their own account.
- **Admin** -- A registered user with the "admin" role set in Supabase. Admins can do everything a regular user can, plus they have access to system level tools like viewing logs, suspending user accounts, sending system wide notifications, and unlinking all external calendars. Admin status can only be set directly in Supabase by a project administrator.

### 2.4. Constraints

- All environment variables like SUPABASE_URL, SUPABASE_KEY, FLASK_SECRET_KEY, APP_BASE_URL, GOOGLE_CLIENT_ID, and GOOGLE_CLIENT_SECRET must be set in Vercel and should never be hardcoded in source files.
- The Supabase schema needs to have the calendars, events, externals, users, and logs tables set up with the right columns and Row Level Security policies.
- CORS origins need to be updated in the index file when deploying to a new domain.
- Google Calendar OAuth needs valid credentials registered in Google Cloud Console, set through GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.
- Outlook calendar OAuth needs valid credentials registered in Azure, set through MS_CLIENT_ID and MS_CLIENT_SECRET.
- Time constraints are a factor since this is a student project and everyone has other class responsibilities.
- The app needs to be accessible through a web browser with an internet connection.

### 2.5. Assumptions and Dependencies

- We assume Supabase services are working and no outages happen while the app is being used.
- Users have internet access and a web browser.
- Users can read and understand English to use the app.
- Google Calendar and Outlook OAuth tokens are valid and have not been revoked by the user on the provider's end.
- The Vercel deployment correctly resolves APP_BASE_URL for OAuth redirect URIs.
- Admin status is set in Supabase app metadata and cannot be set by a regular user through any page in the app.

---

## 3. Specific Requirements

### 3.1. External Interface Requirements

#### 3.1.1. User Interfaces

Calendar's user interface is made up of server rendered HTML pages built with Jinja2 templates and styled with CSS. There are two base layouts: one for logged in users with a navigation bar, and one for guest pages. All forms validate required fields and show flash messages to tell the user if something worked or went wrong.

#### 3.1.2. Hardware Interfaces

The user needs a computer with a monitor, keyboard, and mouse or trackpad. No special hardware is required. The device just needs to be able to run a modern web browser.

#### 3.1.3. Software Interfaces

Calendar uses the Supabase Python client library to handle all authentication and database operations. For UI routes specifically, we also call the auth method on the client with the user's token so that Row Level Security policies apply to all queries. Both Google and Outlook OAuth flows are handled through the requests_oauthlib library.

#### 3.1.4. Communication Interfaces

The Flask app talks to Supabase over HTTPS. Browsers talk to Flask over HTTP in development and HTTPS in production. The REST API sends and receives JSON. The server rendered UI uses standard HTML form submissions. Bearer tokens are sent in the HTTP Authorization header for REST API routes. Flask session cookies keep users logged in for UI routes.

### 3.2. Functional Requirements

Functional requirements are organized by user state and match the numbered use cases in the Use Case Diagram (Figure 2). Each use case specification includes the actor, preconditions, main flow, alternate flow, and postconditions.

---

#### 3.2.1. User is Signed Out

##### 3.2.1.1. AU 01: Register Account

Users who do not have an account can create one on the registration page (Figure 3) by clicking the "Register" link on the login page.

*(Figure 3: Register Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | AU 01 |
| **Use Case Name** | Register Account |
| **Actor** | Guest User |
| **Precondition** | The user does not have an existing account and is not logged in. |
| **Main Flow** | 1. User navigates to /ui/register. 2. User enters a display name (optional), email address, password, and password confirmation. 3. App checks that email and password fields are not empty and that the two password fields match. 4. App submits the registration to Supabase Auth, which sends a verification email. 5. App sends the user back to the login page with a confirmation message. |
| **Alternate Flow** | If the email or password field is empty, the app shows: "Email and password are required." If the passwords do not match, the app shows: "PASSWORDS DON'T MATCH." If Supabase returns an error like email already registered, the app shows that error message. |
| **Postcondition** | A new user account is created in Supabase Auth. The user gets a verification email and must verify it before they can log in. |

---

##### 3.2.1.2. AU 02: Login to Account

If a user already has an account they can log in on the login page (Figure 4). This is the first page users see when they visit the site.

*(Figure 4: Login Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | AU 02 |
| **Use Case Name** | Login to Account |
| **Actor** | Guest User |
| **Precondition** | The user has a verified account and is not currently logged in. |
| **Main Flow** | 1. User navigates to /ui/login. 2. User enters their email address and password and submits the form. 3. App sends the credentials to Supabase Auth for verification. 4. App saves the user's ID, email, access token, and role in the Flask session. 5. App sends the user to the home page. |
| **Alternate Flow** | If either field is empty, the app shows: "Email and password are required." If Supabase returns an authentication failure, the app shows: "Wrong email or password." |
| **Postcondition** | The user's session is created. The user is redirected to the home page. |

---

#### 3.2.2. User is Signed In

##### 3.2.2.1. AU 03: Log Out

Users can log out at any time using the logout link in the navigation menu.

| Field | Detail |
|---|---|
| **Use Case ID** | AU 03 |
| **Use Case Name** | Log Out |
| **Actor** | User, Admin |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User clicks the logout link in the navigation bar. 2. App clears the session data. 3. App sends the user to the login page. |
| **Alternate Flow** | None. |
| **Postcondition** | The user's session is cleared and they are treated as unauthenticated. |

---

##### 3.2.2.2. UA 01: Remove Account

If a user wants to delete their account they can do so from the account settings page accessible through the navigation menu (Figure 5).

*(Figure 5: Remove Account Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | UA 01 |
| **Use Case Name** | Remove Account |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to /ui/user/remove-account. 2. User confirms they want to delete their account. 3. App removes the user's account and associated data from Supabase. 4. App clears the session and sends the user to the login page. |
| **Alternate Flow** | If the user cancels the action, nothing changes and they go back to the previous page. |
| **Postcondition** | The user's account is deleted from Supabase and their session is cleared. |

---

##### 3.2.2.3. VC 01: View Calendar

Once logged in, users are taken to the home page (Figure 6) where they can see their calendars and switch between them.

*(Figure 6: Home Page with Calendar View)*

| Field | Detail |
|---|---|
| **Use Case ID** | VC 01 |
| **Use Case Name** | View Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has at least one calendar. |
| **Main Flow** | 1. User navigates to /ui/ which is the home page. 2. App fetches all calendars owned by the user or where the user is a member. 3. App shows the first calendar by default. The user can switch to other calendars using a selector. 4. App fetches and shows all events for the selected calendar. |
| **Alternate Flow** | If the user has no calendars, the app shows a message prompting the user to create one. If events fail to load, the app shows an error message. |
| **Postcondition** | The user can see the selected calendar and its events. |

---

##### 3.2.2.4. VE 01: View Event

Users can view events on a selected calendar from the home page (Figure 6) or the Manage Events page (Figure 9).

| Field | Detail |
|---|---|
| **Use Case ID** | VE 01 |
| **Use Case Name** | View Event |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to a calendar that has events. |
| **Main Flow** | 1. User goes to the home page or the Manage Events page. 2. App fetches all events for the selected calendar. 3. App shows each event's title, description, and start and end times. |
| **Alternate Flow** | If the calendar has no events, the app shows a message saying the calendar is empty. |
| **Postcondition** | The user sees a list of events for the selected calendar. |

---

##### 3.2.2.5. CM 01: Manage Calendars

Logged in users can manage their calendars from the Manage Calendars page (Figure 7). This use case covers creating calendars, managing members, and deleting calendars. It also includes the Manage Events sub use case.

*(Figure 7: Manage Calendars Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | CM 01 |
| **Use Case Name** | Manage Calendars |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to /ui/user/calendars. 2. App fetches all calendars owned by the user. 3. App shows each calendar with options for creating new ones, editing membership, generating guest links, and deleting. |
| **Alternate Flow** | If the calendars list fails to load, the app shows an error message. |
| **Postcondition** | The user can see all their calendars and take action on them. |

---

##### 3.2.2.6. CM 02: Create Calendar

From the Manage Calendars page (Figure 7), users can create a new calendar.

| Field | Detail |
|---|---|
| **Use Case ID** | CM 02 |
| **Use Case Name** | Create Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by CM 01. |
| **Main Flow** | 1. User types a calendar name on the Manage Calendars page and submits the form. 2. App creates the calendar in Supabase and sets the user as the owner. 3. App shows the updated calendar list with a success message. |
| **Alternate Flow** | If the name field is empty, the app shows a validation error. |
| **Postcondition** | A new calendar record is created in the calendars table with the requesting user set as owner. |

---

##### 3.2.2.7. CM 03: Add Member

Calendar owners can add other users as members to a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 03 |
| **Use Case Name** | Add Member |
| **Actor** | User |
| **Precondition** | The user is logged in and owns the calendar. Included by CM 01. |
| **Main Flow** | 1. User enters the target user's ID in the Add Member field and submits. 2. App checks that the target user exists. 3. App adds the target user's ID to the calendar's member IDs list. 4. App shows a success message. |
| **Alternate Flow** | If the target user does not exist, the app shows an error. If the user is already a member, the app notifies the owner. |
| **Postcondition** | The target user's ID is added to the calendar's member list and they can now view the calendar. |

---

##### 3.2.2.8. CM 04: Remove Member

Calendar owners can remove members from a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 04 |
| **Use Case Name** | Remove Member |
| **Actor** | User |
| **Precondition** | The user is logged in, owns the calendar, and the target member is in the member list. Included by CM 01. |
| **Main Flow** | 1. User selects a member to remove from the member list on the Manage Calendars page. 2. App removes the target user's ID from the calendar's member list. 3. App shows a success message. |
| **Alternate Flow** | If the member ID is not found in the calendar's member list, the app shows an error. |
| **Postcondition** | The target user's ID is removed from the member list and they can no longer access the calendar. |

---

##### 3.2.2.9. CM 05: Remove Calendar

Calendar owners can delete a calendar they own from the Manage Calendars page (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 05 |
| **Use Case Name** | Remove Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and owns the calendar. Included by CM 01. |
| **Main Flow** | 1. User selects a calendar and confirms the delete action. 2. App checks that the user is the calendar owner. 3. App removes the calendar record from Supabase. 4. App shows the updated list with a success message. |
| **Alternate Flow** | If the user is not the owner, the app returns an authorization error. |
| **Postcondition** | The calendar record is removed from the calendars table. |

---

##### 3.2.2.10. GL 01: Generate Guest Link

Calendar owners can generate a shareable guest link that lets unauthenticated users access a calendar (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 01 |
| **Use Case Name** | Generate Guest Link |
| **Actor** | User |
| **Precondition** | The user is logged in and owns the calendar. |
| **Main Flow** | 1. User selects a role (viewer or editor) on the Manage Calendars page and activates the guest link. 2. App generates a random token and stores it in the calendar record along with the selected role and an active flag. 3. App shows the full shareable URL to the user. |
| **Alternate Flow** | If the owner deactivates the guest link, the active flag is set to false and the URL no longer works. |
| **Postcondition** | The calendar record is updated with the guest link token, role, and active status. Unauthenticated users can now access the calendar through the generated URL. |

---

##### 3.2.2.11. CM 06: Manage Events

Users can manage events on their calendars from the Manage Events page (Figure 8). This use case is included by CM 01 and includes the Create Event, Edit Event, and Remove Event sub use cases.

*(Figure 8: Manage Events Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | CM 06 |
| **Use Case Name** | Manage Events |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to at least one calendar. Included by CM 01. |
| **Main Flow** | 1. User navigates to /ui/user/events. 2. App fetches the user's calendars. 3. App shows events for the selected calendar with options to create, edit, and delete events. |
| **Alternate Flow** | If the user has no calendars, the app shows a message and tells the user to create one first. |
| **Postcondition** | The user can view and manage events for the selected calendar. |

---

##### 3.2.2.12. EM 01: Create Event

From the Manage Events page (Figure 8), users can create a new event on a calendar they have access to.

| Field | Detail |
|---|---|
| **Use Case ID** | EM 01 |
| **Use Case Name** | Create Event |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to at least one calendar. Included by CM 06. |
| **Main Flow** | 1. User enters a title, optional description, start time, and end time, then selects a target calendar and submits. 2. App validates the required fields. 3. App creates the event in Supabase and links it to the selected calendar. 4. App shows the updated event list with a success message. |
| **Alternate Flow** | If the title is missing, the app shows a validation error. If the user does not have access to the selected calendar, the app returns an authorization error. |
| **Postcondition** | A new event record is created in the events table with the requesting user as owner. |

---

##### 3.2.2.13. EM 02: Edit Event

Event owners can edit the details of their events from the Edit Event page (Figure 9).

*(Figure 9: Edit Event Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | EM 02 |
| **Use Case Name** | Edit Event |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the event. Included by CM 06. |
| **Main Flow** | 1. User selects an event to edit on the Manage Events page and is taken to the edit page. 2. App loads the existing event data into the form. 3. User changes the title, description, start or end time, or calendars and submits. 4. App updates the event record in Supabase. 5. App sends the user back to the events list with a success message. |
| **Alternate Flow** | If the user is not the event owner, the app redirects to the events list with an error. If required fields are missing, the app shows a validation error. |
| **Postcondition** | The event record in the events table is updated with the new values. |

---

##### 3.2.2.14. EM 03: Remove Event

Event owners can delete their events from the Manage Events page (Figure 8).

| Field | Detail |
|---|---|
| **Use Case ID** | EM 03 |
| **Use Case Name** | Remove Event |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the event. Included by CM 06. |
| **Main Flow** | 1. User selects an event on the Manage Events page and confirms the delete action. 2. App checks ownership. 3. App removes the event record from Supabase. 4. App shows the updated event list with a success message. |
| **Alternate Flow** | If the user is not the event owner, the app returns an authorization error. |
| **Postcondition** | The event record is removed from the events table. |

---

##### 3.2.2.15. EX 01: Manage Externals

Logged in users can view and manage their connected external calendar providers from the Settings page (Figure 10). The app supports Google Calendar and Outlook (Microsoft). This use case includes the sub use cases for linking, pulling, pushing, and unlinking external calendars.

*(Figure 10: Settings Page with External Calendars)*

| Field | Detail |
|---|---|
| **Use Case ID** | EX 01 |
| **Use Case Name** | Manage Externals |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to /ui/settings. 2. App fetches all external calendar records for the user and separates them by provider (Google and Outlook). 3. App shows each provider's connections with options to pull, push, and unlink. |
| **Alternate Flow** | If no external connections exist, the app shows a prompt to connect a provider. |
| **Postcondition** | The user can see their connected external providers and take action on them. |

---

##### 3.2.2.16. EX 02: Pull Data from External Calendar

Users can import events from a connected external calendar into a local calendar (Figure 10).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 02 |
| **Use Case Name** | Pull Data from External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has a linked external calendar (Google or Outlook). Included by EX 01. |
| **Main Flow** | 1. User clicks the sync option next to a connected provider on the Settings page. 2. App fetches events from that provider using the stored access token. 3. For Google, the app creates or updates a local calendar called "Google Calendar (Synced)." For Outlook, the app creates or updates a local calendar called "Outlook Calendar (Synced)." 4. App shows a success message with the number of synced events. |
| **Alternate Flow** | If the access token is expired, the app tries to refresh it automatically. If the refresh fails, the app shows an error and asks the user to reconnect. |
| **Postcondition** | A local synced calendar is created or updated with events pulled from the external provider. |

---

##### 3.2.2.17. EX 03: Push Data to External Calendar

Users can export their local calendars to a connected external calendar provider (Figure 10).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 03 |
| **Use Case Name** | Push Data to External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in, has a linked external calendar (Google or Outlook), and has at least one local calendar to export. Included by EX 01. |
| **Main Flow** | 1. User clicks the push option next to a connected provider on the Settings page. 2. App sends all local calendars owned by the user (excluding the provider's own synced calendar) to the external provider using the stored access token. 3. App shows a success message with the number of events pushed. |
| **Alternate Flow** | If the access token is expired, the app tries to refresh it automatically. If the refresh fails, the app shows an error and asks the user to reconnect. |
| **Postcondition** | The user's local calendar events are sent to the external provider. |

---

##### 3.2.2.18. EX 04: Link External Calendar

Users can link a new external calendar provider account from the Settings page (Figure 10). Both Google Calendar and Outlook are supported.

| Field | Detail |
|---|---|
| **Use Case ID** | EX 04 |
| **Use Case Name** | Link External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in. Valid OAuth credentials are configured in the app environment for the chosen provider. Included by EX 01. |
| **Main Flow** | 1. User navigates to /ui/settings and clicks "Connect Google Calendar" or "Connect Outlook Calendar." 2. App starts the OAuth 2.0 flow and sends the user to the provider's authorization page (Google or Microsoft). 3. User grants calendar permissions. 4. The provider redirects back to the app with an authorization code. 5. App exchanges the code for access and refresh tokens and saves them in the externals table with the correct provider label. 6. App sends the user back to the Settings page with a success message. |
| **Alternate Flow** | If the user denies the permissions request, the app returns to Settings with an error message. If OAuth credentials are missing from the environment, the app shows an error telling the user which environment variables are not set. If the OAuth state does not match when the provider redirects back, the app shows a state mismatch error. |
| **Postcondition** | A new record is added to the externals table with the user's access token and refresh token for the chosen provider. |

---

##### 3.2.2.19. EX 05: Unlink External Calendar

Users can disconnect a connected external calendar provider from their account via the Settings page (Figure 10).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 05 |
| **Use Case Name** | Unlink External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has at least one linked external calendar. Included by EX 01. |
| **Main Flow** | 1. User navigates to /ui/settings and clicks "Disconnect" next to the provider. 2. App removes the external record from the externals table. 3. App shows a success message. |
| **Alternate Flow** | If the external record cannot be found, the app shows an error message. |
| **Postcondition** | The external calendar record is removed from the externals table. |

---

##### 3.2.2.20. FM 01: Manage Friends

Logged in users can manage their friends list from the Manage Friends page (Figure 11). This use case includes viewing, adding, and removing friends.

*(Figure 11: Manage Friends Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | FM 01 |
| **Use Case Name** | Manage Friends |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to /ui/user/friends. 2. App fetches the user's friends list from Supabase. 3. App shows each friend with options to add and remove friends. |
| **Alternate Flow** | If the friends list fails to load, the app shows an error message. |
| **Postcondition** | The user can see their friends list and take action on it. |

---

##### 3.2.2.21. FM 02: View Friends List

Users can view their current list of friends from the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 02 |
| **Use Case Name** | View Friends List |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by FM 01. |
| **Main Flow** | 1. App fetches the user's friends list from Supabase. 2. App looks up each friend's display name and email. 3. App shows the list. |
| **Alternate Flow** | If the friends list is empty, the app shows a message saying no friends have been added yet. |
| **Postcondition** | The user sees their current friends with display names and emails. |

---

##### 3.2.2.22. FM 03: Add Friend

Users can add another user as a friend from the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 03 |
| **Use Case Name** | Add Friend |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by FM 01. |
| **Main Flow** | 1. User enters the target user's ID or email in the Add Friend field and submits. 2. App checks that the target user exists. 3. App adds the target user's ID to the requesting user's friends list in Supabase. 4. App shows a success message. |
| **Alternate Flow** | If the target user does not exist, the app shows an error. If the user is already in the friends list, the app notifies the user. |
| **Postcondition** | The target user's ID is added to the user's friends list. |

---

##### 3.2.2.23. FM 04: Remove Friend

Users can remove a friend from their friends list on the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 04 |
| **Use Case Name** | Remove Friend |
| **Actor** | User |
| **Precondition** | The user is logged in and the target user is in their friends list. Included by FM 01. |
| **Main Flow** | 1. User selects a friend to remove on the Manage Friends page. 2. App removes the target user's ID from the requesting user's friends list in Supabase. 3. App shows the updated friends list with a success message. |
| **Alternate Flow** | If the target user's ID is not found in the friends list, the app shows an error. |
| **Postcondition** | The target user's ID is removed from the user's friends list. |

---

#### 3.2.3. Admin is Signed In

The Admin actor extends the User actor. All use cases available to a regular User are also available to an Admin. The following use cases are exclusive to the Admin role. Admin status is checked on every admin route through a special decorator.

##### 3.2.3.1. AD 01: Suspend User Account

Administrators can suspend a user account, which removes the user's calendars and external calendar connections (Figure 12).

*(Figure 12: Admin Panel with Suspend User Section)*

| Field | Detail |
|---|---|
| **Use Case ID** | AD 01 |
| **Use Case Name** | Suspend User Account |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the admin role. The target user account exists. |
| **Main Flow** | 1. Admin goes to the suspend user section of the admin panel. 2. Admin enters the target user's ID and confirms the suspension. 3. App removes all calendars owned by the target user. 4. App removes all external calendar records for the target user. 5. App shows a success message. |
| **Alternate Flow** | If the target user ID does not exist, the app shows an error. If the requesting user does not have the admin role, the app returns HTTP 403. |
| **Postcondition** | The target user's calendars and externals are deleted from the database. |

---

##### 3.2.3.2. AD 02: View System Logs

Administrators can view application level request and event logs from the admin panel (Figure 13).

*(Figure 13: Admin Panel with System Logs)*

| Field | Detail |
|---|---|
| **Use Case ID** | AD 02 |
| **Use Case Name** | View System Logs |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the admin role. |
| **Main Flow** | 1. Admin navigates to /ui/admin/logs. 2. App checks the admin role. 3. The page loads and fetches log data from the logs endpoint. 4. App returns log records sorted by creation time with support for configurable limit, sort column, and sort direction. 5. Logs are shown in a table with timestamp, level, event type, message, user ID, path, method, and status code. |
| **Alternate Flow** | If the requesting user does not have the admin role, the app returns HTTP 403. |
| **Postcondition** | The admin can view the system log records. |

---

##### 3.2.3.3. AD 03: Send System Wide Notification

Administrators can send a notification message to all users in the system.

| Field | Detail |
|---|---|
| **Use Case ID** | AD 03 |
| **Use Case Name** | Send System Wide Notification |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the admin role. |
| **Main Flow** | 1. Admin navigates to the notifications section of the admin panel. 2. Admin writes a notification message and submits it. 3. App sends the notification to all users. 4. App confirms the notification was sent. |
| **Alternate Flow** | If the message is empty, the app shows a validation error. If the requesting user does not have the admin role, the app returns HTTP 403. |
| **Postcondition** | All users receive the system wide notification. |

---

##### 3.2.3.4. AD 04: Unlink All External Calendars

Administrators can remove all external calendar connections across all users from the admin panel.

| Field | Detail |
|---|---|
| **Use Case ID** | AD 04 |
| **Use Case Name** | Unlink All External Calendars |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the admin role. |
| **Main Flow** | 1. Admin goes to the external calendars section of the admin panel. 2. Admin confirms the bulk unlink action. 3. App removes all records from the externals table. 4. App shows a success message with the count of removed records. |
| **Alternate Flow** | If no external records exist, the app tells the admin there is nothing to unlink. If the requesting user does not have the admin role, the app returns HTTP 403. |
| **Postcondition** | All records are removed from the externals table. |

---

#### 3.2.4. Guest User

Guest users access the system through a guest link token generated by a calendar owner (GL 01). They do not have an account and cannot log in. What they can do depends on the role assigned to the guest link.

##### 3.2.4.1. GL 02: View Shared Calendar

An unauthenticated user with a valid guest link can view the shared calendar and its events (Figure 14).

*(Figure 14: Public Guest Calendar Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | GL 02 |
| **Use Case Name** | View Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, the calendar exists, and the guest link is set to active. |
| **Main Flow** | 1. User navigates to /ui/guest/ followed by the token. 2. App looks up the calendar by the guest link token. 3. App fetches and shows the calendar name and all associated events. 4. If the link role is "editor," event creation, edit, and delete controls are also shown. |
| **Alternate Flow** | If the token is invalid or the calendar cannot be found, the app shows a not found page. If a server error occurs, the app shows a generic error message. |
| **Postcondition** | The guest user sees the shared calendar and its events. |

---

##### 3.2.4.2. GL 03: Create Event on Shared Calendar

A guest user with an editor role guest link can create new events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 03 |
| **Use Case Name** | Create Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the editor role. Extends GL 02. |
| **Main Flow** | 1. Guest user fills in the event title and optional description and times on the public calendar page and submits. 2. App checks the token and confirms the editor role. 3. App creates the event in Supabase and links it to the shared calendar. 4. App reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the event creation form is not shown. If the title is missing, the app shows a validation error. |
| **Postcondition** | A new event is created in the events table and linked to the shared calendar. |

---

##### 3.2.4.3. GL 04: Edit Event on Shared Calendar

A guest user with an editor role guest link can edit existing events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 04 |
| **Use Case Name** | Edit Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the editor role. The event belongs to the shared calendar. Extends GL 02. |
| **Main Flow** | 1. Guest user selects an event to edit on the public calendar page. 2. App loads the existing event data into an edit form. 3. Guest user changes the fields and submits. 4. App checks the token role and updates the event in Supabase. 5. App reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the edit option is not shown. |
| **Postcondition** | The event record is updated in the events table. |

---

##### 3.2.4.4. GL 05: Delete Event on Shared Calendar

A guest user with an editor role guest link can delete events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 05 |
| **Use Case Name** | Delete Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the editor role. The event belongs to the shared calendar. Extends GL 02. |
| **Main Flow** | 1. Guest user selects an event to delete on the public calendar page. 2. App checks the token role. 3. App removes the event from Supabase. 4. App reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the delete option is not shown. |
| **Postcondition** | The event record is removed from the events table. |

---

#### 3.2.5. Mis-Use Cases

The following mis use cases describe ways someone might try to misuse the system and explain how the app prevents or handles each one.

##### 3.2.5.1. MU 01: Bypass Authentication

An unauthenticated user tries to access a protected page like the home page, events page, or admin panel without being logged in.

**Mitigation:** All protected UI routes use the ui_login_required or ui_admin_required decorator. The decorator checks for the ui_user key in the Flask session. If it is not there, the user is sent back to the login page. The originally requested path is saved as a query parameter so the user can be sent there after logging in.

---

##### 3.2.5.2. MU 02: Access Another User's Data

A logged in user tries to view, edit, or delete calendars, events, or externals that belong to a different user.

**Mitigation:** The Supabase client used in all UI routes calls auth with the logged in user's access token before running any query. This makes Supabase apply Row Level Security policies, which restricts results to records owned by or shared with the authenticated user. Ownership is also checked at the app level before any deletions happen.

---

##### 3.2.5.3. MU 03: Escalate Privileges to Admin

A regular user tries to access admin only routes like /ui/admin/logs without having the admin role.

**Mitigation:** Admin routes use the ui_admin_required decorator, which checks that the session user's role equals "admin." The role is read from Supabase app metadata at login time and can only be set by a Supabase project administrator. Regular users have no way to change it. Any request to an admin route from a non admin user gets HTTP 403.

---

##### 3.2.5.4. MU 04: Access an Invalid or Deactivated Guest Link

A user tries to open a public calendar using a guest link token that does not exist, has been turned off by the owner, or has been changed.

**Mitigation:** The app looks up the calendar using the exact token value. If no matching calendar is found or if the guest link is set to inactive, the app shows a not found page and does not expose any calendar data. Guest link tokens are generated with a cryptographically secure random function that produces values that are practically impossible to guess or brute force.

---

### 3.3. Performance Requirements

Calendar and event data needs to be retrieved and displayed quickly on each page load so users have a good experience. Queries to Supabase use column filters to limit results instead of pulling all rows. Log retrieval in the admin panel supports a configurable limit that defaults to 25 records and caps at 500 to avoid pulling too much data. Log writes happen in a way that cannot block or crash an incoming request. The app is deployed as a Vercel serverless function, which scales automatically under more traffic.

### 3.4. Design Constraints

Users need an internet connection and a modern web browser to access the app. The app will not work without a valid Supabase project configured with the correct environment variables. The admin role can only be set directly in Supabase by a project administrator and is not accessible through any page in the app. Google Calendar OAuth requires the app to be registered in Google Cloud Console with the correct redirect URI. The Vercel deployment routes all requests through the main index file so any changes to routing need to be reflected there. CORS origins are set in the index file and need to be updated when deploying to a new domain.
