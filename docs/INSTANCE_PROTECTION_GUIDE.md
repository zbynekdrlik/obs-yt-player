# Instance Protection Guide

## ⚠️ Problem: Git Deletes Instances When Switching Branches

Even though `yt-player-*/` is in `.gitignore`, Git may still delete your instances when:
- Switching branches
- Running `git clean`
- Checking out with `--force`
- If directories were tracked before being added to `.gitignore`

## ✅ Solution: Keep Instances Outside Repository

### 🆕 Default Behavior (v2.2.4+)

The simplified batch scripts now **automatically create instances in the parent directory**:

```cmd
create_new_ytplayer.bat worship
```

This creates instances **outside the repository by default** - no prompts needed!

### Recommended Directory Structure

```
C:\OBS-Scripts\
├── obs-yt-player\              # Git repository
│   ├── yt-player-main\         # Template only
│   ├── create_new_ytplayer.bat
│   └── update_all_instances.bat
│
├── yt-player-worship\          # Created automatically in parent!
├── yt-player-kids\             # Safe from git
├── yt-player-music\            # Git can't touch these
└── yt-player-ambient\          # Perfect!
```

### How to Set This Up

1. **Just run the script - it's safe by default:**
   ```cmd
   create_new_ytplayer.bat worship
   ```
   Creates in `../yt-player-worship` automatically!

2. **For custom locations (optional):**
   ```cmd
   create_new_ytplayer.bat kids /path:D:\OBS\Instances
   ```

3. **Move existing instances (if needed):**
   ```cmd
   move yt-player-worship ..\
   move yt-player-kids ..\
   ```

## 🛡️ Why This Is Safe

1. **Parent directory is default** - Git only controls the repository folder
2. **No prompts** - Can't accidentally choose wrong location
3. **Update script searches parent** - Finds instances automatically
4. **Complete isolation** - Instances are truly independent

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

1. **Use default behavior** - Just run `create_new_ytplayer.bat name`
2. **Update all instances** - Run `update_all_instances.bat`
3. **Never run `git clean -fd`** without checking what will be deleted

## 🚀 Quick Recovery

If you just lost instances:

1. **Recreate them instantly:**
   ```cmd
   create_new_ytplayer.bat worship
   ```
   No questions asked - created in parent directory!

2. **Reconfigure in OBS:**
   - Add the scripts from their new locations
   - Scenes and sources remain the same

3. **Re-download videos:**
   - Click "Sync Playlist Now" in each script
   - Videos will re-download to cache

## 📋 Safety Checklist

- [✅] **Default behavior is safe** - Parent directory by default
- [✅] **No accidental placement** - No prompts to mess up
- [✅] **Automatic search** - Update script finds instances
- [ ] `.gitignore` includes `yt-player-*/` (just in case)
- [ ] Regular backups of instance folders (good practice)

## 💡 Best Practices

1. **Use the defaults** - They're designed for safety
2. **Don't use `/repo` option** unless you really know why
3. **Let the scripts handle locations** - They know best
4. **Document custom locations** if you use `/path:`
5. **Test branch switches** after creating instances

## 🎯 Quick Reference

### Safe Commands (Default)
```cmd
# Create instance (parent directory)
create_new_ytplayer.bat worship

# Update all instances
update_all_instances.bat
```

### Advanced Commands (Use Carefully)
```cmd
# Create in repository (NOT RECOMMENDED)
create_new_ytplayer.bat test /repo

# Custom location
create_new_ytplayer.bat kids /path:D:\SafePlace

# Update with prompts (old behavior)
update_all_instances.bat /confirm
```

Remember: **The default is the safest option!** The scripts are designed to keep your instances safe from Git operations automatically.