# Social sign-in setup — Quỳnh Anh English

Existing portal: https://quynh-anh-english.onrender.com/#account/login and #account/signup. Both use Supabase Auth through the Node backend. Social sign-in creates an account on first consent and signs in on later visits. No separate password is needed. Disabled providers must remain disabled until configured.

## Two different callback addresses
1. Google/Meta application authorized redirect: `https://<actual-project-ref>.supabase.co/auth/v1/callback` (copy exact value from Supabase provider settings).
2. Supabase redirect allowlist for this Node app: `https://quynh-anh-english.onrender.com/auth/callback` and the same URL with the state query (use narrow `/auth/callback?state=*` pattern as supported by Supabase). Existing email recovery callback must remain allowed. Site URL: `https://quynh-anh-english.onrender.com`.

## Google
Google Cloud currently blocks this account until 2-step verification is enabled by the user. Then use an OAuth Web Application, actual app name/support email, Google consent configuration, approved origin `https://quynh-anh-english.onrender.com`, and the Supabase callback above. Store client ID/secret in Supabase Google provider settings, not frontend/GitHub. Only then set `GOOGLE_OAUTH_ENABLED=true` in Render. Request email/profile only; do not request Drive or Gmail access. Test first creation, later sign-in, cancellation and linking to an existing signed-in account.

## Facebook
Meta Developers is currently signed out. The user must log in. Use Facebook Login app configuration with valid OAuth redirect equal to the Supabase callback. Configure app domain, actual privacy policy and user data deletion instructions before making the app public; do not invent contact details or publish unsupported claims. Put App ID/secret in Supabase Facebook provider settings, then `FACEBOOK_OAUTH_ENABLED=true` on Render. Request public_profile/email only. Development-mode access is limited to app roles; verify with a normal account before calling public sign-in complete. No app credentials have been created yet.

## Verified code
Existing signed server session, compact cookie and PKCE verifier persistence. Added required fresh matching state for a started social flow, rejects missing/wrong/array/expired/future state and missing timestamp, preserves email confirmation callbacks without social state. Three local checks passed: two callback guard tests and existing PKCE round trip. Real Google/Facebook sign-in remains unverified until providers are configured.

Official configuration:
- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://supabase.com/docs/guides/auth/social-login/auth-facebook
- https://supabase.com/docs/guides/auth/redirect-urls

## Gemini images
570 per-card prompts queued. 12 October test: HTTP 429 RESOURCE_EXHAUSTED on FreeTier image token/minute, requests/minute and requests/day quotas. Zero images returned by this run. `qa/run_gemini_images.py --limit 1` loads the private local key; `--limit 20` is maximum reviewed batch size. Resume preserves statuses/attempts for unchanged vocabulary hashes; changed meanings invalidate prior status. Stop on quota/auth/model failures; do not enable billing automatically. Review actual images before publishing. The existing illustration fallback remains in use.
