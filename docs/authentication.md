# Authentication Setup

CRUSE uses [Clerk](https://clerk.com) for authentication. Clerk provides
pre-built sign-in/sign-up components, JWT-based session tokens, and a hosted
dashboard for user management.

## Prerequisites

- A Clerk account (free tier supports 50K monthly active users)
- Your CRUSE backend and frontend deployed or running locally

## Step 1: Create a Clerk Application

1. Go to [clerk.com](https://clerk.com) and sign up
2. Create a new application
3. Choose your sign-in methods (email, Google, GitHub, etc.)
4. Copy your keys from the **API Keys** page:
   - **Publishable key** (`pk_test_...` or `pk_live_...`)
   - **Secret key** (`sk_test_...` or `sk_live_...`)

## Step 2: Configure Session Token

By default, Clerk JWTs do not include user metadata. You must customize
the session token so the backend can read the user's role.

1. In the Clerk Dashboard, go to **Sessions** > **Customize session token**
1. Set the template to:

```json
{
  "metadata": "{{user.public_metadata}}"
}
```

1. Save the template

This adds the user's public metadata (including `role`) to every JWT.

## Step 3: Set Environment Variables

### Backend

Create or edit `apps/cruse/backend/.env`:

```bash
CLERK_ISSUER_URL=https://your-clerk-domain.clerk.accounts.dev
CLERK_SECRET_KEY=sk_test_...
```

The issuer URL is found in Clerk Dashboard under **API Keys** > **Advanced** >
**JWT Issuer**.

### Frontend

Create or edit `apps/cruse/frontend/.env.local`:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
```

### Docker

When running with Docker Compose, set these in your shell or a `.env` file
next to `docker-compose.yml`:

```bash
export CLERK_SECRET_KEY=sk_test_...
export CLERK_ISSUER_URL=https://your-clerk-domain.clerk.accounts.dev
export NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

## Step 4: Assign Admin Role

The admin console is only visible to users with the `admin` role.

1. In the Clerk Dashboard, go to **Users**
2. Click on the user you want to make admin
3. Scroll to **Public metadata** and set:

```json
{
  "role": "admin"
}
```

1. Save. The user must sign out and sign back in to pick up the new role.

## How It Works

### Backend (JWT Verification)

The backend verifies Clerk JWTs locally using JWKS (no API call per request):

1. On startup, fetches the public key set from
   `{CLERK_ISSUER_URL}/.well-known/jwks.json`
2. Each request's `Authorization: Bearer <token>` is verified against
   the cached keys (RS256)
3. The user's `role` is extracted from the `metadata` claim in the JWT
4. JWKS keys are refreshed every hour (handles key rotation)

### Frontend (Route Protection)

- Next.js middleware redirects unauthenticated users to `/sign-in`
- The `useAuthenticatedFetch` hook attaches the Bearer token to all
  API requests
- WebSocket connections pass the token as a query parameter
  (`?token=<jwt>`) since browsers do not support custom WebSocket headers

### Role-Based Access

| Role | Permissions |
|------|------------|
| `user` | Create/view/delete own sessions, chat, view network graphs |
| `admin` | All user permissions + admin console, view all sessions, usage stats |

The admin console icon only appears when the backend confirms the user
has the `admin` role via `GET /api/me`.

## Troubleshooting

### "Missing secretKey" error on frontend

The `CLERK_SECRET_KEY` must be set in the frontend environment. Clerk's
Next.js middleware runs server-side and needs the secret key. Add it to
`.env.local`.

### Admin panel not showing after setting role

Clerk does not include public metadata in JWTs by default. Make sure you
completed [Step 2](#step-2-configure-session-token) (session token
customization). Sign out and sign back in after making changes.

### SSO callback stuck on blank page

Ensure the `<SignIn>` and `<SignUp>` components have `routing="path"`
and `path="/sign-in"` (or `/sign-up`) props. Without these, Clerk
cannot route the OAuth callback correctly.

### JWKS fetch warning on backend startup

If you see `CLERK_ISSUER_URL not set, skipping JWKS fetch`, the
`CLERK_ISSUER_URL` environment variable is missing. Set it to your
Clerk instance URL.
