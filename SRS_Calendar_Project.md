# Software Requirement Specification

**Project Name:** Calendar

**Version:** 1.1 (Draft)

**Date:** 2026-04-15

---

## Table of Contents

- [Software Requirement Specification](#software-requirement-specification)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
    - [1.1 Purpose](#11-purpose)
    - [1.2 Scope](#12-scope)
    - [1.3 Definitions, Acronyms, Abbreviations](#13-definitions-acronyms-abbreviations)
    - [1.4 References](#14-references)
  - [2. Overall Description](#2-overall-description)
    - [2.1 Product Perspective](#21-product-perspective)
    - [2.2 Product Functions](#22-product-functions)
    - [2.3 User Classes and Characteristics](#23-user-classes-and-characteristics)
    - [2.4 Operating Environment](#24-operating-environment)
    - [2.5 Design and Implementation Constraints](#25-design-and-implementation-constraints)
  - [3. Specific Requirements](#3-specific-requirements)
    - [3.1 External Interface Requirements](#31-external-interface-requirements)
      - [3.1.1 User Interfaces](#311-user-interfaces)
      - [3.1.2 Hardware Interfaces](#312-hardware-interfaces)
      - [3.1.3 Software Interfaces](#313-software-interfaces)
      - [3.1.4 Communication Interfaces](#314-communication-interfaces)
    - [3.2 Functional Requirements](#32-functional-requirements)
      - [3.2.1 Authentication and Authorization](#321-authentication-and-authorization)
      - [3.2.2 Profile Requirements](#322-profile-requirements)
      - [3.2.3 Calendar Management Requirements](#323-calendar-management-requirements)
      - [3.2.4 Event Management Requirements](#324-event-management-requirements)
      - [3.2.5 External Calendar Record Requirements](#325-external-calendar-record-requirements)
      - [3.2.6 Operational and Error Handling Requirements](#326-operational-and-error-handling-requirements)
  - [4. System Features and Functional Requirements Summary](#4-system-features-and-functional-requirements-summary)
  - [5. Data Requirements](#5-data-requirements)
    - [5.1 Core Entities](#51-core-entities)
    - [5.2 Data Validation Rules](#52-data-validation-rules)
  - [6. Non-Functional Requirements](#6-non-functional-requirements)
    - [6.1 Security](#61-security)
    - [6.2 Reliability and Availability](#62-reliability-and-availability)
    - [6.3 Performance](#63-performance)
    - [6.4 Maintainability](#64-maintainability)
    - [6.5 Portability and Deployment](#65-portability-and-deployment)
  - [7. Verification and Acceptance Criteria](#7-verification-and-acceptance-criteria)
    - [7.1 Functional Acceptance](#71-functional-acceptance)
    - [7.2 Environment Acceptance](#72-environment-acceptance)
  - [8. Risks and Open Items](#8-risks-and-open-items)
  - [9. Traceability Summary](#9-traceability-summary)

---

## 1. Introduction

### 1.1 Purpose

This document explains what the Calendar project does today, what behavior is required, and how we confirm that behavior works.

It is written for readers inside and outside the team, including readers who are new to backend APIs.

### 1.2 Scope

Calendar is a web-based calendar management system with two user-facing surfaces:
- A JSON API for client applications
- A server-rendered web UI under `/ui/*`

Current implemented scope includes:
- User registration and login through Supabase authentication
- Protected API routes using Bearer token authentication
- Calendar create/list/delete behavior
- Event create/list/edit/delete behavior
- External calendar record create/list/delete behavior
- Authenticated user profile endpoint (`/me`)

### 1.3 Definitions, Acronyms, Abbreviations

- **API (Application Programming Interface):** A defined way for software systems to communicate.
- **Auth:** Short for authentication and authorization.
- **Bearer Token:** An access token sent in the `Authorization` header as `Bearer <token>`.
- **CORS (Cross-Origin Resource Sharing):** Browser rules that control which websites can call an API.
- **CRUD (Create, Read, Update, Delete):** The four basic data operations.
- **Endpoint:** A URL path exposed by the server, such as `/events`.
- **Flask:** The Python web framework used by this project.
- **Frontend:** The part of the system users interact with directly in the browser.
- **HTTP (Hypertext Transfer Protocol):** Standard protocol used for web requests.
- **HTTPS (Hypertext Transfer Protocol Secure):** Encrypted version of HTTP.
- **ISO 8601:** Standard date/time format, for example `2026-04-15T10:30:00Z`.
- **JSON (JavaScript Object Notation):** The data format used in API requests and responses.
- **JWT (JSON Web Token):** Token format used by Supabase for authenticated sessions.
- **OAuth (Open Authorization):** Standard used to authorize access to third-party services.
- **OS (Operating System):** The software platform on which the project runs, such as Linux, macOS, or Windows.
- **RBAC (Role-Based Access Control):** Access model based on user roles.
- **REST (Representational State Transfer):** API design style based on resources and HTTP methods.
- **SRS (Software Requirements Specification):** This requirements document.
- **Supabase:** Hosted backend platform used for authentication and database access.
- **UI (User Interface):** The pages and controls users interact with.
- **URL (Uniform Resource Locator):** Web address used to locate API and UI resources.
- **UUID (Universally Unique Identifier):** Unique ID format commonly used for records.
- **Vercel:** Deployment platform used for this serverless Python backend.

### 1.4 References

- [Supabase Documentation](https://supabase.com/docs)
- [REST API Best Practices](https://restfulapi.net/)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [ISO 8601 Date/Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)

---

## 2. Overall Description

### 2.1 Product Perspective

The Calendar system is a Flask backend that provides API endpoints and server-rendered UI pages.

High-level architecture:
- **Backend:** Flask application routes and business logic
- **Data/Auth:** Supabase database plus Supabase Auth
- **Deployment:** Vercel Python runtime
- **Communication:** HTTP/HTTPS with JSON payloads for API operations

### 2.2 Product Functions

The product currently provides these core functions:
- Register and log in users through Supabase Auth
- Validate Bearer tokens on protected API endpoints
- Create, list, and delete calendars
- Create, list, edit, and delete events
- Create, list, and delete external provider records
- Return the authenticated user's profile/session state via `/me`
- Provide server-rendered UI routes for login, registration, dashboards, and user workflows under `/ui/*`

### 2.3 User Classes and Characteristics

- **Guest:** A user who is not authenticated. Guests can access public UI pages but cannot call protected API routes.
- **Authenticated User:** A signed-in user with access to owned/member calendars and associated events.
- **Administrator (Operational Role):** Team member who manages environment variables, deployment setup, and service operations.

### 2.4 Operating Environment

- **Development OS:** Linux, macOS, Windows
- **Runtime:** Python 3.12+
- **Framework:** Flask
- **Database/Auth Provider:** Supabase
- **Deployment Target:** Vercel serverless Python runtime

### 2.5 Design and Implementation Constraints

- Required environment variables: `SUPABASE_URL`, `SUPABASE_KEY`
- API requests and responses use JSON
- Protected API routes require `Authorization: Bearer <token>`
- Runtime behavior depends on Supabase service availability
- Secrets must be provided through environment variables and must not be hard-coded

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

The project currently has two UI layers:
- **Server-rendered Flask UI:** Primary interactive UI under `/ui/*`
- **Static website scaffold (`website/*`):** Minimal placeholder assets

Implemented UI expectations:
- Login and registration forms accept email/password input
- Users can navigate to calendar, event, and settings pages from the UI
- UI session-based routes support authenticated user workflows

#### 3.1.2 Hardware Interfaces

No special hardware is required. A standard computer and web browser are sufficient.

#### 3.1.3 Software Interfaces

The system integrates with:
- Supabase Auth API (registration, login, token verification)
- Supabase database tables (`calendars`, `events`, `externals`)
- Flask request/response runtime

API endpoints:

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| / | GET | No | Redirects to `/ui/` |
| /api/auth/register | POST | No | Register a user |
| /api/auth/login | POST | No | Log in with email/password |
| /calendars | GET | Yes | List calendars where user is owner or member |
| /calendars | POST | Yes | Create a calendar |
| /calendars/{calendar_id} | DELETE | Yes | Delete owned calendar |
| /events | GET | Yes | List events linked to accessible calendars |
| /events | POST | Yes | Create event on accessible calendar(s) |
| /events/{event_id} | PUT | Yes | Edit event fields |
| /events/{event_id} | DELETE | Yes | Delete accessible event |
| /externals | GET | Yes | List current user's external records |
| /externals | POST | Yes | Create external record |
| /externals/{external_id} | DELETE | Yes | Delete current user's external record |
| /me | GET | Yes | Return authenticated user/session summary |

UI route groups under `/ui/*` include:
- Auth routes (login/register/logout)
- Dashboard routes
- User calendar and event management routes
- Settings routes for external provider links
- Admin pages for operational tasks

API behavior requirements:
- API requests and responses shall use JSON payloads.
- Protected API routes shall require Bearer token authentication.
- API routes shall use consistent HTTP status code behavior.

#### 3.1.4 Communication Interfaces

- Development may run over HTTP.
- Production deployments should use HTTPS.
- API clients send authentication credentials through Bearer tokens in headers.
- Browser access is controlled by CORS policy on API routes.

### 3.2 Functional Requirements

Each requirement below is written as a testable "shall" statement.

#### 3.2.1 Authentication and Authorization

| ID | Requirement |
|---|---|
| FR-AUTH-1 | The system shall accept email and password for user registration. |
| FR-AUTH-2 | The system shall support optional name metadata during registration. |
| FR-AUTH-3 | The system shall return HTTP 201 for successful registration. |
| FR-AUTH-4 | The system shall authenticate credentials through Supabase Auth. |
| FR-AUTH-5 | The system shall return authenticated session and user data for successful login. |
| FR-AUTH-6 | The system shall return HTTP 401 for invalid login credentials. |
| FR-AUTH-7 | The system shall require Bearer token authentication on protected API endpoints. |
| FR-AUTH-8 | The system shall validate Bearer tokens against Supabase user validation. |
| FR-AUTH-9 | The system shall reject missing or invalid Bearer tokens with HTTP 401. |

#### 3.2.2 Profile Requirements

| ID | Requirement |
|---|---|
| FR-PROF-1 | The system shall expose `/me` for authenticated API users. |
| FR-PROF-2 | The `/me` response shall include user identity fields and authenticated session state. |
| FR-PROF-3 | The `/me` endpoint shall return HTTP 401 when a valid Bearer token is not provided. |

#### 3.2.3 Calendar Management Requirements

| ID | Requirement |
|---|---|
| FR-CAL-1 | The system shall allow authenticated users to create calendars with a required `name` field. |
| FR-CAL-2 | The system shall assign the requesting user as calendar owner when creating a calendar. |
| FR-CAL-3 | The system shall list calendars where the user is owner or listed in `member_ids`. |
| FR-CAL-4 | The system shall allow calendar deletion only for the calendar owner. |
| FR-CAL-5 | The system shall return an error when deleting a non-owned or missing calendar. |
| FR-CAL-6 | The system shall return HTTP 201 for successful calendar creation. |

#### 3.2.4 Event Management Requirements

| ID | Requirement |
|---|---|
| FR-EVT-1 | The system shall require event `title` and at least one `calendar_id` on event creation. |
| FR-EVT-2 | The system shall allow event creation only if the user can access at least one target calendar. |
| FR-EVT-3 | The system shall list events associated with calendars accessible to the authenticated user. |
| FR-EVT-4 | The system shall support event updates for title, description, timestamps, and `calendar_ids`. |
| FR-EVT-5 | The system shall enforce calendar-based authorization on event edit and delete operations. |
| FR-EVT-6 | The system shall return HTTP 404 when an event ID does not exist. |
| FR-EVT-7 | The system shall return HTTP 201 for successful event creation. |

#### 3.2.5 External Calendar Record Requirements

| ID | Requirement |
|---|---|
| FR-EXT-1 | The system shall allow authenticated users to create external records with required `provider` and `url` fields. |
| FR-EXT-2 | The system shall support optional `access_token` and `refresh_token` metadata on external records. |
| FR-EXT-3 | The system shall return only records scoped to the authenticated user. |
| FR-EXT-4 | The system shall allow deletion only for external records scoped to the authenticated user. |
| FR-EXT-5 | The system shall return HTTP 201 for successful external record creation. |

#### 3.2.6 Operational and Error Handling Requirements

| ID | Requirement |
|---|---|
| FR-OPS-1 | The system shall log incoming API requests and response status codes. |
| FR-OPS-2 | The system shall return JSON error payloads for common client and server errors. |
| FR-OPS-3 | The system shall use consistent HTTP status code behavior across API endpoints. |

---

## 4. System Features and Functional Requirements Summary

The current system includes:
- Authentication and authorization
- Calendar management (create, list, delete)
- Event management (create, list, edit, delete)
- External provider record management
- Profile/session endpoint (`/me`)
- Server-rendered UI route groups for auth, user workflows, settings, and admin operations

---

## 5. Data Requirements

### 5.1 Core Entities

**Users** (primarily managed by Supabase Auth):
- `id` (UUID/string) - user identifier
- `email` (string) - sign-in email
- `name` (optional string) - profile metadata when provided at registration

**Calendars:**
- `id` (UUID/string) - calendar identifier
- `name` (string, required) - calendar display name
- `owner_id` (UUID/string, required) - owner user ID
- `member_ids` (array of user IDs) - users with access
- `events` (array of event IDs, optional) - linked event identifiers
- `age_timestamp` (timestamp) - creation/audit timestamp from data layer

**Events:**
- `id` (UUID/string) - event identifier
- `owner_id` (UUID/string) - event creator ID
- `calendar_ids` (array, required) - one or more associated calendars
- `title` (string, required) - event title
- `description` (string, optional) - event details
- `start_timestamp` (ISO 8601 string, optional) - start time
- `end_timestamp` (ISO 8601 string, optional) - end time
- `age_timestamp` (timestamp) - creation/audit timestamp from data layer

**Externals:**
- `id` (UUID/string) - external record identifier
- `owner_id` (UUID/string) - record owner
- `user_id` (UUID/string) - associated user
- `url` (string, required) - provider API/resource URL
- `provider` (string, required) - provider name/type
- `access_token` (string, optional) - provider access token
- `refresh_token` (string, optional) - provider refresh token

### 5.2 Data Validation Rules

- **DR-1:** Required fields shall be validated before inserts and updates.
- **DR-2:** IDs shall be unique and consistent with Supabase schema constraints.
- **DR-3:** Date/time fields should use ISO 8601 format.

---

## 6. Non-Functional Requirements

### 6.1 Security

- **NFR-SEC-1:** Secrets shall be supplied through environment variables and never hard-coded.
- **NFR-SEC-2:** Protected API endpoints shall reject unauthorized access.
- **NFR-SEC-3:** Production traffic should use HTTPS.

### 6.2 Reliability and Availability

- **NFR-REL-1:** API routes shall return stable JSON error payloads for common failures.
- **NFR-REL-2:** Token validation failures shall deny access by default.

### 6.3 Performance

- **NFR-PERF-1:** Typical API calls should respond within reasonable web API latency under expected class-project load.
- **NFR-PERF-2:** Query operations should use database filters to reduce payload size.

### 6.4 Maintainability

- **NFR-MAIN-1:** Code structure shall remain modular (`api`, `models`, `utils`, `scripts`, `website`).
- **NFR-MAIN-2:** Integration checks shall remain runnable from project root.

### 6.5 Portability and Deployment

- **NFR-DEP-1:** Backend shall be deployable through Vercel Python build configuration.
- **NFR-DEP-2:** Project shall run inside virtual environments across Linux, macOS, and Windows.

---

## 7. Verification and Acceptance Criteria

### 7.1 Functional Acceptance

- **AC-1:** Registration and login flows return expected status codes and payload structures.
- **AC-2:** `/me` returns HTTP 401 without a token and HTTP 200 with a valid token.
- **AC-3:** Calendar operations enforce owner/member access rules.
- **AC-4:** Event operations enforce calendar-based authorization.
- **AC-5:** External record operations are user-scoped.
- **AC-6:** Key middleware and endpoint behaviors are script-checkable from the `scripts/` directory.

### 7.2 Environment Acceptance

- **AC-7:** System starts when `SUPABASE_URL` and `SUPABASE_KEY` are present.
- **AC-8:** Missing required environment variables result in explicit startup/runtime failure.

---

## 8. Risks and Open Items

- **RISK-1:** UI requirements are still evolving as the team expands user features.
- **RISK-2:** External provider synchronization behavior needs much more work.
- **RISK-3:** Current checks are mostly script-driven; full automated test coverage is still in progress.
- **RISK-4:** Performance testing under realistic production-like load has not been considered.
- **RISK-5:** Third-party provider requirements (for example Google and Microsoft flows) may cause issues in the future regarding API call limits.

---

## 9. Traceability Summary

This SRS is aligned to the current repository implementation and operational intent.

Primary implementation references:
- [api/index.py](api/index.py) - Main Flask app and API routes
- [api/auth_routes.py](api/auth_routes.py) - Registration/login behavior
- [api/ui_routes.py](api/ui_routes.py) - Server-rendered UI routes and flows
- [models/calendar.py](models/calendar.py) - Calendar data behavior
- [models/event.py](models/event.py) - Event data behavior
- [models/external.py](models/external.py) - External record behavior
- [utils/auth.py](utils/auth.py) - Bearer token middleware
- [utils/supabase_client.py](utils/supabase_client.py) - Supabase client configuration
- [scripts/](scripts/) - Script-based integration checks