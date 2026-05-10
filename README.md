# Kiro Token Generator

Automated tool to generate and refresh Kiro authentication tokens using Google OAuth.

## Installation

```bash
git clone git@github.com:Altairzx/Refresh-token-Kiro.git
cd Refresh-token-Kiro
pip install -r requirements.txt
```

## Usage

1. Create `accounts.txt` with your Google accounts (one per line):
```
email1@gmail.com:password1
email2@gmail.com:password2
```

2. Run the script:
```bash
python kiro_token_generator.py
```

3. Tokens will be saved to `kiro_tokens.json`:
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

## Features

- Automated Google OAuth login
- Multi-account support
- Headless browser automation using Camoufox
- Anti-detection measures
- Automatic retry on failures

## Requirements

- Python 3.8+
- camoufox
- browserforge
- aiohttp

## Security

Never commit these files:
- `accounts.txt` - Contains credentials
- `kiro_tokens.json` - Contains tokens
- `*.log` - Log files

These are already excluded in `.gitignore`.

## License

MIT License

## Author

Altairzx - https://github.com/Altairzx
