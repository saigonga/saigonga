[← Back to the profile](https://github.com/saigonga)

# A developer?

How the scraper, the API and this profile are built

- **Web Scrapper** uses httpx for static pages and Playwright for JavaScript-heavy ones, then BeautifulSoup splits the page into sections, links, tables and metadata. CI runs on every push
- **finance-backend** is FastAPI with role-based access over JWT, SQLAlchemy models, Alembic migrations and Pydantic v2 validation
- **AI × BS Panel** signs people in with Google through NextAuth, runs Prisma on SQLite locally and Postgres when hosted, and only shows money views to money teams
- **TBM Studio** talks to the Meta Graph API with app-review-scoped permissions and keeps shortlists in Supabase
- **This profile** is Python-generated SVG. One Action rebuilds the changelog every morning, another runs the guestbook from issues. [Read the scripts](../scripts)

---

<sub>Other paths · [Hiring?](./hiring.md) · [Need something built?](./client.md) · [Sign the v3 release](https://github.com/saigonga#sign-the-release)</sub>
