#!/usr/bin/env bash
#        git-helper — pure shell TUI         
#  deps: bash, git, fzf, tput, awk, sed, grep  

# How to run -> in git bash type -> bash ./scripts/git-helper.sh or just ./scripts/git-helper.sh

set -euo pipefail

# colours (tput) 
RESET=$(tput sgr0)
BOLD=$(tput bold)
DIM=$(tput dim 2>/dev/null || echo "")

BLACK=$(tput setaf 0)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)

BG_BLACK=$(tput setab 0)
BG_BLUE=$(tput setab 4)
BG_MAGENTA=$(tput setab 5)

COLS=$(tput cols)
LINES=$(tput lines)

# guards
check_deps() {
  for cmd in git fzf tput awk sed; do
    if ! command -v "$cmd" &>/dev/null; then
      echo "✗ Missing dependency: $cmd" >&2
      exit 1
    fi
  done
}

check_repo() {
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "\n  ${RED}✗  Not inside a Git repository.${RESET}\n"
    exit 1
  fi
}

# helpers
current_branch() { git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"; }
repo_root()      { git rev-parse --show-toplevel 2>/dev/null || echo "."; }
repo_name()      { basename "$(repo_root)"; }

hr() {
  # print a horizontal rule of given char (default ─)
  local char="${1:-─}"
  printf '%*s' "$COLS" '' | tr ' ' "$char"
}

header() {
  local branch; branch=$(current_branch)
  local repo;   repo=$(repo_name)
  clear
  echo "${BG_MAGENTA}${WHITE}${BOLD} ⎇  git-helper  ${RESET}${MAGENTA}${BOLD} repo: ${repo}  branch: ${branch} ${RESET}"
  echo "${DIM}$(hr)${RESET}"
}

pause() {
  echo ""
  echo -n "${DIM}  Press any key to continue...${RESET}"
  read -rsn1
}

confirm() {
  local msg="$1"
  echo -n "${YELLOW}  ${msg} [y/N]: ${RESET}"
  read -r ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

# fzf base options
FZF_OPTS=(
  --ansi
  --no-bold
  --layout=reverse
  --border=rounded
  --color="bg:#1e1e2e,bg+:#313244,fg:#cdd6f4,fg+:#cdd6f4,hl:#cba6f7,hl+:#cba6f7,border:#585b70,prompt:#cba6f7,pointer:#f5c2e7,marker:#a6e3a1,header:#89b4fa"
  --prompt="  "
  --pointer="▶"
  --marker="✓"
)

#  1. BRANCH SWITCHER

menu_branches() {
  while true; do
    header
    echo "${BOLD}${CYAN}  [ BRANCHES ]${RESET}"
    echo "${DIM}  enter=checkout  n=new  d=delete  m=merge  q=back${RESET}"
    echo ""

    local current; current=$(current_branch)

    # build display list: local branches
    local all_display=""
    while IFS= read -r b; do
      if [[ "$b" == "$current" ]]; then
        all_display+=$'\033[32m● '"$b"$' (current)\033[0m\n'
      else
        all_display+=$'\033[34m  '"$b"$'\033[0m\n'
      fi
    done < <(git branch --format='%(refname:short)' 2>/dev/null)

    # append remote-only branches
    while IFS= read -r rb; do
      local rname="${rb#origin/}"
      if ! git branch --format='%(refname:short)' 2>/dev/null | grep -qx "$rname"; then
        all_display+=$'\033[35m  '"$rb"$' (remote only)\033[0m\n'
      fi
    done < <(git branch -r --format='%(refname:short)' 2>/dev/null | grep -v HEAD)

    local picked=""
    local fzf_out=""
    fzf_out=$(printf '%s' "$all_display" | \
      fzf "${FZF_OPTS[@]}" \
        --header="  Enter=checkout  n=new  d=delete  m=merge  q=back" \
        --preview="echo {} | sed 's/\x1b\[[0-9;]*m//g;s/●//;s/(current)//;s/(remote only)//' | awk '{print \$1}' | xargs -I% git log --oneline --color=always --graph -15 % 2>/dev/null" \
        --preview-window="right:55%:wrap" \
        --expect="n,d,m,q,esc" \
        --print-query \
      2>/dev/null) || return 0

    local pressed_key picked
    pressed_key=$(echo "$fzf_out" | sed -n '2p')
    picked=$(echo "$fzf_out"      | sed -n '3p')

    # strip ansi and labels to get bare branch name
    local clean_picked
    clean_picked=$(printf '%s' "$picked" \
      | sed 's/\x1b\[[0-9;]*m//g' \
      | sed 's/●//;s/(current)//;s/(remote only)//' \
      | awk '{print $1}')

    # handle key presses first
    case "$pressed_key" in
      n) action_new_branch; continue ;;
      q|esc) return 0 ;;
      d)
        header
        local del_b=""
        del_b=$(git branch --format='%(refname:short)' 2>/dev/null | \
          fzf "${FZF_OPTS[@]}" --header="Select branch to DELETE" --no-preview 2>/dev/null) || true
        [[ -n "$del_b" ]] && action_delete_branch "$del_b"
        continue ;;
      m)
        header
        local mrg_b=""
        mrg_b=$(git branch --format='%(refname:short)' 2>/dev/null | \
          fzf "${FZF_OPTS[@]}" --header="Select branch to MERGE into $(current_branch)" --no-preview 2>/dev/null) || true
        [[ -n "$mrg_b" ]] && action_merge_branch "$mrg_b"
        continue ;;
    esac

    # handle branch selection (Enter)
    local clean_picked
    clean_picked=$(printf '%s' "$picked" \
      | sed 's/\x1b\[[0-9;]*m//g' \
      | sed 's/●//;s/(current)//;s/(remote only)//' \
      | awk '{print $1}')

    [[ -z "$clean_picked" || "$clean_picked" == "$(current_branch)" ]] && continue

    echo ""
    if [[ "$clean_picked" == origin/* ]]; then
      local localname="${clean_picked#origin/}"
      echo "  ${CYAN}Creating local '${localname}' from remote...${RESET}"
      if git checkout -b "$localname" "$clean_picked" 2>/tmp/git_err; then
        echo "  ${GREEN}✓ Created and switched to ${BOLD}${localname}${RESET}"
      else
        echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
      fi
    else
      if git checkout "$clean_picked" 2>/tmp/git_err; then
        echo "  ${GREEN}✓ Switched to ${BOLD}${clean_picked}${RESET}"
      else
        echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
      fi
    fi
    pause
  done
}

action_new_branch() {
  echo ""
  echo -n "  ${CYAN}New branch name: ${RESET}"
  read -r name
  [[ -z "$name" ]] && return
  if git checkout -b "$name" 2>/tmp/git_err; then
    echo "  ${GREEN}✓ Created and switched to ${BOLD}${name}${RESET}"
  else
    echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
  fi
  pause
}

action_delete_branch() {
  local branch="$1"
  echo ""
  confirm "Delete branch '${branch}'?" || return
  if git branch -d "$branch" 2>/tmp/git_err; then
    echo "  ${GREEN}✓ Deleted ${branch}${RESET}"
  else
    echo "  ${YELLOW}! Try force delete?${RESET}"
    confirm "Force delete (-D)?" && git branch -D "$branch" && \
      echo "  ${GREEN}✓ Force deleted ${branch}${RESET}" || \
      echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
  fi
  pause
}

action_merge_branch() {
  local branch="$1"
  local current; current=$(current_branch)
  echo ""
  confirm "Merge '${branch}' into '${current}'?" || return
  if git merge "$branch" 2>/tmp/git_err; then
    echo "  ${GREEN}✓ Merged ${branch} into ${current}${RESET}"
  else
    echo "  ${RED}✗ Merge conflict!${RESET}"
    echo "  $(cat /tmp/git_err)"
  fi
  pause
}

action_rename_branch() {
  local old="$1"
  echo ""
  echo -n "  ${CYAN}Rename '${old}' to: ${RESET}"
  read -r new
  [[ -z "$new" ]] && return
  if git branch -m "$old" "$new" 2>/tmp/git_err; then
    echo "  ${GREEN}✓ Renamed ${old} → ${new}${RESET}"
  else
    echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
  fi
  pause
}

#  2. COMMIT LOG VIEWER

menu_log() {
  while true; do
    header
    echo "${BOLD}${CYAN}  [ COMMIT LOG ]${RESET}"
    echo "${DIM}  enter=full diff  c=cherry-pick  r=revert  q=back${RESET}"
    echo ""

    local picked
    picked=$(git log --oneline --color=always --decorate --graph -80 | \
      fzf "${FZF_OPTS[@]}" \
        --no-sort \
        --preview="echo {} | grep -oP '^[* |\\\\/_-]*\K[0-9a-f]{6,}' | head -1 | xargs -I% git show --stat --color=always %" \
        --preview-window="right:55%:wrap" \
        --expect="c,r,q,esc" \
        --print-query \
      2>/dev/null) || return

    local key;  key=$(echo "$picked"  | sed -n '2p')
    local line; line=$(echo "$picked" | sed -n '3p')
    local hash; hash=$(echo "$line"   | grep -oP '^[* |\\/_-]*\K[0-9a-f]{6,}' | head -1)

    case "$key" in
      q|esc) return ;;
      c)
        [[ -z "$hash" ]] && continue
        confirm "Cherry-pick commit ${hash}?" || continue
        git cherry-pick "$hash" && echo "  ${GREEN}✓ Cherry-picked${RESET}" || \
          echo "  ${RED}✗ Cherry-pick failed${RESET}"
        pause ;;
      r)
        [[ -z "$hash" ]] && continue
        confirm "Revert commit ${hash}?" || continue
        git revert --no-edit "$hash" && echo "  ${GREEN}✓ Reverted${RESET}" || \
          echo "  ${RED}✗ Revert failed${RESET}"
        pause ;;
      *)
        [[ -z "$hash" ]] && continue
        clear
        echo "${BOLD}${CYAN}  Full diff: ${hash}${RESET}"
        echo "${DIM}$(hr)${RESET}"
        git show --color=always "$hash" | less -R
        ;;
    esac
  done
}

#  3. WORKING TREE STATUS

menu_status() {
  while true; do
    header
    echo "${BOLD}${CYAN}  [ STATUS ]${RESET}"
    echo "${DIM}  enter=diff  s=stage  u=unstage  a=stage all  x=discard  q=back${RESET}"
    echo ""

    # check if clean
    if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
      echo "  ${GREEN}${BOLD}✓ Working tree clean${RESET}"
      pause
      return
    fi

    local picked
    picked=$(git status --short | \
      awk '{
        code=substr($0,1,2); rest=substr($0,4)
        if (code ~ /M/)  print "\033[33m" code "\033[0m " rest
        else if (code ~ /A/) print "\033[32m" code "\033[0m " rest
        else if (code ~ /D/) print "\033[31m" code "\033[0m " rest
        else if (code ~ /\?/) print "\033[34m" code "\033[0m " rest
        else print "\033[37m" code "\033[0m " rest
      }' | \
      fzf "${FZF_OPTS[@]}" \
        --multi \
        --preview="f=\$(echo {} | awk '{print \$2}'); git diff --color=always HEAD -- \"\$f\" 2>/dev/null || git diff --color=always -- \"\$f\" 2>/dev/null || echo '(untracked — no diff)'" \
        --preview-window="right:60%:wrap" \
        --expect="s,u,a,x,q,esc" \
        --print-query \
      2>/dev/null) || return

    local key;   key=$(echo "$picked"   | sed -n '2p')
    local lines; lines=$(echo "$picked" | tail -n +3)
    local files; files=$(echo "$lines"  | awk '{print $2}' | tr '\n' ' ')

    case "$key" in
      q|esc) return ;;
      a)
        git add -A && echo "  ${GREEN}✓ Staged all changes${RESET}"
        pause ;;
      s)
        [[ -z "$files" ]] && continue
        # shellcheck disable=SC2086
        git add $files && echo "  ${GREEN}✓ Staged: ${files}${RESET}"
        pause ;;
      u)
        [[ -z "$files" ]] && continue
        # shellcheck disable=SC2086
        git restore --staged $files 2>/dev/null && echo "  ${YELLOW}↩ Unstaged: ${files}${RESET}"
        pause ;;
      x)
        [[ -z "$files" ]] && continue
        confirm "Discard changes in: ${files}?" || continue
        # shellcheck disable=SC2086
        git checkout -- $files 2>/dev/null || git restore $files 2>/dev/null
        echo "  ${RED}✗ Discarded: ${files}${RESET}"
        pause ;;

    *)
        [[ -z "$files" ]] && continue
        # local file; file=$(echo "$files" | awk '{print $1}')

        # # skip if it's the current directory or the running script itself
        # local self; self=$(basename "$0")
        # if [[ "$file" == "./" || "$file" == "." || "$file" == "$self" || "$file" == "./$self" ]]; then
        #   echo ""
        #   echo "  ${YELLOW}⚠ Cannot diff the running script itself.${RESET}"
        #   echo ""
        #   echo -n "${DIM}  Press any key...${RESET}"
        #   read -rsn1
        #   continue
        # fi

        local file; file=$(echo "$files" | awk '{print $1}')

        # skip running script itself
        local self; self=$(basename "$0")
        if [[ "$file" == "./" || "$file" == "." || "$file" == "$self" || "$file" == "./$self" ]]; then
          echo ""
          echo "  ${YELLOW}⚠ Cannot diff the running script itself.${RESET}"
          echo ""
          echo -n "${DIM}  Press any key...${RESET}"
          read -rsn1
          continue
        fi

        # if it's a folder — list changed files inside it
        if [[ -d "$file" ]]; then
          clear
          echo "${BOLD}${CYAN}  Folder: ${file}${RESET}"
          echo "${DIM}$(hr)${RESET}"
          echo ""
          echo "${YELLOW}  Changed files inside ${file}:${RESET}"
          echo ""
          git status --short "$file" | awk '{print "    " $0}'
          echo ""
          echo "${DIM}$(hr)${RESET}"
          echo -n "${DIM}  Press any key to go back...${RESET}"
          read -rsn1
          continue
        fi
        clear
        echo "${BOLD}${CYAN}  Diff: ${file}${RESET}"
        echo "${DIM}$(hr)${RESET}"
        echo ""

        local diff_out=""

        # try staged
        diff_out=$(git diff --cached --color=always -- "$file" 2>/dev/null)

        # try unstaged
        if [[ -z "$diff_out" ]]; then
          diff_out=$(git diff --color=always -- "$file" 2>/dev/null)
        fi

        # try HEAD
        if [[ -z "$diff_out" ]]; then
          diff_out=$(git diff --color=always HEAD -- "$file" 2>/dev/null)
        fi

        if [[ -n "$diff_out" ]]; then
          echo "$diff_out"
        elif [[ -f "$file" ]]; then
          echo "${YELLOW}  (untracked — raw content below)${RESET}"
          echo ""
          cat -n "$file"
        else
          echo "${RED}  Cannot show diff for: ${file}${RESET}"
        fi

        echo ""
        echo "${DIM}$(hr)${RESET}"
        echo -n "${DIM}  Press any key to go back...${RESET}"
        read -rsn1
        ;;
    esac
  done
}

#  4. STASH MANAGER

menu_stash() {
  while true; do
    header
    echo "${BOLD}${CYAN}  [ STASH ]${RESET}"
    echo "${DIM}  enter=diff  p=pop  a=apply  d=drop  n=new stash  q=back${RESET}"
    echo ""

    local stashes; stashes=$(git stash list 2>/dev/null)
    if [[ -z "$stashes" ]]; then
      echo "  ${DIM}(no stashes)${RESET}"
      echo ""
      echo -n "  ${CYAN}[n] create new stash  [q] back: ${RESET}"
      read -rsn1 key
      case "$key" in
        n) action_new_stash ;;
        *) return ;;
      esac
      continue
    fi

    local picked
    picked=$(echo "$stashes" | \
      awk '{
        idx=NR-1
        print "\033[33mstash@{" idx "}\033[0m " substr($0, index($0,$3))
      }' | \
      fzf "${FZF_OPTS[@]}" \
        --preview="i=\$(echo {} | grep -oP 'stash@\{\\K[0-9]+'); git stash show -p stash@{\$i} --color=always 2>/dev/null" \
        --preview-window="right:60%:wrap" \
        --expect="p,a,d,n,q,esc" \
        --print-query \
      2>/dev/null) || return

    local key;  key=$(echo "$picked"  | sed -n '2p')
    local line; line=$(echo "$picked" | sed -n '3p')
    local idx;  idx=$(echo "$line"    | grep -oP 'stash@\{\K[0-9]+')

    case "$key" in
      q|esc) return ;;
      n) action_new_stash ;;
      p)
        [[ -z "$idx" ]] && continue
        confirm "Pop stash@{${idx}}?" || continue
        git stash pop "stash@{${idx}}" && echo "  ${GREEN}✓ Popped stash@{${idx}}${RESET}" || \
          echo "  ${RED}✗ Pop failed${RESET}"
        pause ;;
      a)
        [[ -z "$idx" ]] && continue
        git stash apply "stash@{${idx}}" && echo "  ${GREEN}✓ Applied stash@{${idx}}${RESET}" || \
          echo "  ${RED}✗ Apply failed${RESET}"
        pause ;;
      d)
        [[ -z "$idx" ]] && continue
        confirm "Drop stash@{${idx}}?" || continue
        git stash drop "stash@{${idx}}" && echo "  ${YELLOW}↩ Dropped stash@{${idx}}${RESET}"
        pause ;;
      *)
        [[ -z "$idx" ]] && continue
        clear
        echo "${BOLD}${CYAN}  stash@{${idx}} full diff${RESET}"
        echo "${DIM}$(hr)${RESET}"
        git stash show -p "stash@{${idx}}" --color=always | less -R
        ;;
    esac
  done
}

action_new_stash() {
  echo ""
  echo -n "  ${CYAN}Stash message (optional): ${RESET}"
  read -r msg
  if [[ -n "$msg" ]]; then
    git stash push -m "$msg" && echo "  ${GREEN}✓ Stashed with message: ${msg}${RESET}"
  else
    git stash push && echo "  ${GREEN}✓ Stashed current changes${RESET}"
  fi
  pause
}

#  5. QUICK COMMIT

menu_commit() {
  header
  echo "${BOLD}${CYAN}  [ QUICK COMMIT ]${RESET}"
  echo ""

  local status; status=$(git status --short)
  if [[ -z "$status" ]]; then
    echo "  ${GREEN}✓ Nothing to commit${RESET}"
    pause; return
  fi

  echo "${YELLOW}  Staged files:${RESET}"
  git diff --cached --name-only | awk '{print "    " $0}'
  echo ""
  echo "${YELLOW}  Unstaged files:${RESET}"
  git diff --name-only | awk '{print "    " $0}'
  git ls-files --others --exclude-standard | awk '{print "    ?? " $0}'
  echo ""

  echo -n "  ${CYAN}Stage all and commit? [y/N]: ${RESET}"
  read -r stage
  if [[ "$stage" =~ ^[Yy]$ ]]; then
    git add -A
    echo "  ${GREEN}✓ Staged all${RESET}"
  fi

  echo -n "  ${CYAN}Commit message: ${RESET}"
  read -r msg
  [[ -z "$msg" ]] && { echo "  ${RED}✗ Aborted — empty message${RESET}"; pause; return; }

  if git commit -m "$msg" 2>/tmp/git_err; then
    echo ""
    echo "  ${GREEN}${BOLD}✓ Committed: ${msg}${RESET}"
    git log --oneline -1
  else
    echo "  ${RED}✗ $(cat /tmp/git_err)${RESET}"
  fi
  pause
}

#  MAIN MENU

main_menu() {
  while true; do
    header

    local branch; branch=$(current_branch)
    local ahead behind
    ahead=$(git rev-list --count "@{u}..HEAD" 2>/dev/null || echo "?")
    behind=$(git rev-list --count "HEAD..@{u}" 2>/dev/null || echo "?")
    local dirty; dirty=$(git status --short | wc -l | tr -d ' ')

    # repo summary
    echo ""
    printf "  ${BOLD}Branch:${RESET}  ${GREEN}%s${RESET}    " "$branch"
    printf "${BOLD}Ahead:${RESET} ${CYAN}%s${RESET}  " "$ahead"
    printf "${BOLD}Behind:${RESET} ${YELLOW}%s${RESET}  " "$behind"
    printf "${BOLD}Dirty:${RESET} ${RED}%s${RESET}\n" "$dirty"
    echo ""
    echo "${DIM}$(hr ─)${RESET}"
    echo ""

    local choice
    choice=$(printf '%s\n' \
        "  ⎇   Branches    — switch, create, delete, merge" \
        "  ◷   Log         — commit history, diff, cherry-pick" \
        "  ±   Status      — working tree, stage, unstage, discard" \
        "  ✦   Stash       — save, pop, apply, drop" \
        "  ✎   Commit      — quick stage & commit" \
        "  ✗   Quit" | \
        fzf "${FZF_OPTS[@]}" \
            --no-preview \
            --height=14 \
            --color="bg:#1e1e2e" \
            --header="${DIM}  Use ↑↓ arrows , Enter to select${RESET}" \
        2>/dev/null) || break

    case "$choice" in
      *Branches*)  menu_branches ;;
      *Log*)       menu_log      ;;
      *Status*)    menu_status   ;;
      *Stash*)     menu_stash    ;;
      *Commit*)    menu_commit   ;;
      *Quit*|"")   break         ;;
    esac
  done
}

# entry point
check_deps
check_repo
trap 'tput cnorm; clear' EXIT   # restore cursor on exit
tput civis                       # hide cursor
main_menu
clear
echo "${GREEN}  Bye! ⎇${RESET}"