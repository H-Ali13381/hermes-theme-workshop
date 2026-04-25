# Shell & Prompt Theming

Shell theming completes a rice — unthemed prompts break visual coherence.

## Starship (recommended, cross-shell)

Install:
```bash
curl -sS https://starship.rs/install.sh | sh
```

Config: `~/.config/starship.toml`
Activate in `.zshrc` or `.bashrc`:
```bash
eval "$(starship init zsh)"
```

### Palette-Aware Configuration

```toml
[character]
success_symbol = "[➜](bold #7ad4f0)"    # primary
error_symbol   = "[✗](bold #cc3090)"    # danger

[directory]
style = "#d4a012 bold"                   # accent
truncation_length = 3

[git_branch]
symbol = " "
style  = "#2a8060"                       # success

[git_status]
style = "#c87820"                        # warning

[cmd_duration]
style = "#3d2214"                        # muted
min_time = 2000

[hostname]
style = "#0d2e32 bold"                   # secondary

[username]
style_user = "#e4f0ff bold"              # foreground
```

Map: `primary` → character success, `danger` → error, `accent` → directory, `success` → git_branch.

---

## Powerlevel10k (zsh only)

Install via oh-my-zsh or manual clone. Run `p10k configure` for wizard.

Config: `~/.p10k.zsh` — edit color entries directly with palette hex values:

```zsh
# In ~/.p10k.zsh, find and replace color values:
typeset -g POWERLEVEL9K_DIR_FOREGROUND='#d4a012'
typeset -g POWERLEVEL9K_VCS_CLEAN_FOREGROUND='#2a8060'
typeset -g POWERLEVEL9K_VCS_MODIFIED_FOREGROUND='#c87820'
typeset -g POWERLEVEL9K_STATUS_OK_FOREGROUND='#2a8060'
typeset -g POWERLEVEL9K_STATUS_ERROR_FOREGROUND='#cc3090'
```

---

## fzf Integration

Add to `.zshrc` or `.bashrc`:

```bash
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
export FZF_DEFAULT_OPTS="\
  --color=fg:#e4f0ff,bg:#0c1220,hl:#d4a012 \
  --color=fg+:#e4f0ff,bg+:#1c1e2a,hl+:#7ad4f0 \
  --color=info:#2a8060,prompt:#7ad4f0,pointer:#cc3090 \
  --color=marker:#d4a012,spinner:#0d2e32,header:#3d2214 \
  --border"
```

Replace hex values with your palette's actual colors. Maps:
- `fg/bg` → foreground/background
- `hl` → accent (highlighted match)
- `bg+` → surface (selected line)
- `prompt` → primary
- `pointer` → danger
- `info` → success

---

## zsh Plugins

Recommended plugins (inherit terminal colors automatically):

| Plugin | Purpose |
|--------|---------|
| `zsh-autosuggestions` | Ghost text completions |
| `zsh-syntax-highlighting` | Live syntax colors |
| `zsh-history-substring-search` | Up/down searches history |

Install via zinit, antigen, or oh-my-zsh. No additional theming needed — they inherit terminal ANSI colors.

### zinit Example

```zsh
# In ~/.zshrc
zinit light zsh-users/zsh-autosuggestions
zinit light zsh-users/zsh-syntax-highlighting
zinit light zsh-users/zsh-history-substring-search
```

### Autosuggestions Color Override

If the default ghost text color clashes with your palette:

```zsh
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#3d2214"  # muted color
```
