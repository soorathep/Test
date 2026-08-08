# SKH Maintenance Dashboard

Double-click **`Open SKH Dashboard.command`** at the repository root. It checks
the site, writes a private report to `.maintenance/dashboard.html`, and opens the
report in the default browser.

The generated `.maintenance/` directory is ignored by Git and is never included
in the Jekyll site. External-link results are cached for seven days. A `blocked`
result means that a site rejected the automated check; it does not necessarily
mean that the link is broken.

For an offline diagnostic run:

```bash
python3 tools/maintenance/build_dashboard.py --skip-links
```

