# Lab 12: Webex Messaging API

## Lab Introduction

Webex provides REST APIs for identities, rooms, memberships, messages, webhooks, and collaboration workflows. This lab authenticates a bot or developer identity, inventories accessible rooms, creates a dedicated training room, posts a Markdown message, retrieves it, and cleans up the room. Mutating calls require an explicit safety flag.

## Learning Objectives

- Use Bearer-token authentication.
- Interpret Webex resource IDs and JSON responses.
- List and create rooms and messages.
- Handle `401`, `403`, `404`, and `429` responses.
- Respect `Retry-After` with bounded retries.
- Protect and revoke access tokens.

## Task 1: Prepare Webex Access

Create a Webex bot for durable course use or use a short-lived developer token for personal testing. A bot can access only rooms in which it is a member. Never commit or display the token.

Create `lab12-webex-api` in GitLab, copy the supplied files, then:

```bash
source "$HOME/.venvs/ccnpauto/bin/activate"
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

## Task 2: Authenticate and List Rooms

Enter the token but leave changes disabled:

```dotenv
ALLOW_WEBEX_CHANGES=false
```

Run:

```bash
python webex_lab.py
```

The script calls `/people/me` and `/rooms`. Interpret identity, room type, and opaque IDs. HTTP 401 usually indicates an expired or invalid token; 403 indicates insufficient scope or membership.

## Task 3: Create a Test Room and Message

Enable changes and run again:

```dotenv
ALLOW_WEBEX_CHANGES=true
WEBEX_ROOM_TITLE=CCNPAUTO Lab 12 - YOUR_NAME
```

```bash
python webex_lab.py | tee /tmp/lab12-output.txt
```

Confirm the room and Markdown message in the Webex client. The message response includes sender, creation time, room ID, and message ID.

## Task 4: Inspect Requests Manually

Use the token only through a protected shell variable:

```bash
curl --silent https://webexapis.com/v1/people/me \
  --header "Authorization: Bearer $WEBEX_ACCESS_TOKEN" \
  --header "Accept: application/json" | jq
```

Do not paste tokens into screenshots or shell-history examples.

## Task 5: Clean Up

Copy the printed `ROOM_ID` and delete only the lab-created room:

```bash
curl --request DELETE \
  --url "https://webexapis.com/v1/rooms/ROOM_ID" \
  --header "Authorization: Bearer $WEBEX_ACCESS_TOKEN"
```

Expect HTTP 204. Return the flag to false and revoke temporary tokens when finished.

## Key Takeaways

- Webex APIs use Bearer tokens and opaque resource IDs.
- Membership and scopes constrain accessible resources.
- Collaboration automation must handle rate limits and avoid message loops.
- A bot token is an application identity and requires secret-management controls.

## References

- [Webex authentication](https://developer.webex.com/create/docs/authentication)
- [Webex Rooms API](https://developer.webex.com/messaging/docs/api/v1/rooms)
- [Webex Messages API](https://developer.webex.com/messaging/docs/api/v1/messages)
