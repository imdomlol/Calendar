# Software Requirement Specification

**Project Name:** Calendar

**Version:** 1.0 (Draft)

**Date:** 2026-04-06

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [1.1 Purpose](#11-purpose)
   - [1.2 Scope](#12-scope)
   - [1.3 Definitions, Acronyms, Abbreviations](#13-definitions-acronyms-abbreviations)
   - [1.4 References](#14-references)
2. [Overall Description](#2-overall-description)
   - [2.1 Product Perspectives](#21-product-perspectives)
   - [2.2 Product Functions](#22-product-functions)
   - [2.3 User Classes and Characteristics](#23-user-classes-and-characteristics)
   - [2.4 Operating Environment](#24-operating-environment)
   - [2.5 Design and Implementation Constraints](#25-design-and-implementation-constraints)
3. [Specific Requirements](#3-specific-requirements)
   - [3.1 External Interface Requirements](#31-external-interface-requirements)
   - [3.2 Functional Requirements](#32-functional-requirements)
4. [System Features and Functional Requirements](#4-system-features-and-functional-requirements)
5. [Data Requirements](#5-data-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Verification and Acceptance Criteria](#7-verification-and-acceptance-criteria)
8. [Risks and Open Items](#8-risks-and-open-items)
9. [Future Enhancements](#9-future-enhancements)

---

## 1. Introduction

### 1.1 Purpose

This document aims to outline the requirements for the Calendar project. The requirements must be met and tested throughout the project's development.

### 1.2 Scope
Calendar is a web-based calendar management system with:
- User authentication (registration, login, token validation)
- Calendar creation, listing, and deletion
- Event creation, listing, editing, and deletion
- External calendar connection record management
- Protected user profile endpoint

The system uses Supabase for authentication and persistence, and is intended for deployment as a Python serverless backend.

### 1.3 Definitions, Acronyms, Abbreviations

- **API:** Application Programming Interface
- **JWT:** JSON Web Token
- **SRS:** Software Requirements Specification
- **CRUD:** Create, Read, Update, Delete
- **RBAC:** Role-Based Access Control
- **CORS:** Cross-Origin Resource Sharing
- **UUID:** Universally Unique Identifier
- **ISO 8601:** International standard for date and time representation
- **REST:** Representational State Transfer
- **Backend:** Server-side application logic and data management
- **Frontend:** Client-side user interface and user interactions
- **Supabase:** Open-source Firebase alternative with PostgreSQL database and authentication
- **Bearer Token:** Access token sent in HTTP Authorization header for authentication
- **Endpoint:** HTTP route/path on the API server

### 1.4 References

- [Supabase Documentation](https://supabase.com/docs)
- [REST API Best Practices](https://restfulapi.net/)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [ISO 8601 Date/Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)

---

## 2. Overall Description

### 2.1 Product Perspectives

#### 2.1.1 System Interface

The Calendar project is a backend-centric calendar service exposed through REST-style HTTP endpoints. The system architecture consists of:

- **Frontend:** Minimal website client (HTML/CSS/JavaScript) for demonstrative purposes
- **Backend:** Python Flask API deployed on Vercel as a serverless backend
- **Database/Auth:** Supabase (PostgreSQL database with built-in authentication)
- **Communication:** JSON request/response payloads over HTTP/HTTPS

#### 2.1.2 User Interface

The current system provides a minimal web interface with the following elements:
- `index.html`: Welcome/navigation page
- `app.js`: Client-side logic for API interactions
- `styles.css`: Styling for web interface

**Note:** Frontend UI is primarily demonstrative. Full UI requirements for user calendar management and event interaction remain to be defined.

#### 2.1.3 Software Interface

The Calendar system interacts with the following external services and technologies:

- **Supabase REST API:** Database operations and user authentication
- **Python Packages:**
  - `flask`: Web framework for routing and request handling
  - `flask-cors`: Cross-Origin Resource Sharing support
  - `supabase`: Client library for Supabase API
  - `python-dotenv`: Environment variable management
  - `msal`: Microsoft authentication (for future external provider integration)
  - `google-auth`: Google authentication (for future external provider integration)
- **External Provider APIs:** [PLACEHOLDER - Microsoft Graph API, Google Calendar API, etc.]

### 2.2 Product Functions

- Register users and authenticate users through Supabase Auth
- Validate bearer tokens for protected endpoints
- Manage calendars owned by users and calendars shared via member IDs
- Manage events associated with one or more calendars
- Store linked external calendar provider records per user
- Return authenticated user profile/session state

### 2.3 User Classes and Characteristics

**Guest:** Accesses calendars/events where membership does not matter. May be a viewer, editor, or owner depending on calendar sharing settings.

**Member:** Accesses calendars/events where membership exists. May be a viewer, editor, or owner depending on calendar sharing settings.

**Administrator:** Configures deployment environment variables, manages Supabase project setup, and maintains the API infrastructure.

### 2.4 Constraints

- **Required Environment Variables:** `SUPABASE_URL`, `SUPABASE_KEY`
- **Supabase Schema:** Must include tables for users, calendars, events, and externals
- **CORS Policy:** Must allow configured frontend host(s)
- **Authentication:** Depends on Supabase auth API reachability
- **API Format:** JSON request/response payloads
- **Transport:** HTTPS in production environments
- **Assumptions and Dependencies:**
  - Supabase project and API credentials are valid
  - Auth tokens are issued by the same Supabase project configured in runtime
  - Client applications send `Authorization: Bearer <token>` for protected routes
  - Secrets shall be provided via environment variables and never hard-coded
- **Time:** Everyone contributing is a student and has other responsibilities

### 2.5 Assumptions and Dependencies

- **OS:** Linux, macOS, Windows (development and deployment)
- **Runtime:** Python 3.12+
- **Backend Framework:** Flask
- **Database/Auth Provider:** Supabase (PostgreSQL)
- **Deployment Target:** Vercel Python runtime
- **Dependencies:** See `requirements.txt`

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

The Calendar system currently exposes a minimal demonstration web interface and a primary REST API interface.

UI-related requirements:
- Login and registration input forms shall accept email and password.
- Navigation controls shall allow users to access authentication, calendar, event, and external-link actions.
- User-facing forms shall submit and receive JSON-compatible values for API integration.
- API documentation endpoint/specification remains a planned enhancement.

#### 3.1.2 Hardware Interfaces

No special hardware requirements. Standard computer peripherals (monitor, keyboard, mouse/trackpad) required for user interaction with the web application.

#### 3.1.3 Software Interfaces

The system integrates with Supabase services and exposes HTTP endpoints for client applications.

External software interfaces:
- Supabase Auth API for registration, login, and token validation.
- Supabase database tables for calendars, events, and external records.
- Flask runtime for request handling and JSON response generation.

API endpoints:

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| / | GET | No | Welcome/health-style message |
| /api/auth/register | POST | No | Register a user |
| /api/auth/login | POST | No | Login with email/password |
| /calendars | GET | Yes | List calendars owned/member-visible to user |
| /calendars | POST | Yes | Create a calendar |
| /calendars/{calendar_id} | DELETE | Yes | Delete owned calendar |
| /events | GET | Yes | List events overlapping user calendars |
| /events | POST | Yes | Create event on at least one accessible calendar |
| /events/{event_id} | PUT | Yes | Edit event fields |
| /events/{event_id} | DELETE | Yes | Delete accessible event |
| /externals | GET | Yes | List linked external records for user |
| /externals | POST | Yes | Create linked external record |
| /externals/{external_id} | DELETE | Yes | Delete owned external record |
| /me | GET | Yes | Return authenticated user/session info |

API behavior requirements:
- Requests and responses shall use JSON payloads.
- Protected routes shall require Authorization: Bearer <token>.
- The service shall use standard HTTP status codes (200, 201, 400, 401, 403, 404, 500).

#### 3.1.4 Communications Interfaces

- The system shall communicate over HTTP in development and HTTPS in production.
- Client-server communication shall use REST-style request/response patterns.
- Authentication credentials shall be transmitted using bearer tokens in HTTP headers.
- CORS policy shall allow configured frontend origin(s).

### 3.2 Functional Requirements

Functional requirements are grouped by feature area. Each requirement is uniquely identified and written as a verifiable "shall" statement.

#### 3.2.1 Authentication and Authorization

| ID | Requirement |
|---|---|
| FR-AUTH-1 | The system shall accept email and password to register a user. |
| FR-AUTH-2 | The system shall optionally capture and store user name metadata during registration. |
| FR-AUTH-3 | The system shall return HTTP 201 for successful user registration. |
| FR-AUTH-4 | The system shall authenticate user credentials through Supabase Auth. |
| FR-AUTH-5 | The system shall return authenticated session/user data for successful login requests. |
| FR-AUTH-6 | The system shall return HTTP 401 for invalid login credentials. |
| FR-AUTH-7 | The system shall require a bearer token on protected endpoints. |
| FR-AUTH-8 | The system shall validate bearer tokens against Supabase user/session validation mechanisms. |
| FR-AUTH-9 | The system shall reject missing or invalid tokens with HTTP 401. |

#### 3.2.2 Profile Requirements

| ID | Requirement |
|---|---|
| FR-PROF-1 | The system shall expose /me for authenticated users. |
| FR-PROF-2 | The /me response shall include authenticated user identity and session state. |
| FR-PROF-3 | The /me endpoint shall return HTTP 401 when no valid token is provided. |

#### 3.2.3 Calendar Management Requirements

| ID | Requirement |
|---|---|
| FR-CAL-1 | The system shall allow authenticated users to create calendars with a required name field. |
| FR-CAL-2 | The system shall assign the requesting user as owner of each created calendar. |
| FR-CAL-3 | The system shall list calendars where the user is owner or listed in member_ids. |
| FR-CAL-4 | The system shall allow calendar deletion only by the calendar owner. |
| FR-CAL-5 | The system shall return an authorization or not-found error when attempting to delete a non-owned or missing calendar. |
| FR-CAL-6 | The system shall return HTTP 201 for successful calendar creation. |

#### 3.2.4 Event Management Requirements

| ID | Requirement |
|---|---|
| FR-EVT-1 | The system shall allow event creation with required title and at least one calendar_id. |
| FR-EVT-2 | The system shall permit event creation only when the user has access to at least one target calendar. |
| FR-EVT-3 | The system shall list events associated with calendars accessible by the authenticated user. |
| FR-EVT-4 | The system shall allow event updates for title, description, time range, and associated calendar_ids. |
| FR-EVT-5 | The system shall restrict event edit and delete operations to authorized users based on calendar access policy. |
| FR-EVT-6 | The system shall return HTTP 404 when a requested event ID does not exist. |
| FR-EVT-7 | The system shall return HTTP 201 for successful event creation. |

#### 3.2.5 External Calendar Record Requirements

| ID | Requirement |
|---|---|
| FR-EXT-1 | The system shall allow authenticated users to create external calendar link records with provider and url. |
| FR-EXT-2 | The system shall support optional access_token and refresh_token metadata in external records. |
| FR-EXT-3 | The system shall return only external records owned by the authenticated user. |
| FR-EXT-4 | The system shall allow deletion only for external records owned by the authenticated user. |
| FR-EXT-5 | The system shall return HTTP 201 for successful external record creation. |

#### 3.2.6 Operational and Error Handling Requirements

| ID | Requirement |
|---|---|
| FR-OPS-1 | The system shall log incoming HTTP requests and corresponding response status codes. |
| FR-OPS-2 | The system shall return JSON error payloads for common client and server errors. |
| FR-OPS-3 | The system shall use consistent status code semantics across endpoints for success and failure outcomes. |

---

## 4 System Features and Functional Requirements

The system includes the following major feature areas:
- User authentication and authorization
- Calendar management (create, list, delete)
- Event management (CRUD operations)  
- External provider integration records management
- User profile and session management

---

## 5. Data Requirements

### 5.1 Core Entities

**Users** (managed by Supabase auth + optional users table metadata):
- `id` (string/UUID) - Primary identifier
- `email` (string) - User email address
- `name` (optional string) - User display name

**Calendars:**
- `id` (string/UUID) - Primary identifier
- `name` (string, required) - Calendar name
- `owner_id` (string/UUID, required) - Calendar owner
- `member_ids` (array of user IDs) - Shared members
- `events` (array of event IDs, optional) - Associated events
- `age_timestamp` (timestamp, system-managed) - Creation timestamp

**Events:**
- `id` (string/UUID) - Primary identifier
- `owner_id` (string/UUID) - Event owner
- `calendar_ids` (array, required) - Associated calendars
- `title` (string, required) - Event title
- `description` (string, optional) - Event description
- `start_timestamp` (ISO 8601 datetime, optional) - Event start time
- `end_timestamp` (ISO 8601 datetime, optional) - Event end time
- `age_timestamp` (timestamp, system-managed) - Creation timestamp

**Externals:**
- `id` (string/UUID) - Primary identifier
- `owner_id` (string/UUID) - External record owner
- `user_id` (string/UUID) - Associated user
- `url` (string, required) - External calendar URL
- `provider` (string, required) - Calendar provider type
- `access_token` (string, optional) - OAuth access token
- `refresh_token` (string, optional) - OAuth refresh token

### 5.2 Data Validation Rules

- **DR-1:** Required fields must be validated before inserts/updates.
- **DR-2:** IDs must be unique and consistent with Supabase schema constraints.
- **DR-3:** Datetime values should use ISO 8601 format.

---

## 6. Non-Functional Requirements

### 6.1 Security

- **NFR-SEC-1:** Secrets shall be provided via environment variables and never hard-coded.
- **NFR-SEC-2:** Protected endpoints shall reject unauthorized access.
- **NFR-SEC-3:** Transport should use HTTPS in deployed environments.

### 6.2 Reliability and Availability

- **NFR-REL-1:** API shall return deterministic JSON error payloads for common failures.
- **NFR-REL-2:** Token validation failures shall fail closed (deny access).

### 6.3 Performance

- **NFR-PERF-1:** Typical endpoint responses should complete within acceptable web API latency bounds under expected project load.
- **NFR-PERF-2:** Query operations should leverage table filters to reduce payload size.

### 6.4 Maintainability

- **NFR-MAIN-1:** Code shall preserve modular separation (api/models/utils/scripts).
- **NFR-MAIN-2:** Integration checks should remain scriptable from project root.

### 6.5 Portability and Deployment

- **NFR-DEP-1:** The backend shall be deployable via Vercel Python build configuration.
- **NFR-DEP-2:** The system shall run in virtual environments across major OS platforms.

---

## 7. Verification and Acceptance Criteria

### 7.1 Functional Acceptance

- **AC-1:** Register/login flows return expected status codes and payloads.
- **AC-2:** `/me` returns 401 without token and 200 with valid token.
- **AC-3:** Calendar CRUD operations enforce owner/member access policy.
- **AC-4:** Event CRUD operations enforce calendar-based authorization.
- **AC-5:** External record CRUD is user-scoped.

### 7.2 Environment Acceptance

- **AC-6:** System starts with valid `SUPABASE_URL` and `SUPABASE_KEY`.
- **AC-7:** Missing required environment variables produce explicit runtime failure.

---

## 8. Risks and Open Items

- **RISK-1:** Current frontend is minimal; complete UI requirements remain to be defined.
- **RISK-2:** External provider sync behavior is partially represented and needs full product definition.
- **RISK-3:** Placeholder test scripts are not complete automated test coverage.
- **RISK-4:** Final authorization semantics (404 vs 403 behavior for some ownership checks) should be standardized.
- **RISK-5:** Performance testing under production load has not been conducted.
- **RISK-6:** [PLACEHOLDER] Specific third-party provider integration requirements (Microsoft Graph, Google Calendar API).

---

## 9. Future Enhancements

- **FE-1:** Recurring events and recurrence rules.
- **FE-2:** Calendar sharing invitations and role levels (owner/editor/viewer).
- **FE-3:** Bi-directional sync with external providers.
- **FE-4:** Full web UI with authentication and event visualization.
- **FE-5:** [PLACEHOLDER] Real-time event notifications.
- **FE-6:** [PLACEHOLDER] Calendar search and filtering capabilities.

---

## 10. Traceability Summary

This SRS is based on the current repository structure and implementation intent from backend modules, utility middleware, deployment config, and available integration scripts. The document defines core API endpoints, functional requirements, and data models for the Calendar project backend.

**Key Implementation Files:**
- [api/index.py](api/index.py) - Main Flask application
- [api/auth_routes.py](api/auth_routes.py) - Authentication endpoints
- [models/](models/) - Data models (calendar, event, external, storage)
- [utils/](utils/) - Utility functions (auth middleware, Supabase client)