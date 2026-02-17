# Push This Project to a New GitHub Repo

Follow these steps to put this project on GitHub.

## 1. Install Git (if needed)

- Download: [git-scm.com](https://git-scm.com/download/win)
- Install and restart your terminal. Check: `git --version`

## 2. Create the repo on GitHub (no local files yet)

1. Go to [github.com](https://github.com) and sign in.
2. Click **New repository** (or the **+** menu → New repository).
3. Set:
   - **Repository name**: e.g. `OPENBCICOMMUNICATION` or `openbci-ml-pipeline`
   - **Description**: e.g. "OpenBCI EEG/biosignal ML pipeline for SSVEP and robotics"
   - **Public** (or Private if you prefer).
   - **Do not** add a README, .gitignore, or license (this folder already has them).
4. Click **Create repository**.

## 3. Initialize Git and push from this folder

Open a terminal (PowerShell or Command Prompt) and run:

```powershell
cd "c:\Users\cants\OneDrive\Desktop\Hadimani Lab\OPENBCICOMMUNICATION"

git init
git add .
git commit -m "Initial commit: OpenBCI ML pipeline, config, docs"

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username and `YOUR_REPO_NAME` with the repo name you chose (e.g. `OPENBCICOMMUNICATION`).

Note: The project `.gitignore` excludes `*.csv` and `data/` so recordings and large outputs aren’t pushed. Add a small sample file with `git add -f path/to/sample.csv` if you want one in the repo.

If GitHub asks for auth, use a **Personal Access Token** as the password, or set up SSH keys and use the SSH URL:  
`git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git`

## 4. Done

Refresh the repo page on GitHub; you should see all project files there.
