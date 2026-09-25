# Security

Lumina accepts declarative image operations over a local HTTP boundary. It does not execute agent-supplied Python, shell commands, or file paths.

Keep the default bind address on localhost. If exposing the API to a network, place it behind authentication, TLS, rate limits, and a request-size-enforcing reverse proxy. Configure provider keys through environment variables and never commit `.env`.

Report security issues privately to the repository owner rather than opening a public issue containing exploit details or credentials.
