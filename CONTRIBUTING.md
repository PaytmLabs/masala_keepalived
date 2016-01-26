## Contribution Guidelines

Please read and follow the below guidelines to contribute to this project.

This project makes use of [git-flow](https://github.com/nvie/gitflow).

### Contribution Workflow

1. Fork the repository on GitHub.
2. Clone your fork and change directory into it
3. Initialize git flow by running ```git flow init``` and accept the defaults for all prompts
4. Create a new feature branch for your changes:
     $ git flow feature start <name-of-feature>
5. Make any changes with the following guidelines:
  - Do not lump unrelated changes into the same feature branch
  - All commits should have a [well-written commit message explaining the change](http://chris.beams.io/posts/git-commit/)  
  - changes should include test coverage
6. Document your changes in the README or other appropriate location. Ensure any new attributes/recipes are added, and that the rest of the documentation still applies with the changes.
7. Ensure [your fork is in sync](https://help.github.com/articles/syncing-a-fork/) and [rebase your feature branch if needed](https://github.com/sevntu-checkstyle/sevntu.checkstyle/wiki/Development-workflow-with-Git:-Fork,-Branching,-Commits,-and-Pull-Request).
8. Run the test suite, ensure everything passes
9. Publish your feature branch:
     $ git flow feature publish <name-of-feature>
10. Submit a pull request on GitHub

#### Things NOT to do:
- Modify the version of the cookbook or gem.
- Update the CHANGELOG
- Make unnecessary changes to the metadata.rb/Berksfile

### Merge Workflow

1. Reviewing commits in the received pull request for:
  - documentation
  - tests are passing, coverage is there
  - good descriptive commit messages
2. Merge with the --no-ff switch, so that the merge is shown in the Git history
3. Do not use the Github merge button

### Release Workflow

1. Create the release line with git flow:
     $ git flow release start X.Y.Z
2. Create/update the changelog
3. Complete the release with git flow:
     $ git flow release finish X.Y.Z

### Post-Release Workflow

1. Increment version numbers to next in the develop line and commit

### Testing workflow

See: [TESTING.md](https://github.com/PaytmLabs/masala_keepalived/blob/develop/TESTING.md)

