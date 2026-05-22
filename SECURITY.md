# 🔒 Security Guidelines for GOOSE Project

## ⚠️ URGENT: Token Leak Remediation

**On May 21, 2026, a Telegram Bot Token was accidentally committed and pushed to the public GitHub repository.**

### Actions Taken to Fix:
- ✅ Revoked the compromised Telegram token via @BotFather
- ✅ Cleaned all repository history using `git filter-repo`
- ✅ Force-pushed clean history to GitHub
- ✅ Updated `.gitignore` to exclude configuration files
- ✅ Added template files for secure configuration
- ✅ Created this security guide

### What Was Exposed:
- **Telegram Bot Token**: `[REDACTED]` (REVOKED via @BotFather)
- **OpenClaw Pairing Code**: `[REDACTED]` (REVOKED)
- **Bot Name**: RG4YZClawRG4YZ_bot

### If You Cloned This Repository Before May 22, 2026:
1. **DO NOT USE** the Telegram token found in the history
2. The token has been revoked and will not work
3. Pull the latest changes: `git pull --rebase`
4. Follow the secure configuration instructions below

---

## 🔐 Secure Configuration Setup

### Telegram Bot Configuration

**NEVER commit actual tokens to Git!**

#### Option 1: Environment Variables (Recommended)

Create a `.env` file in `tool_gateway/`:

```bash
# tool_gateway/.env
TELEGRAM_BOT_TOKEN=your_actual_token_from_botfather
TELEGRAM_PAIRING_CODE=your_pairing_code
```

Add `.env` to `.gitignore` (already done).

#### Option 2: Local Configuration File

1. Copy the template:
```bash
cd tool_gateway/config
cp telegram_config.py.template telegram_config.py
```

2. Edit `telegram_config.py` with your actual tokens

3. **VERIFY** that `telegram_config.py` is in `.gitignore`

#### Option 3: Export Environment Variables

```bash
# In your shell startup file (.bashrc, .zshrc)
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_PAIRING_CODE="your_code_here"
```

---

## 🛡️ Security Best Practices

### ❌ Never Do:
- Commit actual tokens, passwords, or secrets to Git
- Push sensitive data to public repositories
- Store secrets in plain text files without `.gitignore`
- Use real tokens in documentation or examples

### ✅ Always Do:
- Use environment variables for secrets
- Create template files (`.template`) with placeholder values
- Add sensitive files to `.gitignore`
- Review changes before committing: `git diff --cached`
- Use `git-secrets` or `talisman` for pre-commit hooks

### Pre-Commit Hooks

Install `git-secrets` to prevent future leaks:

```bash
# Install git-secrets
git secrets --install

# Add common patterns
git secrets --add 'password.*='
git secrets --add 'token.*='
git secrets --add 'secret.*='
git secrets --add 'api[_-]?key.*='
git secrets --add '[a-zA-Z0-9]{30,}'
```

Or use `talisman`:
```bash
# Install talisman pre-commit hook
curl --silent https://raw.githubusercontent.com/thoughtworks/talisman/master/global_install_scripts/install.bash > /tmp/install_talisman.bash && /bin/bash /tmp/install_talisman.bash
```

---

## 🚨 What To Do If You Accidentally Commit a Secret

1. **REVOKE IMMEDIATELY** - Go to the service provider and revoke the token
2. **Remove from Git history**:
   ```bash
   # Install git-filter-repo
   pip install git-filter-repo
   
   # Replace the secret in history
   git filter-repo --force --replace-text <(echo "SECRET_VALUE==>REDACTED")
   ```
3. **Force push** (if already pushed):
   ```bash
   git push origin main --force
   ```
4. **Rotate all exposed credentials**
5. **Audit your repository**:
   ```bash
   # Search for potential secrets
   git grep -E "(token|secret|key|password|auth)" -- '*.py' '*.md' '*.json'
   ```

---

## 📋 Security Checklist for New Features

- [ ] No hardcoded secrets in code
- [ ] Sensitive files added to `.gitignore`
- [ ] Template files created for configuration
- [ ] Documentation uses placeholder values
- [ ] Pre-commit hooks installed
- [ ] Git history reviewed before push

---

## 🔍 Security Audit Commands

```bash
# Find potential secrets in repository
git grep -n -E "(token|Token|secret|Secret|key|Key|password|Password)" -- '*.py' '*.md' '*.json' '*.yaml'

# Search for long strings that might be tokens
git grep -n -E "[a-zA-Z0-9]{30,}" -- '*.py' '*.md' '*.json'

# Check what's about to be committed
git diff --cached

# View commit history with secret patterns
git log -p -S "YOUR_SECRET_VALUE_HERE"
```

---

## 📚 Additional Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [GitGuardian](https://www.gitguardian.com/)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitSecrets](https://github.com/awslabs/git-secrets)
- [Talisman](https://github.com/thoughtworks/talisman)

---

*Last updated: May 22, 2026*
*Maintained by: Lucas Tymen*
