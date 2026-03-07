# SonarQube / SonarLint Setup for VS Code
### QuantumShell Team Guide

This guide walks you through connecting SonarLint in VS Code to the team's
SonarQube server running on `bane.tamucc.edu`. Once set up, SonarLint will
highlight code quality issues in real time as you code.

---

## Requirements

- **Visual Studio Code** installed on your machine
- **On campus** or connected to the **TAMU-CC network** (the SonarQube server
  is only accessible from the university network)
- A **GitHub account** that has been added to the project repo

---

## Step 1: Install the SonarLint Extension

1. Open VS Code
2. Open the Extensions panel with `Ctrl+Shift+X` (Windows/Linux) or `Cmd+Shift+X` (Mac)
3. Search for **SonarLint**
4. Click **Install** on the extension by SonarSource

---

## Step 2: Generate a Personal Token on SonarQube

1. Open a browser and go to: `http://bane.tamucc.edu:9000`
2. Log in with your credentials (ask the project lead if you don't have an account)
3. Click your profile icon in the top right corner
4. Go to **My Account → Security**
5. Under **Generate Tokens**, enter a name (e.g. your username) and click **Generate**
6. **Copy the token immediately** — you will not be able to see it again

---

## Step 3: Add SonarLint Configuration to VS Code

1. In VS Code open the Command Palette with `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
2. Type **Open User Settings (JSON)** and select it
3. Add the following inside the curly braces of your `settings.json`:

```jsonc
"sonarlint.connectedMode.connections.sonarqube": [
    {
        "connectionId": "bane-sonarqube",
        "serverUrl": "http://bane.tamucc.edu:9000",
        "token": "YOUR_TOKEN_HERE"
    }
]
```

Replace `YOUR_TOKEN_HERE` with the token you generated in Step 2.

Your full `settings.json` should look something like this:

```jsonc
{
    "workbench.colorTheme": "Solarized Dark",
    "sonarlint.connectedMode.connections.sonarqube": [
        {
            "connectionId": "bane-sonarqube",
            "serverUrl": "http://bane.tamucc.edu:9000",
            "token": "YOUR_TOKEN_HERE"
        }
    ]
}
```

4. Save the file with `Ctrl+S`

---

## Step 4: Bind the Project

After saving, VS Code may prompt you to bind the connection to the project.
If it does:

1. Click **Bind to a SonarQube project** when prompted
2. Select **bane-sonarqube** as the connection
3. Select **quantumshell** as the project

If you are not prompted automatically:

1. Open the Command Palette (`Ctrl+Shift+P`)
2. Type **SonarLint: Configure the binding of this folder** and select it
3. Follow the prompts to select the connection and project

---

## Step 5: Log in with GitHub (If Prompted)

SonarLint may ask you to log in with GitHub to verify your identity.
Go ahead and log in — this links your GitHub account to the SonarQube project.

---

## You're All Set!

SonarLint will now highlight code quality issues directly in your editor
as you type, using the same rules as the team's SonarQube server. Look for
colored underlines in your code — hovering over them will show the issue
and a suggested fix.

---

## Important Notes

- You must be **on campus or on the TAMU-CC network** for SonarLint to
  communicate with the SonarQube server. It will not work remotely.
- **Never share your personal token** — each team member should generate
  their own in Step 2.
- Automated scans also run on every push and pull request via GitHub Actions.
  Results are visible on the SonarQube dashboard at `http://bane.tamucc.edu:9000`.

---

## Troubleshooting

**SonarLint isn't showing any issues**
- Make sure you are on the TAMU-CC network
- Check that your token is correct in `settings.json`
- Try restarting VS Code after saving the settings

**Can't reach bane.tamucc.edu:9000**
- Confirm you are on campus or on the university network
- Try opening `http://bane.tamucc.edu:9000` in a browser to verify access

**Token is invalid or expired**
- Go back to Step 2 and generate a new token
- Replace the old token in your `settings.json`
