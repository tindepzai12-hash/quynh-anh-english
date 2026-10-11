# Quỳnh Anh English

Node.js web server, managed Supabase accounts and durable learning state.
The existing Python learning engine runs as a private serialized child process.
Deploy on Render **Free**, Node.js runtime. Build: `npm ci --omit=dev && python3 --version`. Start: `npm start`.
Set SESSION_SECRET (32+ chars), SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY privately on Render.
Run `node/schema.sql` in your Supabase SQL editor. No service key is exposed to the browser.
Configure Auth redirect allowlist for `/auth/callback` on the Render URL and localhost.
Enable Google/Facebook only after configuring real provider credentials in Supabase.

Original course videos/PDFs, personal progress, administrator keys, logs and Blender tools are excluded.
Without account configuration the online app is a read-only preview, never a fake saving session.
Course media remains on the laptop. Speaking recordings currently remain in browser IndexedDB.
The cloud service uses Node.js for HTTP/accounts/storage and Python for existing IELTS business logic.
Free services can sleep; free infrastructure is not a substitute for backups or an uptime guarantee.
