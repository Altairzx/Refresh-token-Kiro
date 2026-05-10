# 🔑 Kiro Token Generator

Automated tool to generate and refresh Kiro authentication tokens using Google OAuth.

## 🚀 Features

- ✅ Automated Google OAuth login
- ✅ Multi-account support
- ✅ Token extraction and storage
- ✅ Headless browser automation (Camoufox)
- ✅ Anti-detection measures
- ✅ Bulk account processing

## 📦 Installation

```bash
# Clone repository
git clone git@github.com:Altairzx/Refresh-token-Kiro.git
cd Refresh-token-Kiro

# Install dependencies
pip install -r requirements.txt
```

## 🎯 Usage

### 1. Prepare Account List

Create `accounts.txt` with format:
```
email1@gmail.com:password1
email2@gmail.com:password2
```

### 2. Run Script

```bash
python kiro_token_generator.py
```

### 3. Output

Tokens will be saved to `kiro_tokens.json`:
```json
{
  "email@gmail.com": {
    "access_token": "...",
    "refresh_token": "...",
    "profile_arn": "...",
    "expires_in": 3600,
    "timestamp": 1234567890
  }
}
```

## ⚙️ Configuration

The script uses:
- **Camoufox** for anti-detection browsing
- **Headless mode** for server deployment
- **Automatic retry** on failures
- **10s delay** between accounts

## 📋 Requirements

- Python 3.8+
- camoufox
- browserforge
- aiohttp

## ⚠️ Important

- Keep `accounts.txt` and `kiro_tokens.json` **private**
- Never commit credentials to repository
- Use `.gitignore` to exclude sensitive files

## 🔐 Security

Files excluded from Git:
- `accounts.txt` - Account credentials
- `kiro_tokens.json` - Generated tokens
- `*.log` - Log files
- `.env` - Environment variables

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 👤 Author

**Altairzx**
- GitHub: [@Altairzx](https://github.com/Altairzx)

## 🙏 Acknowledgments

- Camoufox for anti-detection browser
- Kiro authentication system
