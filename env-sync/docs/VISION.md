# env-sync Vision

## The Problem

I work across two machines: a MacBook and a Windows Desktop running WSL/Ubuntu. The friction of switching between them is maddening.

When I leave my MacBook at the end of the day, I have:
- A carefully tuned shell environment with aliases, functions, and PATH tweaks
- API keys and secrets scattered across `.env` files in various projects
- Claude Code configured exactly how I like it - custom CLAUDE.md, skills, commands, settings
- Dotfiles that took years to refine (.gitconfig, .vimrc, etc.)
- A mental context of "where I was" in my work

When I sit down at my Desktop the next morning, I want to pick up exactly where I left off. Not "mostly" where I left off. Exactly.

But instead:
- My shell doesn't have that alias I added yesterday
- The API key I added for a new service isn't there
- My Claude Code settings are the old version
- I can't remember if I pushed that .env change or not
- I spend 20 minutes reconstructing context instead of working

This is the problem. The constant low-grade friction of maintaining two development environments that should be mirrors but aren't.

---

## What Makes This Hard

**Gitignored essentials are everywhere.** It's not just secrets - it's everything gitignored that's necessary for a project to actually work:

- **Secrets**: `.env`, `.env.local`, `.env.production`, `.npmrc` with tokens, `.pypirc`
- **Provider configs**: `.vercel/`, `.netlify/`, `.firebase/`, `.amplify/`
- **Cloud configs**: `.aws/`, `.gcloud/`, service account keys
- **Tool configs**: `.lsp.json`, IDE settings if gitignored
- **Auth states**: OAuth tokens, API credentials, session files

All of this is gitignored (correctly) - but it means I can't just `git clone` on a new machine and start working. I need all this context reconstructed. Currently that's manual: copy files, re-authenticate services, remember what was configured where. It's a tax on every machine switch.

**Shell configs are personal and messy.** My `.zshrc` sources my `.bash_aliases` which sources project-specific stuff. Some things are macOS-only (Homebrew paths). Some are WSL-only (Windows interop). Some are universal. Untangling "what should sync" from "what's machine-specific" is tedious.

**Claude Code lives in `~/.claude/`.** This isn't a project directory - it's global user config. It contains:
- `CLAUDE.md` - my carefully crafted global instructions
- `commands/` - custom slash commands I've built
- `skills/` - agent skills with supporting documentation
- `agents/` - custom subagent definitions
- `rules/` - modular rule files (break up CLAUDE.md into focused pieces with path filtering)
- `settings.json` - permissions, hooks (event handlers), model preferences, enabled plugins

None of this syncs anywhere by default. If I improve a skill on my MacBook, my Desktop doesn't know. If I add a useful slash command, I have to recreate it manually on the other machine.

There's also `~/.claude.json` which has OAuth tokens, MCP server configs, per-project trust settings, and preferences. This should sync too (encrypted) - sharing auth tokens saves re-authentication hassle, and MCP configs are definitely something I want consistent across machines.

The only truly transient thing is `~/.claude/plugins/cache/` - downloaded plugin files that regenerate automatically. Everything else I've configured should follow me.

**Projects live in different places.** On my MacBook: `~/cc-projects/muse-v1`. On my Desktop: `~/projects/muse/muse-v1`. Same project, different paths. Any sync system needs to understand this mapping.

**Some things MUST be machine-specific.** The path to Homebrew. The number of CPU cores for parallel builds. The location of Windows executables in WSL. These can't be blindly synced - they need to stay local.

**Merge conflicts are inevitable.** I edit `.zshrc` on my MacBook. I also edit it on my Desktop before syncing. Now what? Manual merge? Overwrite? This needs to be handled gracefully, not catastrophically.

**I don't want to think about it.** The whole point is to reduce friction, not add a new system I have to babysit. If the solution requires me to remember steps, run multiple commands, or maintain complex config, I'll stop using it. It needs to be: type command, enter password, done.

**The "instant redeploy" test.** If I got a new machine tomorrow, I should be able to: clone the sync repo, run pull, and have every project ready to work. Not "mostly ready" - actually ready. All the gitignored essentials reconstructed. All the auth in place. All the configs deployed. The only manual step should be re-cloning the actual project repos (which is just `git clone` commands). Everything else that makes those projects functional should come from the sync.

---

## What I Actually Want

**One command to push everything.** All my secrets, shell configs, Claude Code setup, dotfiles, provider configs, project gitignored essentials - encrypted and synced to git. I type `devenv push`, enter my encryption password, and walk away.

**One command to pull everything.** Sit down at the other machine, type `devenv pull`, enter password, and my environment is reconstructed. Secrets deployed to the right project `.env` files. Provider configs (`.vercel/`, etc.) in place. Shell config updated. Claude Code fully configured. Every project ready to run.

**Smart handling of conflicts.** When both machines have changes, don't just overwrite. Show me what's different. Let me choose. But make it easy - present options I can select with a keypress, not walls of text I have to parse.

**Machine-specific configs that stay local.** A shared bashrc with universal stuff. A machine-specific file that gets sourced for local tweaks. Clean separation, no conditionals scattered everywhere.

**Auto-discovery of projects.** I shouldn't have to register every project manually. Scan my project directories, find the git repos, track their gitignored essentials - `.env` files, provider configs, tool settings. When I create a new project or add a new service integration, pick it up automatically.

**Protection against mistakes.** If a project has `.claude/` in its gitignore, warn me - that breaks sync. If I'm about to overwrite local changes, tell me first. Fail loudly, not silently.

**History I can reference.** When I resolve a merge conflict, log it. When I come back months later trying to remember why something is configured a certain way, I can look at the history.

**Efficiency.** Don't scan my entire home directory every time. Track what's known, check what's changed, act on differences. Should take seconds, not minutes.

---

## The Complexity Trap

I've seen tools like this become monsters. What starts as "sync my dotfiles" becomes a sprawling system with plugins, hooks, templating engines, and a config file longer than my actual dotfiles.

I don't want that.

I want the minimum viable system that solves my actual problem. If it requires 500 lines of bash, fine. If it requires 5000 lines, something went wrong.

The test: Can I explain how it works to myself in 60 seconds? If not, it's too complex.

---

## Specific Scenarios

**Scenario 1: Add a new API key**
I sign up for a new service, get an API key, add it to `~/.env.secrets` on my MacBook. Run `devenv push`. Go to Desktop, run `devenv pull`. The key is there.

**Scenario 2: Update shell aliases**
I create a useful alias on my Desktop. Edit my shared bashrc. Run `devenv push`. Next time I'm on my MacBook, `devenv pull` brings it over.

**Scenario 3: New project**
I clone a new repo on my MacBook, create its `.env` with database credentials. Run `devenv push`. On Desktop, I clone the same repo (different path), run `devenv pull`. The `.env` appears in the right place.

**Scenario 4: Conflicting edits**
I edit `.zshrc` on both machines before syncing. When I `devenv pull`, it detects the conflict. I invoke the resolve helper. It shows me the diff, asks what I want to do for each difference. I pick options. It applies my decisions.

**Scenario 5: Machine-specific PATH**
My MacBook has Homebrew at `/opt/homebrew`. My Desktop has it at `/home/linuxbrew/.linuxbrew`. Each machine has a local bashrc snippet that sets the right PATH. This never syncs - it's machine-specific by design.

**Scenario 6: Claude Code skill improvement**
I improve a skill in `~/.claude/skills/` on my MacBook. Run `devenv push`. On Desktop, `devenv pull` updates the skill. My Claude Code sessions on both machines now have the improvement.

**Scenario 7: Custom bash utilities**
I build a significant utility function - maybe an integration with a tool I've built, or a complex workflow automation. It lives in my shell config (or a sourced file). These aren't trivial aliases; they're substantial pieces of functionality I rely on daily. When I refine or add to them on one machine, they need to sync. I shouldn't have to remember which machine has the latest version of my `deploy-to-staging` function.

**Scenario 8: Provider configs**
I deploy a project to Vercel. The `.vercel/` directory gets created with project linking, org settings, etc. This is gitignored. When I switch to my Desktop, I shouldn't have to re-link the project. The `.vercel/` config should already be there. Same for `.netlify/`, `.firebase/`, `.amplify/` - any provider-specific config that's gitignored but essential.

**Scenario 9: New machine setup**
I get a new laptop. I clone the sync repo, run `devenv pull`, enter my password. Within minutes: shell configured, all my Claude Code customizations in place, every project's gitignored essentials ready to deploy. I clone my project repos and immediately start working. No "setup day." No forgotten configs discovered weeks later.

---

## Non-Goals

- **Not a backup system.** This syncs between my machines. It's not for disaster recovery. (Though it does provide some backup-like benefits.)
- **Not a secrets manager for production.** I'm not trying to replace 1Password or AWS Secrets Manager for team/production secrets. This is for my personal development environment secrets.
- **Not a dotfiles framework.** I don't want templating, bootstrapping scripts, or complex OS detection. I have known machines. The setup is: clone repo, run pull, done.
- **Not cross-team.** This is for me. One person, multiple machines. No multi-user concerns.
- **Not syncing generated artifacts.** `node_modules/`, `dist/`, `build/`, `__pycache__/` - these regenerate. Only config and secrets, not build outputs.

---

## The Feeling I Want

Sitting down at either machine should feel identical. Not "similar" - identical. The same aliases work. The same secrets are available. The same Claude Code behavior. The environment is a mirror.

The sync itself should be invisible. A speed bump, not a roadblock. Type, authenticate, continue working.

When there are conflicts, the resolution should feel like a conversation, not a chore. "This changed on both machines. Which version do you want?" Click. Done.

And when I don't touch it for months, it should still work. No bit rot. No "oh that config format changed." No "that dependency is outdated." Simple, stable, boring.

That's the goal.
