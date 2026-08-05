---
name: catalog-page-count
description: Count pages in one or more PDF catalog files and report per-file and total page counts. Use whenever the user wants to know how many pages a catalog (or a batch of catalogs) has, asks for a "page count", wants catalogs compared or summarized by length, or hands over a folder/list of PDFs and asks something like "how many pages are in these", "count pages in these catalogs", or "what's the total page count across these files." Trigger this even if the user only pastes file paths or a directory without saying "count" explicitly.
---

# Catalog Page Count

Count pages in PDF catalog files and report a clear per-file and total summary.

## Workflow

1. **Find the PDF(s).** The user may give exact file paths, a directory, or describe catalogs loosely ("the ones in my downloads"). If they mention a folder without listing files, use Glob (e.g. `**/*.pdf`) to find PDF files in it before counting.
2. **Run the counting script** on all files at once:
   ```bash
   python3 .claude/skills/catalog-page-count/scripts/count_pages.py file1.pdf file2.pdf ...
   ```
   It prints a per-file page count, a total when more than one file is given, and warnings on stderr for anything it couldn't read (missing file, wrong extension, corrupt PDF).
3. **Report the result in chat** as the deliverable — this skill's output is a summary, not a new file. Mirror the script's numbers; don't recompute or round them.

## Output format

Default to a short markdown list or table, e.g.:

| Catalog | Pages |
|---|---|
| spring-2026-fasteners.pdf | 84 |
| spring-2026-hydraulics.pdf | 212 |
| **Total** | **296** |

For a single file, one line is enough: "spring-2026-fasteners.pdf has 84 pages."

## Notes

- Only PDFs are supported. If the user hands over a `.docx` or `.pptx` "catalog," say plainly that page count isn't well-defined for that format without rendering it, and ask whether they want slide/section count instead — don't guess a page number.
- The script prefers the `pypdf` library (installing it on first use if missing) for an exact count, and falls back to a direct scan of the PDF's page objects if `pypdf` can't be used in the environment. Fallback counts are marked `(estimated)` — mention that caveat to the user if it shows up, since it can undercount PDFs using compressed page trees.
- If a file can't be read at all (encrypted, corrupt, wrong extension), report that file's issue rather than silently dropping it from the total.
