# Test Links

This file contains links for testing the link checker.

- Valid: [GitHub](https://github.com/)
- Also Valid: https://www.google.com
- Redirect (Valid): http://httpbin.org/redirect-to?url=https://www.google.com (Should be OK)
- Broken: https://httpbin.org/status/404 (Should be BROKEN 404)
- Also Broken: http://sdfgsdfgsdfg.invalid/ (Should be ERROR ClientConnectorError or similar)
- Timeout (Simulated): We can't easily test a real timeout, but the code path is tested via unit tests.
- Error (Client): https://httpbin.org/status/403 (Should be BROKEN 403)
- Error (Server): https://httpbin.org/status/500 (Should be BROKEN 500)
 