# Git Workflow Guide

This document outlines our Git workflow to ensure proper tracking of project progress, maintain backups of previous versions, and avoid losing time with changes that break the application.

## Branch Structure

- **main**: Production-ready code. Protected branch requiring pull request reviews.
- **feature/[feature-name]**: For developing new features.
- **fix/[issue-description]**: For bug fixes.
- **release/v[X.Y.Z]**: For preparing releases.

## Workflow Steps

### Starting New Work

1. Always start from an updated main branch:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Create a new branch for your feature or fix:
   ```bash
   # For features
   git checkout -b feature/your-feature-name
   
   # For bug fixes
   git checkout -b fix/issue-description
   ```

### Working on Your Branch

3. Make small, frequent commits that represent complete units of work:
   ```bash
   git add [files]
   git commit -m "type(scope): descriptive message"
   ```

4. Push your branch to remote regularly to create backups:
   ```bash
   git push origin [your-branch-name]
   ```

5. If main has advanced while you're working, keep your branch updated:
   ```bash
   git checkout main
   git pull origin main
   git checkout [your-branch-name]
   git merge main
   # Resolve any conflicts
   ```

### Completing Your Work

6. Before submitting a pull request:
   - Ensure all tests pass
   - Check that the application runs correctly
   - Verify your changes meet requirements

7. Create a pull request on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Link to any related issues

8. After code review and approval, merge using "Squash and merge" option.

## Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code changes that neither fix bugs nor add features
- **test**: Adding or fixing tests
- **chore**: Changes to build process, dependencies, etc.

**Example:**
```
feat(api): implement file upload endpoint

- Add file validation
- Store file metadata
- Generate vector embeddings

Closes #123
```

## Emergency Procedures

### If a Breaking Change is Pushed to Main

1. **Identify the Issue**: Determine which commit introduced the problem.

2. **Create a Fix Branch**:
   ```bash
   git checkout -b fix/urgent-main-fix
   ```

3. **Fix the Issue**: Make the minimal necessary changes to resolve the problem.

4. **Or Revert if Necessary**:
   ```bash
   git revert [commit-hash]
   ```

5. **Push and Create Emergency PR**:
   ```bash
   git push origin fix/urgent-main-fix
   ```

6. **After Fix is Merged**: Analyze what went wrong in the process and adjust procedures to prevent similar issues.

## Best Practices

1. **Never Force Push to Main**: This can cause loss of history and break others' work.

2. **Keep Commits Atomic**: Each commit should represent a single logical change.

3. **Write Meaningful Commit Messages**: Future you and others will thank you.

4. **Branch Often**: Branches are cheap in Git; use them liberally.

5. **Delete Branches After Merging**: Keep the repository clean.

6. **Backup Local Work**: Push to remote frequently to avoid losing work.

By following this workflow, we ensure that:
- Project progress is precisely tracked
- We have backups of all previous versions
- Breaking changes are caught before they impact the main branch
- The development process is transparent and collaborative 