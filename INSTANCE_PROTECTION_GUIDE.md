# Instance Protection Guide

## ⚠️ Problem: Git Deletes Instances When Switching Branches

Even though `yt-player-*/` is in `.gitignore`, Git may still delete your instances when:
- Switching branches
- Running `git clean`
- Checking out with `--force`
- If directories were tracked before being added to `.gitignore`

## ✅ Solution: Keep Instances Outside Repository

### Recommended Directory Structure

```
C:\OBS-Scripts\
├── obs-yt-player\              # Git repository
│   ├── yt-player-main\         # Template only
│   ├── create_new_ytplayer.bat
│   └── update_all_instances.bat
│
└── yt-player-instances\        # Outside git (safe!)
    ├── yt-player-worship\
    ├── yt-player-kids\
    ├── yt-player-music\
    └── yt-player-ambient\
```

### How to Set This Up

1. **Create instances directory outside repository:**
   ```cmd
   cd ..
   mkdir yt-player-instances
   cd yt-player-instances
   ```

2. **Use the instance creator with location choice:**
   ```cmd
   ..\obs-yt-player\create_new_ytplayer.bat worship
   ```
   Choose option 2 or 3 to create outside repository.

3. **Move existing instances (if any survived):**
   ```cmd
   move yt-player-worship ..\yt-player-instances\
   move yt-player-kids ..\yt-player-instances\
   ```

## 🔧 Alternative Solutions

### Option 1: Git Stash Method
Before switching branches:
```cmd
git add yt-player-* -f
git stash push -m "Save instances" -- yt-player-*
git checkout <branch>
git stash pop
```

### Option 2: Exclude from Git Operations
```cmd
git update-index --skip-worktree yt-player-worship/
git update-index --skip-worktree yt-player-kids/
```

### Option 3: Use Symbolic Links
Keep instances elsewhere and link them:
```cmd
mklink /D yt-player-worship C:\yt-instances\yt-player-worship
```

## 📝 Safe Workflow

1. **Always create instances outside the repository** (choose option 2 or 3 in the creator)
2. **Use `update_all_instances.bat` which searches multiple locations**
3. **Never run `git clean -fd` without checking what will be deleted**

## 🚀 Quick Recovery

If you just lost instances:

1. **Recreate them quickly:**
   ```cmd
   create_new_ytplayer.bat worship
   ```
   Choose option 2 to create in parent directory.

2. **Reconfigure in OBS:**
   - Add the scripts from their new locations
   - Scenes and sources remain the same

3. **Re-download videos:**
   - Click "Sync Playlist Now" in each script
   - Videos will re-download to cache

## 🛡️ Permanent Protection

### Add to your Git config:
```
[alias]
    safe-checkout = checkout
    safe-clean = clean -fd --exclude=yt-player-*
```

### Create `.git/info/exclude` (local only):
```
yt-player-*/
```

## 📋 Checklist for Safety

- [ ] Instances stored outside repository
- [ ] Using location choice when creating instances
- [ ] `.gitignore` includes `yt-player-*/`
- [ ] Never use `git clean -fd` without checking
- [ ] Regular backups of instance folders

## 💡 Best Practices

1. **Template in repo, instances outside**
2. **Use version control only for template code**
3. **Document instance locations**
4. **Backup instance configurations**
5. **Test branch switches in safe environment first**

Remember: The safest instance is one that Git doesn't know about!