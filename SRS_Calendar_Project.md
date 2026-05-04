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

The back end is a Python Flask application that has two main parts: a REST API blueprint and a UI blueprint. Authentication routes live inside the UI blueprint. The app is deployed to Vercel as a Python serverless function. Supabase handles user authentication and the PostgreSQL database. Flask communicates with Supabase over HTTPS using the Supabase Python client library.

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

**Admin Signed In (extends User Signed In):** AD 01 Suspend User Account, AD 02 View System Logs, AD 03 Send System Wide Notification, AD 04 Unlink External Calendar, AD 05 Manage User Accounts

**Guest User (via Guest Link):** GL 02 View Shared Calendar, GL 03 Create Event on Shared Calendar, GL 04 Edit Event on Shared Calendar, GL 05 Delete Event on Shared Calendar

### 2.3. User Characteristics

The Use Case Diagram (Figure 2) shows three actors:

- **Guest User** -- An unauthenticated user who either has not made an account yet or is accessing a shared calendar through a guest link token. If they are accessing a shared calendar, they can view events. If the guest link has an editor role they can also create, edit, and delete events on that calendar.
- **User** -- A registered and logged in user. They can log in and out, manage calendars and events, add and remove calendar members, generate guest links, connect external calendar providers, manage friends, and delete their own account.
- **Admin** -- A registered user with the `is_admin` flag set to `true` in the `users` table. Admins can do everything a regular user can, plus they have access to system level tools like viewing logs, suspending user accounts, managing the user list, sending system wide notifications, and unlinking external calendars. Admin status can be granted by another admin through the admin panel, or set directly in Supabase.

### 2.4. Constraints

- All environment variables like SUPABASE_URL, SUPABASE_KEY, FLASK_SECRET_KEY, APP_BASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and CRON_SECRET must be set in Vercel and should never be hardcoded in source files.
- The Supabase schema needs to have the calendars, events, externals, users, notifications, and logs tables set up with the right columns and Row Level Security policies.
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

The Flask app talks to Supabase over HTTPS. Browsers talk to Flask over HTTP in development and HTTPS in production. The server rendered UI uses standard HTML form submissions. Flask session cookies keep users logged in for UI routes. The remaining REST endpoints use their own validation mechanisms: Google webhooks identify the source calendar via the `X-Goog-Channel-Token` header, Outlook webhooks use a `clientState` field in the request body, guest token endpoints take the token directly in the URL path, and the cron endpoint requires a `CRON_SECRET` Bearer token sent by Vercel.

### 3.2. Functional Requirements

Functional requirements are organized by user state and match the numbered use cases in the Use Case Diagram (Figure 2). Each use case specification includes the ID, description, primary actor, preconditions, postcondition, main success scenario, extensions, frequency of use, includes, and priority.

---

#### 3.2.1. User is Signed Out

##### 3.2.1.1. AU 01: Register Account

Users who do not have an account can create one on the registration page (Figure 3) by clicking the "Register" link on the login page.

*(Figure 3: Register Page)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Register Account |
| **Description** | A new user creates an account so they can log in and use the app. |
| **Primary Actor** | Guest User |
| **Preconditions** | The user does not have an existing account and is not logged in. |
| **Postcondition** | A new user account is created in Supabase Auth. The user gets a verification email and must verify it before they can log in. |
| **Main Success Scenario** | 1. User navigates to /ui/register. 2. User enters a display name (optional), email address, password, and password confirmation. 3. App checks that email and password fields are not empty and that the two password fields match. 4. App submits the registration to Supabase Auth, which sends a verification email. 5. App sends the user back to the login page with a confirmation message. |
| **Extensions** | 2a. If the email or password field is empty, the app shows: "Email and password are required." 2b. If the passwords do not match, the app shows: "PASSWORDS DON'T MATCH." 4a. If Supabase returns an error like email already registered, the app shows that error message. |
| **Frequency of Use** | Once per user |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.1.2. AU 02: Login to Account

If a user already has an account they can log in on the login page (Figure 4). This is the first page users see when they visit the site.

*(Figure 4: Login Page)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Login to Account |
| **Description** | A registered user signs in to access their calendars and events. |
| **Primary Actor** | Guest User |
| **Preconditions** | The user has a verified account and is not currently logged in. |
| **Postcondition** | The user's session is created. The user is redirected to the home page. |
| **Main Success Scenario** | 1. User navigates to /ui/login. 2. User enters their email address and password and submits the form. 3. App sends the credentials to Supabase Auth for verification. 4. App saves the user's ID, email, access token, and admin flag in the Flask session. 5. App sends the user to the home page. |
| **Extensions** | 2a. If either field is empty, the app shows: "Email and password are required." 3a. If Supabase returns an authentication failure, the app shows: "Wrong email or password." 3b. If the account is suspended, the app shows: "Your account has been suspended." |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

#### 3.2.2. User is Signed In

##### 3.2.2.1. AU 03: Log Out

Users can log out at any time using the logout link in the navigation menu.

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Log Out |
| **Description** | A logged in user ends their session and returns to the login page. |
| **Primary Actor** | User, Admin |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user's session is cleared and they are treated as unauthenticated. |
| **Main Success Scenario** | 1. User clicks the logout link in the navigation bar. 2. App clears the session data. 3. App sends the user to the home page. |
| **Extensions** | N/A |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.2. 27: Remove Account

If a user wants to delete their account they can do so from the account settings page accessible through the navigation menu (Figure 5).

*(Figure 5: Remove Account Page)*

| Field | Detail |
|---|---|
| **ID** | 27 |
| **Name** | Remove Account |
| **Description** | User no longer wants their data in the database or on the website. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user's account and related data is deleted from Supabase and their session is cleared. |
| **Main Success Scenario** | 1. User navigates to /ui/user/remove-account. 2. User confirms they want to delete their account. 3. App removes the user's account and data from Supabase. 4. App clears the session and sends the user to the login page. |
| **Extensions** | 2a. If the user cancels the action, nothing changes and they go back to the previous page. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.3. VC 01: View Calendar

Once logged in, users are taken to the home page (Figure 6) where they can see their calendars and switch between them.

*(Figure 6: Home Page with Calendar View)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | View Calendar |
| **Description** | A logged in user views their calendars and the events on them from the home page. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has at least one calendar. |
| **Postcondition** | The user can see the selected calendar and its events. |
| **Main Success Scenario** | 1. User navigates to /ui/ which is the home page. 2. App fetches all calendars owned by the user or where the user is a member. 3. App shows the first calendar by default. The user can switch to other calendars using a selector. 4. App fetches and shows all events for the selected calendar. |
| **Extensions** | 2a. If the user has no calendars, the page shows a message prompting the user to create one. 4a. If events fail to load, the app shows an error message. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.4. 1: View Event

Users can view events on a selected calendar from the home page (Figure 6) or the Manage Events page (Figure 9).

| Field | Detail |
|---|---|
| **ID** | 1 |
| **Name** | View Event |
| **Description** | A user reads the details of an event on one of their calendars. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has access to a calendar that has events. |
| **Postcondition** | The user sees a list of events for the selected calendar. |
| **Main Success Scenario** | 1. User goes to the home page or the Manage Events page. 2. App fetches all events for the selected calendar. 3. App shows each event's title, description, and start and end times. |
| **Extensions** | 2a. If the calendar has no events, the page shows a message saying the calendar is empty. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.5. CM 01: Manage Calendars

Logged in users can manage their calendars from the Manage Calendars page (Figure 7). This use case covers creating calendars, managing members, and deleting calendars. It also includes the Manage Events sub use case.

*(Figure 7: Manage Calendars Page)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Manage Calendars |
| **Description** | A user views and manages all calendars they own from a single page. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user can see all their calendars and take action on them. |
| **Main Success Scenario** | 1. User navigates to /ui/user/calendars. 2. App fetches all calendars owned by the user. 3. App shows each calendar with options for creating new ones, editing membership, generating guest links, and deleting. |
| **Extensions** | 2a. If the calendars list fails to load, the app shows an error message. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | 17 (Create Calendar), 18 (Remove Calendar), 19 (Add Member), 20 (Remove Member), Manage Events |
| **Priority** | P1 - High |

---

##### 3.2.2.6. 17: Create Calendar

From the Manage Calendars page (Figure 7), users can create a new calendar.

| Field | Detail |
|---|---|
| **ID** | 17 |
| **Name** | Create Calendar |
| **Description** | A user creates a new calendar to organize their events. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | A new calendar record is created in the calendars table with the requesting user set as owner. |
| **Main Success Scenario** | 1. User types a calendar name on the Manage Calendars page and submits the form. 2. App creates the calendar in Supabase and sets the user as the owner. 3. App shows the updated calendar list with a success message. |
| **Extensions** | 1a. If the name field is empty, the app shows a validation error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.7. 19: Add Member

Calendar owners can add other users as members to a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **ID** | 19 |
| **Name** | Add Member |
| **Description** | A calendar owner shares their calendar with another user by adding them as a member. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and owns the calendar. |
| **Postcondition** | The target user's ID is added to the calendar's member list and they can now view the calendar. |
| **Main Success Scenario** | 1. User enters the target user's ID in the Add Member field and submits. 2. App checks that the target user exists. 3. App adds the target user's ID to the calendar's member IDs list. 4. App shows a success message. |
| **Extensions** | 2a. If the target user does not exist, the app shows an error. 3a. If the user is already a member, the app notifies the owner. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.8. 20: Remove Member

Calendar owners can remove members from a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **ID** | 20 |
| **Name** | Remove Member |
| **Description** | A calendar owner removes a user's access to their calendar. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in, owns the calendar, and the target member is in the member list. |
| **Postcondition** | The target user's ID is removed from the member list and they can no longer access the calendar. |
| **Main Success Scenario** | 1. User selects a member to remove from the member list on the Manage Calendars page. 2. App removes the target user's ID from the calendar's member list. 3. App shows a success message. |
| **Extensions** | 2a. If the member ID is not found in the calendar's member list, the app shows an error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.9. 18: Remove Calendar

Calendar owners can delete a calendar they own from the Manage Calendars page (Figure 7).

| Field | Detail |
|---|---|
| **ID** | 18 |
| **Name** | Remove Calendar |
| **Description** | A calendar owner deletes one of their calendars from the system. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and owns the calendar. |
| **Postcondition** | The calendar record is removed from the calendars table. |
| **Main Success Scenario** | 1. User selects a calendar and confirms the delete action. 2. App checks that the user is the calendar owner. 3. App removes the calendar record from Supabase. 4. App shows the updated list with a success message. |
| **Extensions** | 2a. If the user is not the owner, the app returns an authorization error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.10. GL 01: Generate Guest Link

Calendar owners can generate a shareable guest link that lets unauthenticated users access a calendar (Figure 7).

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Generate Guest Link |
| **Description** | A calendar owner creates a shareable URL so people without an account can view or edit the calendar. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and owns the calendar. |
| **Postcondition** | The calendar record is updated with the guest link token, role, and active status. Unauthenticated users can now access the calendar through the generated URL. |
| **Main Success Scenario** | 1. User selects a role (viewer or editor) on the Manage Calendars page and activates the guest link. 2. App generates a random token and stores it in the calendar record along with the selected role and an active flag. 3. App shows the full shareable URL to the user. |
| **Extensions** | 1a. If the owner deactivates the guest link, the active flag is set to false and the URL no longer works. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.11. CM 06: Manage Events

Users can manage events on their calendars from the Manage Events page (Figure 8). This use case is included by CM 01 and includes the Create Event, Edit Event, and Remove Event sub use cases.

*(Figure 8: Manage Events Page)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Manage Events |
| **Description** | A user navigates to the events page to view and manage events across their calendars. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has access to at least one calendar. |
| **Postcondition** | The user can view and manage events for the selected calendar. |
| **Main Success Scenario** | 1. User navigates to /ui/user/events. 2. App fetches the user's calendars. 3. App shows events for the selected calendar with options to create, edit, and delete events. |
| **Extensions** | 2a. If the user has no calendars, the page shows a message to create one first. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | 21 (Create Event), 22 (Edit Event), 23 (Remove Event) |
| **Priority** | P1 - High |

---

##### 3.2.2.12. 21: Create Event

From the Manage Events page (Figure 8), users can create a new event on a calendar they have access to.

| Field | Detail |
|---|---|
| **ID** | 21 |
| **Name** | Create Event |
| **Description** | A user adds a new event to one of their calendars. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has access to at least one calendar. |
| **Postcondition** | A new event record is created in the events table with the requesting user as owner. |
| **Main Success Scenario** | 1. User enters a title, optional description, start time, and end time, then selects a target calendar and submits. 2. App validates the required fields. 3. App creates the event in Supabase and links it to the selected calendar. 4. App shows the updated event list with a success message. |
| **Extensions** | 2a. If the title is missing, the app shows a validation error. 2b. If the user does not have access to the selected calendar, the app returns an authorization error. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.13. 22: Edit Event

Event owners can edit the details of their events from the Edit Event page (Figure 9).

*(Figure 9: Edit Event Page)*

| Field | Detail |
|---|---|
| **ID** | 22 |
| **Name** | Edit Event |
| **Description** | A user updates the title, description, or time of an event they own. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and is the owner of the event. |
| **Postcondition** | The event record in the events table is updated with the new values. |
| **Main Success Scenario** | 1. User selects an event to edit on the Manage Events page and is taken to the edit page. 2. App loads the existing event data into the form. 3. User changes the title, description, start or end time, or calendars and submits. 4. App updates the event record in Supabase. 5. App sends the user back to the events list with a success message. |
| **Extensions** | 1a. If the user is not the event owner, the app redirects to the events list with an error. 3a. If required fields are missing, the app shows a validation error. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.14. 23: Remove Event

Event owners can delete their events from the Manage Events page (Figure 8).

| Field | Detail |
|---|---|
| **ID** | 23 |
| **Name** | Remove Event |
| **Description** | A user permanently deletes an event they own from their calendar. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and is the owner of the event. |
| **Postcondition** | The event record is removed from the events table. |
| **Main Success Scenario** | 1. User selects an event on the Manage Events page and confirms the delete action. 2. App checks ownership. 3. App removes the event record from Supabase. 4. App shows the updated event list with a success message. |
| **Extensions** | 2a. If the user is not the event owner, the app returns an authorization error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P1 - High |

---

##### 3.2.2.15. EX 01: Manage Externals

Logged in users can view and manage their connected external calendar providers from the Settings page (Figure 10). The app supports Google Calendar and Outlook (Microsoft). This use case includes the sub use cases for linking, pulling, pushing, and unlinking external calendars.

*(Figure 10: Settings Page with External Calendars)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Manage Externals |
| **Description** | A user views and manages all of their connected external calendar accounts from the Settings page. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user can see their connected external providers and take action on them. |
| **Main Success Scenario** | 1. User navigates to /ui/settings. 2. App fetches all external calendar records for the user and separates them by provider (Google and Outlook). 3. App shows each provider's connections with options to pull, push, and unlink. |
| **Extensions** | 2a. If no external connections exist, the page shows a prompt to connect a provider. |
| **Frequency of Use** | Less than once per day |
| **Includes** | 9, 13 (Link External), 10, 15 (Push External), 11, 14 (Pull External), 12, 16 (Unlink External) |
| **Priority** | P2 - Low |

---

##### 3.2.2.16. 11, 14: Pull Data from External Calendar

Users can import events from a connected external calendar into a local calendar (Figure 10).

| Field | Detail |
|---|---|
| **ID** | 11 (Google), 14 (Outlook) |
| **Name** | Pull Data from External Calendar |
| **Description** | A user imports events from their Google or Outlook calendar into a local synced calendar. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has a linked external calendar (Google or Outlook). |
| **Postcondition** | A local synced calendar is created or updated with events pulled from the external provider. |
| **Main Success Scenario** | 1. User clicks the sync option next to a connected provider on the Settings page. 2. App fetches events from that provider using the stored access token. 3. For Google, the app creates or updates a local calendar called "Google Calendar (Synced)." For Outlook, the app creates or updates a local calendar called "Outlook Calendar (Synced)." 4. App shows a success message with the number of synced events. |
| **Extensions** | 2a. If the access token is expired, the app tries to refresh it automatically. If the refresh fails, the app shows an error and asks the user to reconnect. |
| **Frequency of Use** | Multiple times per week |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.17. 10, 15: Push Data to External Calendar

Users can export their local calendars to a connected external calendar provider (Figure 10).

| Field | Detail |
|---|---|
| **ID** | 10 (Google), 15 (Outlook) |
| **Name** | Push Data to External Calendar |
| **Description** | A user exports their local calendar events to their Google or Outlook calendar. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in, has a linked external calendar (Google or Outlook), and has at least one local calendar to export. |
| **Postcondition** | The user's local calendar events are sent to the external provider. |
| **Main Success Scenario** | 1. User clicks the push option next to a connected provider on the Settings page. 2. App sends all local calendars owned by the user (excluding the provider's own synced calendar) to the external provider using the stored access token. 3. App shows a success message with the number of events pushed. |
| **Extensions** | 2a. If the access token is expired, the app tries to refresh it automatically. If the refresh fails, the app shows an error and asks the user to reconnect. |
| **Frequency of Use** | Multiple times per week |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.18. 9, 13: Link External Calendar

Users can link a new external calendar provider account from the Settings page (Figure 10). Both Google Calendar and Outlook are supported.

| Field | Detail |
|---|---|
| **ID** | 9 (Google), 13 (Outlook) |
| **Name** | Link External Calendar |
| **Description** | A user connects their Google or Outlook account to the app so they can sync calendar events. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. Valid OAuth credentials are configured in the app environment for the chosen provider. |
| **Postcondition** | A new record is added to the externals table with the user's access token and refresh token for the chosen provider. |
| **Main Success Scenario** | 1. User navigates to /ui/settings and clicks "Connect Google Calendar" or "Connect Outlook Calendar." 2. App starts the OAuth 2.0 flow and sends the user to the provider's authorization page (Google or Microsoft). 3. User grants calendar permissions. 4. The provider redirects back to the app with an authorization code. 5. App exchanges the code for access and refresh tokens and saves them in the externals table with the correct provider label. 6. App registers a push notification subscription so the app receives webhook updates. 7. App sends the user back to the Settings page with a success message. |
| **Extensions** | 2a. If OAuth credentials are missing from the environment, the app shows an error. 3a. If the user denies the permissions request, the app returns to Settings with an error message. 5a. If the OAuth state does not match when the provider redirects back, the app shows a state mismatch error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.19. 12, 16: Unlink External Calendar

Users can disconnect a connected external calendar provider from their account via the Settings page (Figure 10).

| Field | Detail |
|---|---|
| **ID** | 12 (Google), 16 (Outlook) |
| **Name** | Unlink External Calendar |
| **Description** | A user disconnects their Google or Outlook account from the app. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and has at least one linked external calendar. |
| **Postcondition** | The external calendar record is removed from the externals table. |
| **Main Success Scenario** | 1. User navigates to /ui/settings and clicks "Disconnect" next to the provider. 2. App removes the external record from the externals table. 3. App shows a success message. |
| **Extensions** | 2a. If the external record cannot be found, the app shows an error message. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.20. FM 01: Manage Friends

Logged in users can manage their friends list from the Manage Friends page (Figure 11). This use case includes viewing, adding, and removing friends.

*(Figure 11: Manage Friends Page)*

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Manage Friends |
| **Description** | A user views and manages their list of friends from a single page. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user can see their friends list and take action on it. |
| **Main Success Scenario** | 1. User navigates to /ui/user/friends. 2. App fetches the user's friends list from Supabase. 3. App shows each friend with options to add and remove friends. |
| **Extensions** | 2a. If the friends list fails to load, the app shows an error message. |
| **Frequency of Use** | Less than once per day |
| **Includes** | 24 (Add Friend), 25 (Remove Friend), 26 (View Friends List) |
| **Priority** | P2 - Low |

---

##### 3.2.2.21. 26: View Friends List

Users can view their current list of friends from the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **ID** | 26 |
| **Name** | View Friends List |
| **Description** | A user sees all of the friends currently on their account. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The user sees their current friends with display names and emails. |
| **Main Success Scenario** | 1. App fetches the user's friends list from Supabase. 2. App looks up each friend's display name and email. 3. App shows the list. |
| **Extensions** | 1a. If the friends list is empty, the page shows a message saying no friends have been added yet. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.22. 24: Add Friend

Users can add another user as a friend from the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **ID** | 24 |
| **Name** | Add Friend |
| **Description** | A user adds another registered user to their friends list. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in. |
| **Postcondition** | The target user's ID is added to the user's friends list. |
| **Main Success Scenario** | 1. User enters the target user's ID or email in the Add Friend field and submits. 2. App checks that the target user exists. 3. App adds the target user's ID to the requesting user's friends list in Supabase. 4. App shows a success message. |
| **Extensions** | 2a. If the target user does not exist, the app shows an error. 3a. If the user is already in the friends list, the app notifies the user. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.2.23. 25: Remove Friend

Users can remove a friend from their friends list on the Manage Friends page (Figure 11).

| Field | Detail |
|---|---|
| **ID** | 25 |
| **Name** | Remove Friend |
| **Description** | A user removes another user from their friends list. |
| **Primary Actor** | User |
| **Preconditions** | The user is logged in and the target user is in their friends list. |
| **Postcondition** | The target user's ID is removed from the user's friends list. |
| **Main Success Scenario** | 1. User selects a friend to remove on the Manage Friends page. 2. App removes the target user's ID from the requesting user's friends list in Supabase. 3. App shows the updated friends list with a success message. |
| **Extensions** | 2a. If the target user's ID is not found in the friends list, the app shows an error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

#### 3.2.3. Admin is Signed In

The Admin actor extends the User actor. All use cases available to a regular User are also available to an Admin. The following use cases are exclusive to the Admin role. Admin status is stored in the `is_admin` column of the `users` table and is checked on every admin route through the `ui_admin_required` decorator.

##### 3.2.3.1. 5: Suspend User Account

Administrators can suspend a user account from the admin panel (Figure 12).

*(Figure 12: Admin Panel with Suspend User Section)*

| Field | Detail |
|---|---|
| **ID** | 5 |
| **Name** | Suspend User Account |
| **Description** | An admin blocks a user from logging in without deleting their data. |
| **Primary Actor** | Admin |
| **Preconditions** | The admin is logged in with the admin role. The target user account exists. |
| **Postcondition** | The target user's `is_suspended` flag is set to true. Their data is preserved but they are blocked from logging in. |
| **Main Success Scenario** | 1. Admin navigates to /ui/admin/suspend. 2. Admin searches for the target user by email, display name, or ID. 3. App shows the matching user. 4. Admin confirms the suspension. 5. App sets the `is_suspended` flag to true on the target user's record in the users table. 6. App shows a success message. |
| **Extensions** | 1a. If the requesting user does not have the admin role, the app returns HTTP 403. 2a. If no user matches the search, the page shows no result. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.3.2. 6: View System Logs

Administrators can view application level request and event logs from the admin panel (Figure 13).

*(Figure 13: Admin Panel with System Logs)*

| Field | Detail |
|---|---|
| **ID** | 6 |
| **Name** | View System Logs |
| **Description** | An admin reviews request and event logs to monitor system activity. |
| **Primary Actor** | Admin |
| **Preconditions** | The admin is logged in with the admin role. |
| **Postcondition** | The admin can view the system log records. |
| **Main Success Scenario** | 1. Admin navigates to /ui/admin/logs. 2. App checks the admin role. 3. The page loads and fetches log data from the logs endpoint. 4. App returns log records sorted by creation time with support for configurable limit, sort column, and sort direction. 5. Logs are shown in a table with timestamp, level, event type, message, user ID, path, method, and status code. |
| **Extensions** | 1a. If the requesting user does not have the admin role, the app returns HTTP 403. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.3.3. 7: Send System Wide Notification

Administrators can post a notification banner visible to all users of the system.

| Field | Detail |
|---|---|
| **ID** | 7 |
| **Name** | Send System Wide Notification |
| **Description** | An admin publishes a site-wide banner message that all users will see when they use the app. |
| **Primary Actor** | Admin |
| **Preconditions** | The admin is logged in with the admin role. |
| **Postcondition** | The notification banner is active and visible to all users. Any previously active notification is deactivated. |
| **Main Success Scenario** | 1. Admin navigates to /ui/admin/notifications. 2. Admin writes a notification message and submits it. 3. App deactivates any existing active notification and inserts the new message as active. 4. App confirms the notification was saved. |
| **Extensions** | 1a. If the requesting user does not have the admin role, the app returns HTTP 403. 2a. If the message is empty, the form is not submitted. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.3.4. 8: Unlink External Calendar

Administrators can remove a specific external calendar connection for any user from the admin panel.

| Field | Detail |
|---|---|
| **ID** | 8 |
| **Name** | Unlink External Calendar |
| **Description** | An admin removes an external calendar connection on behalf of a user. |
| **Primary Actor** | Admin |
| **Preconditions** | The admin is logged in with the admin role. |
| **Postcondition** | The selected external calendar record is removed from the externals table. |
| **Main Success Scenario** | 1. Admin navigates to /ui/admin/unlink. 2. Admin searches for the target user by email, display name, or ID. 3. App shows the target user's connected external calendar accounts. 4. Admin selects the external to remove and confirms. 5. App removes the selected external record from the externals table. 6. App shows a success confirmation. |
| **Extensions** | 1a. If the requesting user does not have the admin role, the app returns HTTP 403. 2a. If no user matches the search, the page shows no result. 5a. If the selected external is not found, the app returns an error. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.3.5. AD 05: Manage User Accounts

Administrators can view all user accounts and toggle admin status for any user from the admin panel.

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Manage User Accounts |
| **Description** | An admin views the full user list and grants or revokes admin access for any account. |
| **Primary Actor** | Admin |
| **Preconditions** | The admin is logged in with the admin role. |
| **Postcondition** | The target user's `is_admin` flag is updated. The change takes effect on the user's next login. |
| **Main Success Scenario** | 1. Admin navigates to /ui/admin/users. 2. App fetches and shows a list of all users with their ID, email, display name, and current admin status. 3. Admin clicks the toggle next to a user to grant or revoke admin access. 4. App flips the `is_admin` flag for that user and returns the new value. |
| **Extensions** | 1a. If the requesting user does not have the admin role, the app returns HTTP 403. 3a. If the target user is not found, the app returns HTTP 404. |
| **Frequency of Use** | Less than once per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

#### 3.2.4. Guest User

Guest users access the system through a guest link token generated by a calendar owner (GL 01). They do not have an account and cannot log in. What they can do depends on the role assigned to the guest link.

##### 3.2.4.1. 3: View Shared Calendar

An unauthenticated user with a valid guest link can view the shared calendar and its events (Figure 14).

*(Figure 14: Public Guest Calendar Page)*

| Field | Detail |
|---|---|
| **ID** | 3 |
| **Name** | View Shared Calendar |
| **Description** | A guest user opens a shared calendar link and sees the calendar's events. |
| **Primary Actor** | Guest User |
| **Preconditions** | The guest link token is valid, the calendar exists, and the guest link is set to active. |
| **Postcondition** | The guest user sees the shared calendar and its events. |
| **Main Success Scenario** | 1. User navigates to /ui/guest/ followed by the token. 2. App looks up the calendar by the guest link token. 3. App fetches and shows the calendar name and all associated events. 4. If the link role is "editor," event creation, edit, and delete controls are also shown. |
| **Extensions** | 2a. If the token is invalid or the calendar cannot be found, the page shows a not found message. 2b. If a server error occurs, the page shows a generic error message. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.4.2. 4: Create Event on Shared Calendar

A guest user with an editor role guest link can create new events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **ID** | 4 |
| **Name** | Create Event on Shared Calendar |
| **Description** | A guest editor adds a new event to the shared calendar without needing an account. |
| **Primary Actor** | Guest User |
| **Preconditions** | The guest link token is valid, active, and has the editor role. |
| **Postcondition** | A new event is created in the events table and linked to the shared calendar. |
| **Main Success Scenario** | 1. Guest user fills in the event title and optional description and times on the public calendar page and submits. 2. App checks the token and confirms the editor role. 3. App creates the event in Supabase and links it to the shared calendar. 4. App reloads the page with a success message. |
| **Extensions** | 1a. If the token role is "viewer," the event creation form is not shown. 1b. If the title is missing, the app shows a validation error. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.4.3. 2: Edit Event on Shared Calendar

A guest user with an editor role guest link can edit existing events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **ID** | 2 |
| **Name** | Edit Event on Shared Calendar |
| **Description** | A guest editor updates the details of an existing event on the shared calendar. |
| **Primary Actor** | Guest User |
| **Preconditions** | The guest link token is valid, active, and has the editor role. The event belongs to the shared calendar. |
| **Postcondition** | The event record is updated in the events table. |
| **Main Success Scenario** | 1. Guest user selects an event to edit on the public calendar page. 2. App loads the existing event data into an edit form. 3. Guest user changes the fields and submits. 4. App checks the token role and updates the event in Supabase. 5. App reloads the page with a success message. |
| **Extensions** | 1a. If the token role is "viewer," the edit option is not shown. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

---

##### 3.2.4.4. GL 05: Delete Event on Shared Calendar

A guest user with an editor role guest link can delete events on the shared calendar (Figure 14).

| Field | Detail |
|---|---|
| **ID** | N/A |
| **Name** | Delete Event on Shared Calendar |
| **Description** | A guest editor removes an event from the shared calendar. |
| **Primary Actor** | Guest User |
| **Preconditions** | The guest link token is valid, active, and has the editor role. The event belongs to the shared calendar. |
| **Postcondition** | The event record is removed from the events table. |
| **Main Success Scenario** | 1. Guest user selects an event to delete on the public calendar page. 2. App checks the token role. 3. App removes the event from Supabase. 4. App reloads the page with a success message. |
| **Extensions** | 1a. If the token role is "viewer," the delete option is not shown. |
| **Frequency of Use** | Multiple times per day |
| **Includes** | N/A |
| **Priority** | P2 - Low |

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

**Mitigation:** Admin routes use the `ui_admin_required` decorator, which checks the `is_admin` flag stored in the Flask session. The flag is read from the `is_admin` column of the `users` table at login time. Regular users have no way to change it themselves. Any request to an admin route from a non admin user gets HTTP 403.

---

##### 3.2.5.4. MU 04: Access an Invalid or Deactivated Guest Link

A user tries to open a public calendar using a guest link token that does not exist, has been turned off by the owner, or has been changed.

**Mitigation:** The app looks up the calendar using the exact token value. If no matching calendar is found or if the guest link is set to inactive, the app shows a not found page and does not expose any calendar data. Guest link tokens are generated with a cryptographically secure random function that produces values that are practically impossible to guess or brute force.

---

### 3.3. Performance Requirements

Calendar and event data needs to be retrieved and displayed quickly on each page load so users have a good experience. Queries to Supabase use column filters to limit results instead of pulling all rows. Log retrieval in the admin panel supports a configurable limit that defaults to 25 records and caps at 500 to avoid pulling too much data. Log writes happen in a way that cannot block or crash an incoming request. The app is deployed as a Vercel serverless function, which scales automatically under more traffic.

### 3.4. Design Constraints

Users need an internet connection and a modern web browser to access the app. The app will not work without a valid Supabase project configured with the correct environment variables. The initial admin account must be set up directly in Supabase; after that, existing admins can grant or revoke admin access to other users through the admin panel. Google Calendar OAuth requires the app to be registered in Google Cloud Console with the correct redirect URI. Outlook OAuth requires the app to be registered in Azure with the correct redirect URI. The Vercel deployment routes all requests through the main index file so any changes to routing need to be reflected there. CORS origins are set in the index file and need to be updated when deploying to a new domain.
