<h1 align="center">Wizarr</h1>
<h3 align="center">The Free Media Invitation System</h3>

---


<p align="center">
<img src="https://raw.githubusercontent.com/Wizarrrr/wizarr/master/apps/wizarr-frontend/src/assets/img/wizard.png" height="200">
<br/>
<br/>
<a href="https://github.com/wizarrrr/wizarr/blob/master/LICENSE.md"><img alt="GPL 2.0 License" src="https://img.shields.io/github/license/wizarrrr/wizarr.svg"/></a>
<a href="https://github.com/wizarrrr/wizarr/releases"><img alt="Current Release" src="https://img.shields.io/github/release/wizarrrr/wizarr.svg"/></a>
<a href="https://features.wizarr.dev" style="text-decoration: none"><img alt="Submit Feature Requests" src="https://img.shields.io/badge/vote_now-features?label=features"/></a>
<a href="https://discord.gg/XXCz7aM3ak"><img alt="Chat on Discord" src="https://img.shields.io/discord/1020742926856372224"/></a>
<a href="https://www.reddit.com/r/wizarr"><img alt="Join our Subreddit" src="https://img.shields.io/badge/reddit-r%2Fwizarr-%23FF5700.svg"/></a>
<a href="https://github.com/Wizarrrr/wizarr/issues"><img alt="Github Issue" src="https://img.shields.io/github/issues/wizarrrr/wizarr"/></a>
<a href="https://github.com/Wizarrrr/wizarr/actions/workflows/master-beta-ci.yml"><img alt="Github Build" src="https://img.shields.io/github/actions/workflow/status/wizarrrr/wizarr/master-beta-ci.yml"/></a>
</p>

---

# WIZARR NOTICE

Wizzar is back in development! You can test the new beta using `ghcr.io/wizarrrr/wizarr:beta` as your image selection. We are working very hard to make Wizarr even better than before! :blush:

If you wish to stay up-to-date with our progress, make sure to join our [Discord](https://discord.gg/XXCz7aM3ak) server and check the `#releases` channel.

---

## What is Wizarr?

Wizarr is an automated user invitation system compatible with Plex, Jellyfin and Emby. You can create a unique link, share it with a user, and they will be invited to your Media Server after they complete the simple signup process!

## Major Features Include

-   Automatic Invitation System to your Media Server (Plex/Jellyfin/Emby)
-   Support for Passkey authentication for Admin Users
-   Create multiple invitations with different configurations
-   Make invitations and users expire after a certain amount of time
-   Automatically add users to your Requesting System (Jellyseerr/Overseerr)
-   Invite users to your Discord server through the onboarding process
-   Multi-Language Support
-   Multiple Admin Users with different permissions
-   API for Developers with Swagger UI
-   Light and Dark Mode Support
-   Session Management for Admin Users
-   Scheduled Tasks to keep Wizarr updated with your Media Server
-   Live logs directly from the Wizarr Web UI
  
## Major features to come in V4 will include

-   Customizable onboarding and branding
-   Added API Endpoints (already partially available)
-   Plex/Jellyfin/Emby granular user permissions/profiles
-   Discord invite request integration
-   Multi-Server Support
-   SMTP Support for notifications and user invites
-   OAuth Support with custom providers
-   2FA Support for Admin Users
-   Built in Update System
-   Plugin Store
-   and much more!

## Getting Started

You can install the stable version of Wizarr by following the instructions below.

```
docker run -d \
    --name wizarr \
    -p 5690:5690 \
    -v ./wizarr/database:/data/database \
    ghcr.io/wizarrrr/wizarr:latest
```

```
---
services:
  wizarr:
    container_name: wizarr
    image: ghcr.io/wizarrrr/wizarr:latest
    ports:
      - 5690:5690
    volumes:
      - ./wizarr/database:/data/database
```

## Documentation

Check out our documentation for instructions on how to install and run Wizarr!
[View Documentation](https://github.com/Wizarrrr/wizarr/blob/master/docs/setup/README.md).

If you encounter any issues please don't hesitate to visit our [Discord](https://discord.gg/XXCz7aM3ak) server and ask for help, we would be happy to help.

<a href="https://discord.gg/XXCz7aM3ak">
<img alt="Chat on Discord" src="https://img.shields.io/discord/1020742926856372224"/>
</a>


## ❤️ Support me

<!--
Pwease support me >.<
-->  

<p>Since I work full-time on open-source projects spread across my organizations, my only source of income is donations from people like you that use & appreciate my stuff. So, if you can spare a dollar or two, I would really appreciate that. All the money goes towards paying rent, essentials like food, drinks etc, and most importantly it will be used to fuel my cookie addiction🍪<br></p>

**Crypto:**
- **XMR**: `42xc4qPZyfi4wzAkCBXSoMSo3BLDS8946J89JXDqtT5gRj6uYpfhjQF12NLPMxtqGDL2RxoWXjB73iYdBP8DX7SqGvdbdtb`<br>
- **USDT (TRX20):** `TWg6VDUBase3HDA6RxAwTVjQw4SbxoGyqZ`<br>
- **USDT (ERC20):** `0x841251438A8Fb2B16298C15B10feA9Fd2cEA3405`<br>
- **Doge:** `DCKAFtgw6686uEMaFzZfCtUajS9VjPJLMm`<br>
- **BTC:** `bc1qje8qy7gpudm8hhyx43n9xndg7d8xj5f7dh6m4p`<br>

**Fiat:**
- **[Patreon](https://patreon.com/crazyco) (Fee: 8%\*)**: ❤️ Account needed, subscription with perks
- **[ko-fi](https://ko-fi.com/crazyco) (Fee: 2%\*)**: No account needed, subscription or one-time donation
- **[Wire-transfer](https://bunq.me/ClaraK) (Fee: 0%\*)**: No account needed, one-time donation
- **[Paypal](https://paypal.me/ClaraCrazy)\*\* (Fee: 2%\*)**: Account needed, one-time donation

\* Fee is calculated by how much I will lose when cashing out<br>
\*\* Please make sure to select *Friends and Family*<br><br>
**Thanks for all your support <3**
