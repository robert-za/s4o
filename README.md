## geolocation s4o

Copy `.env.example` -> `.env`

Generate `IPSTACK_API_KEY` and paste it under `IPSTACK_API_KEY` in .env.

GET, POST, DELETE @ localhost:8000/geolocation

There is a rate limit per IP Address of 100 per day (limit stored in .env)
Of course in current state it will be nullified when app is restarted as it does not use any cache service.

### Limitations, issues & ideas for improvement

Apparently IPStack does not handle `http://` and `https://` so I decided to limit the app to handle `www` format only.
It does not handle e.g. `www.zalando.pl/faq` so the app will also not recognize it. It certainly could be subject of further development.
There is certain unresolved issue, which is cloud services scaling. If URL is provided e.g. `www.mbank.pl`, the data
obtained from IPStack will be stored in the database. However if couple of minutes later we retry the same adress in IPStack
the IP can be different and there will be a discrepancy between local DB and IPStack service data. This would need to be handled too (update? / PATCH).

### TODOs
 - Malicious SQL injection protection/check

### Development
Before starting development run `make setup` - this will enable custom git hooks for commit and push for tests and linters

`make test` to run pytest tests inside docker container

Tech stack:
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- docker compose
