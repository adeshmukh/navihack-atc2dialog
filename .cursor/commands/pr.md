# Create GitHub Pull Request

Create a GitHub pull request from the current branch to the `main` branch.

## Pre-flight Checks

1. **Check for uncommitted or untracked changes:**
   - If uncommitted/untracked changes are detected:
     - Inform the user and list the files with changes
     - Ask for explicit confirmation before proceeding
     - Do NOT proceed until the user explicitly confirms

2. **Verify gh CLI availability:**
   - If `gh` is not available, inform the user and stop

3. **Verify branch:**
   - Ensure current branch is not `main` (cannot create PR from main to main)
   - Ensure branch is pushed to remote repository

## Creating the Pull Request

1. **Prepare PR description:**
   - Use the template from `.github/pull_request_template.md`
   - Prompt the user to provide content for each section in the template

2. **Create the PR:**
   - Use the `gh` CLI to create the pull request targeting `main` branch
   - PR title should be a concise summary (ask user or infer from branch name)
   - Prefix the PR title with a Conventional Commits tag such as `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`, `ci:`, `build:`, or `style:`
   - PR description should follow the template structure

3. **Handle failures:**
   - If creation fails, display error and suggest solutions (e.g., push branch first)
   - On success, display the PR URL

## Notes

- Verify all changes are committed before creating the PR
- Ensure branch is pushed to remote before creating the PR
- The `gh` CLI must be authenticated
