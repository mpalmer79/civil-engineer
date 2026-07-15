# Email Delivery

How Civil Engineer AI sends account-lifecycle email, added in Production Phase
4D. It builds on the mailer abstraction from Phase 4B/4C and pairs with
`docs/AUTH_LIFECYCLE.md`.

Email delivery is for account lifecycle only (password reset and team
invitations). It carries no review-support content and makes no engineering or
compliance claim. A human reviewer remains responsible for every finding.

## Providers

The provider is selected by `EMAIL_PROVIDER`:

- `noop` (default): the mailer records a redacted delivery log and sends nothing.
  This keeps local development and tests free of any email service.
- `smtp`: the mailer delivers real email through a configured SMTP server using
  the Python standard library (`smtplib`), so no third-party dependency is
  required.

Provider-specific code is isolated in `backend/app/services/mailer.py`. Business
logic calls `mailer.send_email(...)` and never imports a vendor client. A future
HTTP provider (for example a transactional email API) can be added behind the
same interface without touching the reset or invitation flows.

## Configuration

Backend service variables (set on the backend only):

- `EMAIL_PROVIDER` - `noop` or `smtp`. Default `noop`.
- `EMAIL_FROM` - the envelope sender address.
- `APP_PUBLIC_BASE_URL` - the public frontend origin used to build reset and
  invitation links in emails (for example `https://app.example.com`).
- `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT` (default 587), `EMAIL_SMTP_USERNAME`,
  `EMAIL_SMTP_PASSWORD`, `EMAIL_SMTP_USE_TLS` (default true) - SMTP settings, read
  only when `EMAIL_PROVIDER=smtp`.

The SMTP provider is considered configured to send only when `EMAIL_SMTP_HOST` is
set (see `Settings.email_configured`). If `EMAIL_PROVIDER=smtp` but no host is
set, the mailer treats it as noop and sends nothing rather than failing.

## Security

- No SMTP credential is ever logged.
- No reset token, invitation token, full reset/invite URL, email subject, or
  email body is ever logged. The mailer logs only the provider, the message
  category, a redacted recipient, and whether a message was sent.
- A delivery failure is caught and reported as `sent: false` with a generic
  `delivery_failed` error. The underlying exception is not logged, because it can
  contain the recipient or server hints.
- Outside production, the password reset and invitation responses may include a
  dev token so the flow can be completed locally without a provider. This is
  forced off in production (see `Settings.expose_dev_tokens`); production never
  returns a reset or invitation token in an API response.

## Password reset email

When `POST /api/v1/auth/password-reset/request` matches an active account, the
mailer sends a reset email built by `email_content.password_reset_email`. The
email contains:

- A concise subject.
- A reset link to `{APP_PUBLIC_BASE_URL}/reset-password/confirm?token=...`. The
  raw token appears only in this link.
- An expiration note (the token expires after
  `AUTH_PASSWORD_RESET_EXPIRE_MINUTES`).
- A security note to ignore the message if the reset was not requested.

The request response is uniform whether or not an account exists, so the endpoint
never reveals which emails are registered. The token is stored only as a one-way
hash and is single-use. See `docs/AUTH_LIFECYCLE.md`.

## Invitation email

When an org admin creates an invitation
(`POST /api/v1/organizations/{id}/invitations`), the mailer sends an invitation
email built by `email_content.invitation_email`. The email contains:

- A concise subject naming the workspace.
- The role being offered.
- An accept link to `{APP_PUBLIC_BASE_URL}/invitations/accept?token=...`. The raw
  token appears only in this link.
- An expiration note (the invitation expires after `AUTH_INVITATION_EXPIRE_DAYS`).
- A boundary note that Civil Engineer AI is review-support tooling and a human
  reviewer remains responsible.

The invitation token is stored only as a one-way hash and cannot be reused once
accepted, revoked, or expired.

## Local testing

With `EMAIL_PROVIDER=noop` (the default), no email is sent. The reset and
invitation responses include a dev token outside production, so you can follow
the link locally. To exercise the SMTP path locally, run a local debugging SMTP
server (for example `python -m smtpd` style tools or a container) and set
`EMAIL_PROVIDER=smtp` with `EMAIL_SMTP_HOST=localhost` and the relevant port.

## Production requirements

Before onboarding real users:

- Set `EMAIL_PROVIDER=smtp` and the `EMAIL_SMTP_*` settings to a real SMTP
  service, and set `APP_PUBLIC_BASE_URL` to the deployed frontend origin.
- Keep `AUTH_EXPOSE_DEV_TOKENS` off (it is forced off in production regardless).
- Confirm a test reset and a test invitation are delivered.

## Tests

`backend/tests/test_email_delivery.py` covers the noop and SMTP providers (mocked
SMTP server), the safe handling of a delivery failure, that no secret or token is
logged, the email content builders, and that the reset and invitation flows send
through the mailer for an existing account while a non-existent account triggers
no send and the response stays uniform.
