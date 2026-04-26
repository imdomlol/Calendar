# Calendar

## Software Requirement Specification

**Spring 2026**

**Version 2.0**

**Project Manager –** Dominic

**Software Engineer –** Charlize

**Software Engineer –** Owen

**Software Engineer –** Hector

**Software Engineer –** Eric

**Software Engineer –** Nathan

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
     - [3.2.1. User is Signed Out (AU 01–02)](#321-user-is-signed-out)
     - [3.2.2. User is Signed In (AU 03, UA 01, VC 01, VE 01, CM 01–06, EM 01–03, EX 01–05, FM 01–04, GL 01)](#322-user-is-signed-in)
     - [3.2.3. Admin is Signed In (AD 01–04)](#323-admin-is-signed-in)
     - [3.2.4. Guest User (GL 02–05)](#324-guest-user)
     - [3.2.5. Mis-Use Cases (MU 01–04)](#325-mis-use-cases)
   - [3.3. Performance Requirements](#33-performance-requirements)
   - [3.4. Design Constraints](#34-design-constraints)

---

## 1. Introduction

### 1.1. Purpose

This SRS (Software Requirements Specification) document outlines the specific software needs and requirements for the Calendar web application. The requirements described in this document must be met and tested by the end of the CPSC 362 Software Engineering course in Spring 2026.

### 1.2. Scope

Calendar is a web-based calendar management application that allows users to organize events, share calendars, and connect with external calendar providers. The system provides a full server-rendered user interface alongside a REST API, both backed by Supabase for authentication and data persistence, and deployed to Vercel.

For a full overview of system use cases, refer to the Use Case Diagram in Section 2.2.

**Prototype 1:**

- **Authentication:** Users can register with an email and password, log in to an existing account, and log out. Email verification is required before logging in.
- **Calendar Management:** Authenticated users can create calendars, view events on each calendar, and delete calendars they own.

**Final Product:**

- **Event Management:** Users can create, view, edit, and delete events on calendars they own or are a member of.
- **Friends:** Users can view a friends list and add or remove friends from their account.
- **Guest Links:** Calendar owners can generate a shareable guest link with a viewer or editor role, allowing external users to access a calendar without an account. Guest users can view and, if permitted, create, edit, and delete events on the shared calendar.
- **External Calendar Integration:** Users can link a Google Calendar account, pull events from Google Calendar into a local calendar, push local calendars to Google Calendar, and unlink the connection at any time.
- **Settings:** Users can manage their connected external calendar providers.
- **Admin Panel:** Administrators can view system logs, suspend user accounts, send system-wide notifications, and unlink all external calendars.

### 1.3. Definitions, Acronyms, Abbreviations

**Program** – A set of well-defined steps a computer initiates to complete a task.

**Application** – A program or software that enables users to interact with a GUI and a server connected to the internet to accomplish a task.

**Software** – Programs and other operational information used by a computer.

**Computer** – A device for processing and storing data.

**GUI or UI** – Graphical User Interface; allows users to interact with designated programs or web applications.

**SRS** – Software Requirements Specification; this very document.

**Home Page** – The web page users are taken to after they log in.

**Web Application** – A program that runs on a dedicated server and is accessed through a web browser. Typically written with HTML, CSS, and JavaScript.

**HTML** – Hypertext Markup Language; the language used for basic web page structure displayed in a browser.

**CSS** – Cascading Style Sheets; used to style and format HTML elements, giving the site a customized look and feel.

**Python** – A programming language used for the server-side backend of this application.

**Flask** – A lightweight Python web framework used to handle HTTP routing and request processing.

**Database** – A structured set of data held in a computer, accessible in various ways.

**User Credentials** – A user's email address and password used to sign into the application.

**Supabase** – An open-source backend-as-a-service platform providing a PostgreSQL database, authentication, and REST API. Used in place of Firebase for this project.

**JWT** – JSON Web Token; a token format used to represent authenticated sessions.

**RLS** – Row-Level Security; a Supabase/PostgreSQL feature that restricts database rows to authorized users.

**Bearer Token** – An access token sent in the HTTP Authorization header to authenticate requests to the API.

**REST** – Representational State Transfer; an architectural style for designing HTTP APIs.

**OAuth** – An open authorization standard used to grant applications access to a user's data on a third-party service.

**CRUD** – Create, Read, Update, Delete; the four basic operations performed on data.

**UUID** – Universally Unique Identifier; used as a primary key format throughout the database.

**Vercel** – A cloud platform used to deploy the Calendar application as a serverless Python function.

**Guest Link** – A shareable URL token that allows unauthenticated users to access a specific calendar in a viewer or editor role.

**UID** – A User ID; uniquely identifies a user within the system.

**Front End** – The part of the application that the user directly interacts with (the web pages).

**Back End** – The server-side part of the application the user does not directly see; handles data, logic, and authentication.

### 1.4. References

Supabase. "Supabase Documentation." Supabase, 2025, supabase.com/docs.

Pallets Projects. "Flask Documentation." Flask, 2025, flask.palletsprojects.com.

GitHub. "GitHub." GitHub, 2025, github.com.

Vercel. "Vercel Documentation." Vercel, 2025, vercel.com/docs.

Google. "Google Calendar API." Google Developers, 2025, developers.google.com/calendar.

---

## 2. Overall Description

### 2.1. Product Perspectives

#### 2.1.1. System Interfaces (Deployment Diagram)

For the front end, Calendar uses Jinja2 server-rendered HTML templates styled with CSS. All user interface pages are generated server-side by the Flask application and delivered to the user's browser. This approach keeps the architecture simple and avoids a separate JavaScript framework.

The back end is a Python Flask application structured around three blueprints: an authentication blueprint, a REST API blueprint, and a UI blueprint. The application is deployed to Vercel as a Python serverless function. Supabase handles both user authentication (JWT issuance and validation) and the PostgreSQL database (calendars, events, externals, users, and logs tables). The Flask server communicates with Supabase over HTTPS using the Supabase Python client library.

*(Figure 1: Deployment Diagram - Web-Client → Flask on Vercel → Supabase Auth + PostgreSQL Database)*

#### 2.1.2. User Interfaces

**User is signed out:**

- When a user connects to the site they are redirected to the login page. If they do not have an account they can navigate to the register page via the "Register" link.
- All they need is a valid email address and a password. Error handling is in place to address empty fields and mismatched passwords.
- After registration, a verification email is sent to the user before they can log in.

**User is signed in:**

- After logging in, the user is taken to the home page showing their calendars and the events on the selected calendar.
- Users can create and delete calendars, and create, edit, and delete events on those calendars.
- Users can view and manage friends, access a personal to-do list, and connect external calendar providers via the Settings page.
- If the user wants to log out or delete their account, they can do so from the navigation menu.

**Admin is signed in:**

- Administrators have access to the admin panel, which provides system log viewing, user suspension, system-wide notifications, and external calendar unlinking tools.

**Guest user:**

- An unauthenticated user with a valid guest link can view a shared calendar and, if the link grants editor access, create, edit, and delete events on that calendar.

#### 2.1.3. Software Interfaces

1. **Visual Studio Code** – The primary development environment used to write the application code.
   - **Front End** – Jinja2 templates, HTML, and CSS for the server-rendered UI.
   - **Back End** – Python and Flask for routing, business logic, and Supabase communication.

2. **Supabase** – Used to handle authentication and data storage.
   - **Authentication** – Stores user credentials, issues JWTs, and provides session validation.
   - **Database** – PostgreSQL database with tables for calendars, events, externals, users, and logs.

3. **Vercel** – Hosts the Flask application as a serverless Python function and handles HTTPS routing.

4. **Google Calendar API** – Used for OAuth-based external calendar integration. The application requests access to the user's Google Calendar to pull and push events.

### 2.2. Product Functions (Use Case Diagram)

Calendar allows authenticated users to manage calendars and events, connect external calendar providers, manage friends, and generate shareable guest links. Calendar owners can share their calendars publicly via a guest link that grants either viewer or editor access to unauthenticated users. Administrators have elevated access to system-level tools including log viewing and account suspension. The Use Case Diagram (Figure 2) shows the complete set of use cases across all three actors.

*(Figure 2: Use Case Diagram — See Section 3.2 for full use case specifications)*

The diagram includes the following numbered use cases:

**User Signed Out:** AU 01 Register Account · AU 02 Login to Account

**User Signed In:** AU 03 Log Out · UA 01 Remove Account · VC 01 View Calendar · VE 01 View Event · CM 01 Manage Calendars *(includes: CM 02 Create Calendar · CM 03 Add Member · CM 04 Remove Member · CM 05 Remove Calendar · CM 06 Manage Events *(includes: EM 01 Create Event · EM 02 Edit Event · EM 03 Remove Event))* · EX 01 Manage Externals *(includes: EX 02 Pull Data from External Calendar · EX 03 Push Data to External Calendar · EX 04 Link External Calendar · EX 05 Unlink External Calendar)* · FM 01 Manage Friends *(includes: FM 02 View Friends List · FM 03 Add Friend · FM 04 Remove Friend)* · GL 01 Generate Guest Link

**Admin Signed In (extends User Signed In):** AD 01 Suspend User Account · AD 02 View System Logs · AD 03 Send System-Wide Notification · AD 04 Unlink All External Calendars

**Guest User (via Guest Link):** GL 02 View Shared Calendar · GL 03 Create Event on Shared Calendar · GL 04 Edit Event on Shared Calendar · GL 05 Delete Event on Shared Calendar

### 2.3. User Characteristics

The Use Case Diagram (Figure 2) defines three actors:

- **Guest User** – An unauthenticated user who accesses a calendar through a guest link token generated by a calendar owner. They have no account and interact only with the specific shared calendar. Depending on the role assigned to the guest link, they can either view events only (viewer role) or also create, edit, and delete events on that calendar (editor role). Guest Users are also the actor for the Register Account and Login to Account use cases, as they are the ones who do not yet have a session.
- **User** – A registered and authenticated user. They can log in and out, view and manage calendars and events, add and remove calendar members, generate guest links, link and manage external calendar providers, manage friends, and remove their own account.
- **Admin** – A registered user with the "admin" role set in Supabase app_metadata. The Admin actor extends the User actor and has all the same capabilities, plus access to system-level tools: viewing system logs, suspending user accounts, sending system-wide notifications, and unlinking all external calendars across all users. Admin status can only be granted directly in Supabase by a project administrator and cannot be self-assigned.

### 2.4. Constraints

- All environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SECRET_API_KEY`, `FLASK_SECRET_KEY`, `APP_BASE_URL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`) must be configured in Vercel and never hard-coded in source.
- The Supabase schema must include the `calendars`, `events`, `externals`, `users`, and `logs` tables with the correct columns and Row-Level Security policies.
- CORS origins must be updated in `api/index.py` when deploying to a new domain.
- Google Calendar OAuth integration requires valid `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` credentials registered in Google Cloud Console.
- Time constraints due to this being a student project; all team members have other course responsibilities.
- The application must be accessible through a web browser with an internet connection.

### 2.5. Assumptions and Dependencies

- Supabase services work as intended and no outages occur during use.
- Users have internet access and a web browser to access the application.
- Users are able to read and understand English in order to use the application.
- Google Calendar OAuth tokens are valid and not revoked by the user on Google's side.
- The Vercel deployment environment correctly resolves `APP_BASE_URL` for OAuth redirect URIs.
- Admin status is set directly in Supabase `app_metadata` and cannot be self-assigned by a regular user.

---

## 3. Specific Requirements

### 3.1. External Interface Requirements

#### 3.1.1. User Interfaces

Calendar's user interface consists of server-rendered HTML pages generated by Jinja2 templates and styled with CSS. The interface is organized around two layouts: a standard layout for authenticated users with a navigation bar, and a guest layout for public-facing pages. All input forms validate required fields and display flash messages for success or error feedback.

#### 3.1.2. Hardware Interfaces

The user will need common computer peripherals to interact with the application: a monitor, keyboard, and a mouse or trackpad. No special hardware is required beyond a device capable of running a modern web browser.

#### 3.1.3. Software Interfaces

Calendar communicates with Supabase to handle all authentication and database operations. The Supabase Python client library (`supabase`) is used for both the REST API routes and UI routes. UI routes additionally call `.postgrest.auth(token)` on the client so that Row-Level Security policies apply to all queries. Google Calendar OAuth is handled through the `requests_oauthlib` library.

#### 3.1.4. Communication Interfaces

The Flask application communicates with Supabase over HTTPS. Browsers communicate with the Flask server over HTTP in development and HTTPS in production. The REST API accepts and returns JSON payloads. The server-rendered UI uses standard HTML form submissions. Bearer tokens are transmitted in the HTTP Authorization header for REST API routes. Flask session cookies are used to maintain login state for UI routes.

### 3.2. Functional Requirements

Functional requirements are organized by user state and correspond to the numbered use cases in the Use Case Diagram (Figure 2). Each use case specification includes its actor, preconditions, main flow, alternate flow, and postconditions.

---

#### 3.2.1. User is Signed Out

##### 3.2.1.1. AU 01 – Register Account

Users who do not have an account may create one on the registration page (Figure 3) by navigating to the "Sign up" link on the login page.

Users who do not have an account may create one on the registration page (Figure 3) by navigating to the "Register" link on the login page.

*(Figure 3: Register Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | AU 01 |
| **Use Case Name** | Register Account |
| **Actor** | Guest User |
| **Precondition** | The user does not have an existing account and is not logged in. |
| **Main Flow** | 1. User navigates to `/ui/register`. 2. User enters a display name (optional), email address, password, and password confirmation. 3. System validates that email and password are not empty and that the two password fields match. 4. System submits the registration to Supabase Auth and sends a verification email. 5. System redirects the user to the login page with a confirmation message. |
| **Alternate Flow** | If the email or password field is empty, the system displays: "Email and password are required." If the passwords do not match, the system displays: "PASSWORDS DON'T MATCH." If Supabase returns an error (e.g., email already registered), the system displays the error message. |
| **Postcondition** | A new user account is created in Supabase Auth. The user receives a verification email and must verify it before logging in. |

---

##### 3.2.1.2. AU 02 – Login to Account

If a user has an account, they may log in on the login page (Figure 4), which is the first page users see when accessing the site.

*(Figure 4: Login Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | AU 02 |
| **Use Case Name** | Login to Account |
| **Actor** | Guest User |
| **Precondition** | The user has a verified account and is not currently logged in. |
| **Main Flow** | 1. User navigates to `/ui/login`. 2. User enters their email address and password and submits the form. 3. System authenticates the credentials with Supabase Auth. 4. System stores the user's ID, email, access token, and role in the Flask session. 5. System redirects the user to the home page or their originally intended destination. |
| **Alternate Flow** | If either field is empty, the system displays: "Email and password are required." If Supabase returns an authentication failure, the system displays: "Wrong email or password." |
| **Postcondition** | The user's session is established. The user is redirected to the home page. |

---

#### 3.2.2. User is Signed In

##### 3.2.2.1. AU 03 – Log Out

Users can log out of their account at any time using the logout link in the navigation menu.

| Field | Detail |
|---|---|
| **Use Case ID** | AU 03 |
| **Use Case Name** | Log Out |
| **Actor** | User, Admin |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User clicks the logout link in the navigation bar. 2. System removes the session data. 3. System redirects the user to the login page. |
| **Alternate Flow** | None. |
| **Postcondition** | The user's session is cleared. The user is treated as unauthenticated. |

---

##### 3.2.2.2. UA 01 – Remove Account

If a user decides to delete their account, they can do so from the account settings accessible via the navigation menu (Figure 5).

*(Figure 5: Remove Account Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | UA 01 |
| **Use Case Name** | Remove Account |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to `/ui/user/remove-account`. 2. User confirms they want to delete their account. 3. System removes the user's account and associated data from Supabase. 4. System clears the session and redirects the user to the login page. |
| **Alternate Flow** | If the user cancels the action, no changes are made and the user is returned to the previous page. |
| **Postcondition** | The user's account is deleted from Supabase. The session is cleared. |

---

##### 3.2.2.3. VC 01 – View Calendar

Once logged in, users are taken to the home page (Figure 6) where they can view their calendars and switch between them.

*(Figure 6: Home Page — Calendar View)*

| Field | Detail |
|---|---|
| **Use Case ID** | VC 01 |
| **Use Case Name** | View Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has at least one calendar (owned or shared). |
| **Main Flow** | 1. User navigates to `/ui/` (home page). 2. System retrieves all calendars owned by the user or where the user is listed in `member_ids`. 3. System displays the first calendar by default; the user can switch calendars using a selector. 4. System retrieves and displays all events associated with the selected calendar. |
| **Alternate Flow** | If the user has no calendars, the system displays a "no calendars" message and prompts the user to create one. If events cannot be loaded, the system displays an error message. |
| **Postcondition** | The user can see the selected calendar and its associated events. |

---

##### 3.2.2.4. VE 01 – View Event

Users can view events on a selected calendar from the home page (Figure 6) or the Manage Events page (Figure 9).

| Field | Detail |
|---|---|
| **Use Case ID** | VE 01 |
| **Use Case Name** | View Event |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to a calendar that contains events. |
| **Main Flow** | 1. User navigates to the home page or the Manage Events page. 2. System retrieves all events associated with the selected calendar. 3. System displays each event's title, description, and start/end times. |
| **Alternate Flow** | If no events exist for the selected calendar, the system displays a message indicating the calendar is empty. |
| **Postcondition** | The user sees a list of events for the selected calendar. |

---

##### 3.2.2.5. CM 01 – Manage Calendars

Authenticated users can manage their calendars from the Manage Calendars page (Figure 7). This use case encompasses the sub-use cases for creating calendars, managing membership, and removing calendars, as well as the nested Manage Events sub-use case.

*(Figure 7: Manage Calendars Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | CM 01 |
| **Use Case Name** | Manage Calendars |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to `/ui/user/calendars`. 2. System retrieves all calendars owned by the user. 3. System displays each calendar with controls for creating, editing membership, generating guest links, and deleting. |
| **Alternate Flow** | If the calendars list cannot be loaded, the system displays an error message. |
| **Postcondition** | The user can see all their owned calendars and take action on them. |

---

##### 3.2.2.6. CM 02 – Create Calendar

From the Manage Calendars page (Figure 7), users can create a new calendar.

| Field | Detail |
|---|---|
| **Use Case ID** | CM 02 |
| **Use Case Name** | Create Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by CM 01. |
| **Main Flow** | 1. User enters a calendar name on the Manage Calendars page and submits the form. 2. System creates the calendar in Supabase, setting the user as the owner. 3. System displays the updated calendar list with a success message. |
| **Alternate Flow** | If the name field is empty, the system displays a validation error. |
| **Postcondition** | A new calendar record is created in the `calendars` table with `owner_id` set to the requesting user. |

---

##### 3.2.2.7. CM 03 – Add Member

Calendar owners can add other users as members of a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 03 |
| **Use Case Name** | Add Member |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the calendar. Included by CM 01. |
| **Main Flow** | 1. User enters the target user's ID in the Add Member field on the Manage Calendars page and submits. 2. System verifies the target user exists. 3. System appends the target user's ID to the calendar's `member_ids` array. 4. System displays a success message. |
| **Alternate Flow** | If the target user does not exist, the system displays an error message. If the user is already a member, the system notifies the owner. |
| **Postcondition** | The target user's ID is added to `member_ids`. The added member can now view the calendar. |

---

##### 3.2.2.8. CM 04 – Remove Member

Calendar owners can remove members from a calendar they own (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 04 |
| **Use Case Name** | Remove Member |
| **Actor** | User |
| **Precondition** | The user is logged in, is the owner of the calendar, and the target member exists in `member_ids`. Included by CM 01. |
| **Main Flow** | 1. User selects a member to remove from the member list on the Manage Calendars page. 2. System removes the target user's ID from the calendar's `member_ids` array. 3. System displays a success message. |
| **Alternate Flow** | If the member ID is not found in the calendar's `member_ids`, the system displays an error. |
| **Postcondition** | The target user's ID is removed from `member_ids`. The removed member can no longer access the calendar. |

---

##### 3.2.2.9. CM 05 – Remove Calendar

Calendar owners can delete a calendar they own from the Manage Calendars page (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | CM 05 |
| **Use Case Name** | Remove Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the calendar to be deleted. Included by CM 01. |
| **Main Flow** | 1. User selects a calendar and confirms the delete action on the Manage Calendars page. 2. System verifies the user is the calendar owner. 3. System removes the calendar record from Supabase. 4. System displays the updated list with a success message. |
| **Alternate Flow** | If the user is not the calendar owner, the system returns an authorization error. |
| **Postcondition** | The calendar record is removed from the `calendars` table. |

---

##### 3.2.2.10. GL 01 – Generate Guest Link

Calendar owners can generate a shareable guest link that allows unauthenticated users to access a calendar (Figure 7).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 01 |
| **Use Case Name** | Generate Guest Link |
| **Actor** | User |
| **Precondition** | The user is logged in and owns the calendar. |
| **Main Flow** | 1. User selects a role (viewer or editor) on the Manage Calendars page and activates the guest link. 2. System generates a cryptographically secure random token and stores it in the calendar record along with the selected role and an active flag. 3. System displays the full shareable URL to the user. |
| **Alternate Flow** | If the owner deactivates the guest link, `guest_link_active` is set to false and the URL is no longer accessible. |
| **Postcondition** | The calendar record is updated with `guest_link_token`, `guest_link_role`, and `guest_link_active`. Unauthenticated users can now access the calendar via the generated URL. |

---

##### 3.2.2.11. CM 06 – Manage Events

Users can manage events on their calendars from the Manage Events page (Figure 8). This use case is included by CM 01 and itself includes the Create Event, Edit Event, and Remove Event sub-use cases.

*(Figure 8: Manage Events Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | CM 06 |
| **Use Case Name** | Manage Events |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to at least one calendar. Included by CM 01. |
| **Main Flow** | 1. User navigates to `/ui/user/events`. 2. System retrieves the user's accessible calendars. 3. System displays events for the selected calendar with controls for creating, editing, and deleting events. |
| **Alternate Flow** | If the user has no calendars, the system displays a message and prompts the user to create one first. |
| **Postcondition** | The user can view and take action on events for the selected calendar. |

---

##### 3.2.2.12. EM 01 – Create Event

From the Manage Events page (Figure 8), users can create a new event on an accessible calendar.

| Field | Detail |
|---|---|
| **Use Case ID** | EM 01 |
| **Use Case Name** | Create Event |
| **Actor** | User |
| **Precondition** | The user is logged in and has access to at least one calendar. Included by CM 06. |
| **Main Flow** | 1. User enters a title, optional description, start time, and end time, selects a target calendar, and submits the form on the Manage Events page. 2. System validates the required fields. 3. System creates the event in Supabase, linking it to the selected calendar. 4. System displays the updated event list with a success message. |
| **Alternate Flow** | If the title is missing, the system displays a validation error. If the user does not have access to the selected calendar, the system returns an authorization error. |
| **Postcondition** | A new event record is created in the `events` table with `owner_id` set to the requesting user and `calendar_ids` populated. |

---

##### 3.2.2.13. EM 02 – Edit Event

Event owners can edit the details of their events from the Edit Event page (Figure 9).

*(Figure 9: Edit Event Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | EM 02 |
| **Use Case Name** | Edit Event |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the event. Included by CM 06. |
| **Main Flow** | 1. User selects an event to edit on the Manage Events page and is taken to `/ui/user/events/<event_id>/edit`. 2. System loads the existing event data into the form. 3. User modifies the title, description, start/end time, or associated calendars and submits. 4. System updates the event record in Supabase. 5. System redirects to the events list with a success message. |
| **Alternate Flow** | If the user is not the event owner, the system redirects to the events list with an error. If required fields are missing, the system displays a validation error. |
| **Postcondition** | The event record in the `events` table is updated with the new values. |

---

##### 3.2.2.14. EM 03 – Remove Event

Event owners can delete their events from the Manage Events page (Figure 8).

| Field | Detail |
|---|---|
| **Use Case ID** | EM 03 |
| **Use Case Name** | Remove Event |
| **Actor** | User |
| **Precondition** | The user is logged in and is the owner of the event. Included by CM 06. |
| **Main Flow** | 1. User selects an event on the Manage Events page and confirms the delete action. 2. System verifies ownership. 3. System removes the event record from Supabase. 4. System displays the updated event list with a success message. |
| **Alternate Flow** | If the user is not the event owner, the system returns an authorization error. |
| **Postcondition** | The event record is removed from the `events` table. |

---

##### 3.2.2.15. EX 01 – Manage Externals

Authenticated users can view and manage their connected external calendar providers from the Manage Externals page (Figure 10). This use case includes the sub-use cases for linking, pulling, pushing, and unlinking external calendars.

*(Figure 10: Manage Externals Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | EX 01 |
| **Use Case Name** | Manage Externals |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to `/ui/user/externals` or `/ui/settings`. 2. System retrieves all external calendar records associated with the user. 3. System displays each provider connection with controls for pulling, pushing, and unlinking. |
| **Alternate Flow** | If no external connections exist, the system displays a prompt to connect a provider. |
| **Postcondition** | The user can see their connected external providers and take action on them. |

---

##### 3.2.2.16. EX 02 – Pull Data from External Calendar

Users can import events from a connected external calendar provider into a local calendar (Figure 11).

*(Figure 11: Settings Page — Google Calendar Sync)*

| Field | Detail |
|---|---|
| **Use Case ID** | EX 02 |
| **Use Case Name** | Pull Data from External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has a linked external calendar record. Included by EX 01. |
| **Main Flow** | 1. User clicks the sync/pull option on the Settings page. 2. System retrieves events from the external provider using the stored access token. 3. System creates or updates a local calendar (e.g., "Google Calendar (Synced)") and populates it with the retrieved events. 4. System displays a success message with the count of synced events. |
| **Alternate Flow** | If the access token is expired, the system attempts a token refresh. If the refresh fails, the system displays an error and prompts the user to reconnect. |
| **Postcondition** | A local calendar is created or updated with events pulled from the external provider. |

---

##### 3.2.2.17. EX 03 – Push Data to External Calendar

Users can export a local calendar to a connected external calendar provider (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 03 |
| **Use Case Name** | Push Data to External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in, has a linked external calendar record, and has at least one local calendar to export. Included by EX 01. |
| **Main Flow** | 1. User selects a local calendar and clicks the push option on the Settings page. 2. System sends the local calendar's events to the external provider using the stored access token. 3. System displays a success message confirming the push. |
| **Alternate Flow** | If the access token is expired, the system attempts a token refresh. If the refresh fails, the system displays an error and prompts the user to reconnect. |
| **Postcondition** | The selected local calendar's events are created or updated in the external provider. |

---

##### 3.2.2.18. EX 04 – Link External Calendar

Users can link a new external calendar provider account from the Settings page (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 04 |
| **Use Case Name** | Link External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in. Valid OAuth credentials are configured in the application environment. Included by EX 01. |
| **Main Flow** | 1. User navigates to `/ui/settings` and clicks "Connect Google Calendar." 2. System initiates the OAuth 2.0 authorization flow and redirects the user to Google's authorization page. 3. User grants the requested calendar permissions. 4. Google redirects back to the application with an authorization code. 5. System exchanges the code for access and refresh tokens and stores them in the `externals` table. 6. System redirects to the Settings page with a success message. |
| **Alternate Flow** | If the user denies the Google permissions request, the system returns to Settings with an error message. If OAuth credentials are not configured in the environment, the system displays an appropriate error. |
| **Postcondition** | A new record is created in the `externals` table containing the user's Google access token and refresh token. |

---

##### 3.2.2.19. EX 05 – Unlink External Calendar

Users can remove a connected external calendar provider from their account via the Settings page (Figure 11).

| Field | Detail |
|---|---|
| **Use Case ID** | EX 05 |
| **Use Case Name** | Unlink External Calendar |
| **Actor** | User |
| **Precondition** | The user is logged in and has at least one linked external calendar record. Included by EX 01. |
| **Main Flow** | 1. User navigates to `/ui/settings` and clicks "Disconnect" next to the connected provider. 2. System removes the external record from the `externals` table. 3. System displays a success message. |
| **Alternate Flow** | If the external record cannot be found, the system displays an error message. |
| **Postcondition** | The external calendar record is removed from the `externals` table. |

---

##### 3.2.2.20. FM 01 – Manage Friends

Authenticated users can manage their friends list from the Manage Friends page (Figure 12). This use case includes the sub-use cases for viewing, adding, and removing friends.

*(Figure 12: Manage Friends Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | FM 01 |
| **Use Case Name** | Manage Friends |
| **Actor** | User |
| **Precondition** | The user is logged in. |
| **Main Flow** | 1. User navigates to `/ui/user/friends`. 2. System retrieves the user's friends list from Supabase. 3. System displays each friend alongside controls for adding and removing friends. |
| **Alternate Flow** | If the friends list cannot be loaded, the system displays an error message. |
| **Postcondition** | The user can see their friends list and take action on it. |

---

##### 3.2.2.21. FM 02 – View Friends List

Users can view their current list of friends from the Manage Friends page (Figure 12).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 02 |
| **Use Case Name** | View Friends List |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by FM 01. |
| **Main Flow** | 1. System retrieves the user's `friends` array from Supabase. 2. System resolves each friend ID to their display name and email. 3. System displays the resolved list. |
| **Alternate Flow** | If the friends list is empty, the system displays a message indicating no friends have been added yet. |
| **Postcondition** | The user sees their current friends with display names and emails. |

---

##### 3.2.2.22. FM 03 – Add Friend

Users can add another user as a friend from the Manage Friends page (Figure 12).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 03 |
| **Use Case Name** | Add Friend |
| **Actor** | User |
| **Precondition** | The user is logged in. Included by FM 01. |
| **Main Flow** | 1. User enters the target user's ID or email in the Add Friend field and submits. 2. System verifies the target user exists. 3. System appends the target user's ID to the requesting user's `friends` array in Supabase. 4. System displays a success message. |
| **Alternate Flow** | If the target user does not exist, the system displays an error. If the user is already in the friends list, the system notifies the user. |
| **Postcondition** | The target user's ID is added to the user's `friends` array. |

---

##### 3.2.2.23. FM 04 – Remove Friend

Users can remove a friend from their friends list on the Manage Friends page (Figure 12).

| Field | Detail |
|---|---|
| **Use Case ID** | FM 04 |
| **Use Case Name** | Remove Friend |
| **Actor** | User |
| **Precondition** | The user is logged in and the target user exists in their `friends` array. Included by FM 01. |
| **Main Flow** | 1. User selects a friend to remove on the Manage Friends page. 2. System removes the target user's ID from the requesting user's `friends` array in Supabase. 3. System displays the updated friends list with a success message. |
| **Alternate Flow** | If the target user ID is not found in the friends array, the system displays an error. |
| **Postcondition** | The target user's ID is removed from the user's `friends` array. |

---

#### 3.2.3. Admin is Signed In

The Admin actor extends the User actor. All use cases available to a User are also available to an Admin. The following use cases are exclusive to the Admin role. Admin status is verified on every admin route via the `@ui_admin_required` decorator.

##### 3.2.3.1. AD 01 – Suspend User Account

Administrators can suspend a user account, removing the user's calendars and externals from the system (Figure 13).

*(Figure 13: Admin Panel — Suspend User)*

| Field | Detail |
|---|---|
| **Use Case ID** | AD 01 |
| **Use Case Name** | Suspend User Account |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the "admin" role. The target user account exists. |
| **Main Flow** | 1. Admin navigates to the suspend user section of the admin panel. 2. Admin enters the target user's ID and confirms the suspension. 3. System removes all calendars owned by the target user. 4. System removes all external calendar records for the target user. 5. System displays a success message. |
| **Alternate Flow** | If the target user ID does not exist, the system displays an error. If the requesting user does not have the admin role, the system returns HTTP 403. |
| **Postcondition** | The target user's calendars and externals are deleted from the database. |

---

##### 3.2.3.2. AD 02 – View System Logs

Administrators can view application-level request and event logs from the Admin panel (Figure 14).

*(Figure 14: Admin Panel — System Logs)*

| Field | Detail |
|---|---|
| **Use Case ID** | AD 02 |
| **Use Case Name** | View System Logs |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the "admin" role. |
| **Main Flow** | 1. Admin navigates to `/ui/admin/logs`. 2. System verifies the admin role. 3. The page loads and JavaScript fetches log data from `/ui/admin/logs/data`. 4. System returns log records sorted by creation time (newest first) with support for configurable limit, sort column, and sort direction. 5. Logs are displayed in a table showing timestamp, level, event type, message, user ID, path, method, and status code. |
| **Alternate Flow** | If the requesting user does not have the admin role, the system returns HTTP 403. |
| **Postcondition** | The admin can view the system log records. |

---

##### 3.2.3.3. AD 03 – Send System-Wide Notification

Administrators can send a notification message to all users in the system.

| Field | Detail |
|---|---|
| **Use Case ID** | AD 03 |
| **Use Case Name** | Send System-Wide Notification |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the "admin" role. |
| **Main Flow** | 1. Admin navigates to the notifications section of the admin panel. 2. Admin composes a notification message and submits. 3. System distributes the notification to all users. 4. System confirms the notification was sent. |
| **Alternate Flow** | If the message is empty, the system displays a validation error. If the requesting user does not have the admin role, the system returns HTTP 403. |
| **Postcondition** | All users receive the system-wide notification. |

---

##### 3.2.3.4. AD 04 – Unlink All External Calendars

Administrators can remove all external calendar connections across all users from the admin panel.

| Field | Detail |
|---|---|
| **Use Case ID** | AD 04 |
| **Use Case Name** | Unlink All External Calendars |
| **Actor** | Admin |
| **Precondition** | The user is logged in with the "admin" role. |
| **Main Flow** | 1. Admin navigates to the external calendars section of the admin panel. 2. Admin confirms the bulk unlink action. 3. System removes all records from the `externals` table. 4. System displays a success message with the count of removed records. |
| **Alternate Flow** | If no external records exist, the system informs the admin that there is nothing to unlink. If the requesting user does not have the admin role, the system returns HTTP 403. |
| **Postcondition** | All records are removed from the `externals` table. |

---

#### 3.2.4. Guest User

Guest users access the system through a guest link token generated by a calendar owner (GL 01). They do not have an account and cannot log in. Their available actions depend on the role assigned to the guest link (viewer or editor).

##### 3.2.4.1. GL 02 – View Shared Calendar

An unauthenticated user with a valid guest link can view the shared calendar and its events (Figure 15).

*(Figure 15: Public Guest Calendar Page)*

| Field | Detail |
|---|---|
| **Use Case ID** | GL 02 |
| **Use Case Name** | View Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, the calendar exists, and `guest_link_active` is true. |
| **Main Flow** | 1. User navigates to `/ui/guest/<token>`. 2. System looks up the calendar by the guest link token. 3. System retrieves and displays the calendar name and all associated events. 4. If the link role is "editor," event creation, edit, and delete controls are also shown. |
| **Alternate Flow** | If the token is invalid or the calendar cannot be found, the system displays a "not found" page. If an unexpected server error occurs, the system displays a generic error message. |
| **Postcondition** | The guest user sees the shared calendar and its events. |

---

##### 3.2.4.2. GL 03 – Create Event on Shared Calendar

A guest user with an editor-role guest link can create new events on the shared calendar (Figure 15).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 03 |
| **Use Case Name** | Create Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the "editor" role. Extends GL 02. |
| **Main Flow** | 1. Guest user fills in the event title, optional description, and optional start/end times on the public calendar page and submits. 2. System verifies the token and confirms the "editor" role. 3. System creates the event in Supabase linked to the shared calendar. 4. System reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the event creation form is not shown. If the title is missing, the system displays a validation error. |
| **Postcondition** | A new event is created in the `events` table and linked to the shared calendar. |

---

##### 3.2.4.3. GL 04 – Edit Event on Shared Calendar

A guest user with an editor-role guest link can edit existing events on the shared calendar (Figure 15).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 04 |
| **Use Case Name** | Edit Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the "editor" role. The event belongs to the shared calendar. Extends GL 02. |
| **Main Flow** | 1. Guest user selects an event to edit on the public calendar page. 2. System loads the existing event data into an edit form. 3. Guest user modifies the fields and submits. 4. System verifies the token role and updates the event in Supabase. 5. System reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the edit option is not displayed. |
| **Postcondition** | The event record is updated in the `events` table. |

---

##### 3.2.4.4. GL 05 – Delete Event on Shared Calendar

A guest user with an editor-role guest link can delete events on the shared calendar (Figure 15).

| Field | Detail |
|---|---|
| **Use Case ID** | GL 05 |
| **Use Case Name** | Delete Event on Shared Calendar |
| **Actor** | Guest User |
| **Precondition** | The guest link token is valid, active, and has the "editor" role. The event belongs to the shared calendar. Extends GL 02. |
| **Main Flow** | 1. Guest user selects an event to delete on the public calendar page. 2. System verifies the token role. 3. System removes the event from Supabase. 4. System reloads the page with a success message. |
| **Alternate Flow** | If the token role is "viewer," the delete option is not displayed. |
| **Postcondition** | The event record is removed from the `events` table. |

---

#### 3.2.5. Mis-Use Cases

The following mis-use cases identify potential misuse scenarios and describe how the system prevents or mitigates each.

##### 3.2.5.1. MU 01 – Bypass Authentication

An unauthenticated user attempts to access a protected UI route (e.g., the home page, events page, or admin panel) without being logged in.

**Mitigation:** All protected UI routes are decorated with `@ui_login_required` or `@ui_admin_required`. The decorator checks for the `ui_user` key in the Flask session. If it is absent, the user is redirected to the login page with the originally requested path stored as the `next` query parameter. The `next` parameter is validated to be a relative path to prevent open redirect attacks.

---

##### 3.2.5.2. MU 02 – Access Another User's Data

An authenticated user attempts to view, edit, or delete calendars, events, or externals that belong to a different user.

**Mitigation:** The Supabase client used in all UI routes calls `.postgrest.auth(token)` with the logged-in user's access token before executing any query. This causes Supabase's Row-Level Security policies to apply, restricting query results to records owned by or explicitly shared with the authenticated user. Ownership is additionally verified at the application layer before performing destructive operations such as deletion.

---

##### 3.2.5.3. MU 03 – Escalate Privileges to Admin

A regular user attempts to access admin-only routes (e.g., `/ui/admin/logs`) without the admin role.

**Mitigation:** Admin routes are decorated with `@ui_admin_required`, which verifies that `session["ui_user"]["role"] == "admin"`. The role value is read from Supabase `app_metadata` at login time and can only be set by a Supabase project administrator; regular users have no mechanism to modify it. Any request to an admin route from a non-admin user results in HTTP 403.

---

##### 3.2.5.4. MU 04 – Access an Invalid or Deactivated Guest Link

A user attempts to access a public calendar using a guest link token that does not exist, has been deactivated by the owner, or has been manually altered.

**Mitigation:** The system looks up the calendar by the exact token value stored in `guest_link_token`. If no matching calendar is found or `guest_link_active` is false, the system renders a "not found" page and exposes no calendar data. Guest link tokens are generated with `secrets.token_urlsafe(32)`, producing 256-bit random values that are computationally infeasible to guess or brute-force.

---

### 3.3. Performance Requirements

In order for users to have the most seamless experience, calendar and event data must be retrieved and displayed promptly on each page load. Queries to Supabase use column filters (e.g., `owner_id`, `member_ids`, `calendar_ids`) to limit the result set rather than fetching all rows. Log retrieval in the admin panel supports configurable limits (defaulting to 25 records, capped at 500) to prevent excessive data transfer. All log write operations are performed asynchronously and swallowed on failure so they cannot block or crash an incoming request. The application is deployed as a Vercel serverless function, which scales automatically under increased request volume.

### 3.4. Design Constraints

Users must have an internet connection and a modern web browser to access the application. The system will not function without a valid Supabase project configured with the correct environment variables. The `app_metadata.role` field required for admin status can only be set directly in Supabase by a project administrator and is not accessible through any user-facing interface. Google Calendar OAuth requires the application to be registered in Google Cloud Console with the correct redirect URI matching `APP_BASE_URL`. The Vercel deployment configuration in `vercel.json` routes all requests through `api/index.py`; changes to the routing structure must be reflected there. CORS origins are hardcoded in `api/index.py` and must be updated when deploying to a new domain.
