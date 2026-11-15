# Exit tickets and feedback (anonymous, stored on GitHub)

Students scan the QR code on the exit-ticket slide and open
`teaching/2105603/slides-2027/exit.html?s=<session>`. The page posts the answers
to a Cloudflare Worker (`worker.js`). The Worker holds a GitHub token and saves
each response as one JSON file in a private repository:

    responses/2105603/s01/2026-11-15-1a2b3c4d.json

No name, student ID, e-mail or IP address is stored. The page and the Worker
both accept only these answers: session, in class or on my own, exit ticket,
pace, confidence 1-5, lab worked, still unclear, one change.

## One-time setup

1. Create a private repository, for example `soorathep/course-feedback`.
2. Create a fine-grained GitHub token for that repository only, permission
   "Contents: Read and write".
3. In Cloudflare (free plan), create a Worker, paste `worker.js`, deploy.
   Under Settings > Variables add `REPO` = `soorathep/course-feedback` and the
   secret `GITHUB_TOKEN`.
4. Put the Worker address in `RELAY_URL` at the bottom of `exit.html`, render
   and publish.

## Current deployment

- Repository: `soorathep/course-feedback` (private)
- Worker: `https://course-feedback-relay.ecs-thailand-election.workers.dev/`
  (Cloudflare account soorathep.k; token expires about November 2027)

## Reading the answers

Clone the private repository, then run `python3 collect.py` inside it (copy the
script there once). It writes one CSV per session under `summary/`, readable in
Excel with Thai text intact.
