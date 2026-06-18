# 02 – UI Layout & Navigation Plan

## General Page Structure

All pages share the same layout through `templates/base.html` — a navigation
bar at the top and the main content area below.

```
┌─────────────────────────────────────────────────────────────────┐
│  NAVIGATION BAR                                                 │
│  NewsApp  |  Articles  |  Newsletters  |  [Role Badge] username │
│                                         |  Logout               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    MAIN PAGE CONTENT                            │
│                    (changes per page)                           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  FOOTER (optional)                                              │
└─────────────────────────────────────────────────────────────────┘
```

The navigation bar adapts based on the user's role:

| User state | Nav items shown |
|------------|-----------------|
| **Guest** | Articles, Newsletters, Login, Register |
| **Reader** | Articles, Newsletters, `[Reader]` username, Logout |
| **Journalist** | Articles, Newsletters, My Dashboard, `[Journalist]` username, Logout |
| **Editor** | Articles, Newsletters, Review Queue, `[Editor]` username, Logout |
| **Admin** | All of the above + Admin Panel link |

The **role badge** (`[Reader]`, `[Journalist]`, `[Editor]`) is always visible
next to the username when logged in.

Flash messages (Django `messages` framework) appear directly below the nav bar
and dismiss automatically. They confirm create/edit/delete/subscribe actions
without navigating the user away from their current context.

---

## Page Layouts

### Article List (Home) — `/`

The landing page for all users. Displays all approved articles in a card grid,
paginated. Readers see a "Subscribe to Journalist" button on each card.

```
┌──────────────────────────────────────────────────────┐
│  ALL ARTICLES                          [Search/Filter] │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  [image]    │  │  [image]    │  │  [image]    │  │
│  │  Title      │  │  Title      │  │  Title      │  │
│  │  Author     │  │  Author     │  │  Author     │  │
│  │  Publisher  │  │  Publisher  │  │  Publisher  │  │
│  │  Date       │  │  Date       │  │  Date       │  │
│  │  [Read →]   │  │  [Read →]   │  │  [Read →]   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                       │
│               [← Prev]  1 2 3  [Next →]               │
└──────────────────────────────────────────────────────┘
```

### Article Detail — `/articles/<id>/`

Shows the full article. The "Back to Articles" link returns the reader to the
list without losing pagination context (continuous browsing).

```
┌────────────────────────────────────────────────────┐
│  [ ← Back to Articles ]                            │
│                                                    │
│  Article Title                                     │
│  By: Journalist Name  |  Publisher: Daily News     │
│  Published: 2026-05-30                             │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  [Article Image]                             │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Article content paragraph...                      │
│  More content...                                   │
│                                                    │
│  ── ABOUT THE AUTHOR ──────────────────────────    │
│  Journalist Name  [Subscribe to Journalist]  ←Reader only
│                                                    │
│  ── PART OF PUBLISHER ─────────────────────────    │
│  Daily News  [Subscribe to Publisher]  ←Reader only│
└────────────────────────────────────────────────────┘
```

Editors see **[Edit]** and **[Delete]** buttons. Journalists see them on their
own articles only.

### Editor Queue — `/editor/queue/`

Only accessible to Editors. Lists all unapproved articles ordered by
submission date (oldest first).

```
┌────────────────────────────────────────────────────┐
│  EDITOR REVIEW QUEUE  (5 pending)                  │
│                                                    │
│  Title                  Author        Submitted    │
│  ─────────────────────────────────────────────     │
│  "AI in Medicine"       j.smith       2026-05-28   │
│  [Preview] [✓ Approve] [✗ Reject]                  │
│                                                    │
│  "Climate Update"       a.jones       2026-05-29   │
│  [Preview] [✓ Approve] [✗ Reject]                  │
│                                                    │
│  "Space Mission 2027"   b.lee         2026-05-30   │
│  [Preview] [✓ Approve] [✗ Reject]                  │
└────────────────────────────────────────────────────┘
```

### Article Create / Edit Form — `/articles/create/` and `/articles/<id>/edit/`

Accessible to Journalists (create & own articles) and Editors (edit any).

```
┌────────────────────────────────────────────────────┐
│  CREATE NEW ARTICLE                                │
│                                                    │
│  Title: [ _________________________________ ]      │
│                                                    │
│  Publisher (optional): [ Dropdown ▼ ]              │
│                                                    │
│  Content:                                          │
│  ┌──────────────────────────────────────────────┐  │
│  │                                              │  │
│  │  (textarea)                                  │  │
│  │                                              │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Image (optional): [ Choose File ]                 │
│                                                    │
│  [ Save Draft ]                                    │
└────────────────────────────────────────────────────┘
```

### Journalist Dashboard — `/journalist/dashboard/`

Visible only to the logged-in Journalist.

```
┌────────────────────────────────────────────────────┐
│  MY DASHBOARD                                      │
│                                                    │
│  MY ARTICLES                        [+ New Article] │
│  ─────────────────────────────────────────────     │
│  "AI in Medicine"    ● Pending Approval  [Edit]    │
│  "Last Year Review"  ✓ Approved          [Edit]    │
│                                                    │
│  MY NEWSLETTERS                  [+ New Newsletter] │
│  ─────────────────────────────────────────────     │
│  "Tech Weekly #12"   3 articles  [View] [Edit]     │
└────────────────────────────────────────────────────┘
```

### Newsletter List — `/newsletters/`

```
┌────────────────────────────────────────────────────┐
│  NEWSLETTERS                                       │
│                                                    │
│  Tech Weekly #12  — by j.smith  — 3 articles       │
│  [Read →]                                          │
│                                                    │
│  Climate Digest   — by a.jones  — 5 articles       │
│  [Read →]                                          │
└────────────────────────────────────────────────────┘
```

### Newsletter Detail — `/newsletters/<id>/`

```
┌────────────────────────────────────────────────────┐
│  Tech Weekly #12                                   │
│  By: j.smith  |  Created: 2026-05-20               │
│                                                    │
│  Description: A curated collection of...           │
│                                                    │
│  ARTICLES IN THIS NEWSLETTER                       │
│  ─────────────────────────────────────────────     │
│  "AI in Medicine"   j.smith   2026-05-20  [Read →] │
│  "Robot Ethics"     j.smith   2026-05-15  [Read →] │
│                                                    │
│  [ ← Back to Newsletters ]                         │
└────────────────────────────────────────────────────┘
```

### Publisher Profile — `/publishers/<id>/`

```
┌────────────────────────────────────────────────────┐
│  [Logo]  Daily News                                │
│  daily-news.example.com                            │
│                                                    │
│  A description of the publisher...                 │
│                                                    │
│  [Subscribe to Daily News]  ← Reader only          │
│                                                    │
│  LATEST ARTICLES                                   │
│  ─────────────────────────────────────────────     │
│  "Climate Update"  a.jones  2026-05-29  [Read →]   │
└────────────────────────────────────────────────────┘
```

### Registration — `/register/`

Single form for all roles — no separate pages per role.

```
┌────────────────────────────────────────────────────┐
│  CREATE ACCOUNT                                    │
│                                                    │
│  Username:  [ __________________________ ]         │
│  Email:     [ __________________________ ]         │
│  Role:      [ Reader           ▼ ]                 │
│  Password:  [ __________________________ ]         │
│  Confirm:   [ __________________________ ]         │
│                                                    │
│  [ Register ]                                      │
│                                                    │
│  Already have an account? Login →                  │
└────────────────────────────────────────────────────┘
```

### Password Reset Form — `/password-reset/`

Includes a visible submit button.

```
┌────────────────────────────────────────────────────┐
│  RESET YOUR PASSWORD                               │
│                                                    │
│  Email: [ _____________________________________ ]  │
│                                                    │
│  [ Send Reset Link ]                               │
└────────────────────────────────────────────────────┘
```
