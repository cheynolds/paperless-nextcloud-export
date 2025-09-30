# Contributing to Paperless → Nextcloud Export

Thanks for your interest in contributing!  

This project is intended to make it easy to route documents from Paperless-ngx into Nextcloud via WebDAV. Contributions of all kinds are welcome.

---

## How to Contribute

### Reporting Issues
- Use the GitHub Issues tab to report bugs or request features.
- Include as much detail as possible:
  - Paperless-ngx version
  - Nextcloud version
  - Logs or error messages
  - Steps to reproduce

### Suggesting Enhancements
- Open an Issue labeled `enhancement`.
- Explain what problem the new feature solves.
- If possible, suggest a rough idea of implementation.

### Submitting Code
1. Fork the repository and clone it locally.
2. Create a new branch for your work:

   git checkout -b feature/my-new-feature

3. Make changes, following these guidelines:
- Keep code style consistent with the existing scripts.
- Document changes with comments/docstrings.
- Test on your own Paperless + Nextcloud setup.

4. Commit your changes:

   git commit -m "Add: short description of change"

5. Push your branch and open a Pull Request.

---

## Project Structure

- `scripts/` – Main Python export script(s).
- `examples/` – Example routing configs and Unraid helper scripts.
- `export.sh` – Portable entrypoint script.
- `.env.example` – Environment variable template.
- `README.md` – Usage documentation.

---

## Development Notes

- Paperless-ngx requires **Tika** and **Gotenberg** containers for parsing.
- Nextcloud must have **WebDAV** enabled (`remote.php/dav/files/<username>/`).
- Test your `.env` and `routing.json` locally before opening PRs.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
