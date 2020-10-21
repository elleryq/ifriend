# iFriend


- 請實作一個簡易的交友網站，分別具有以下功能:
  - 有一個註冊頁面 User 需要填寫email/password，以完成註冊流程。
  - 有一個登入頁面 User可以輸入email & password登入。
  - 當User登入後可以查看並編輯自己的Profile頁面，Profile頁面至少包含以下內容:
    - 生活照一張
    - 使用者名稱
    - 姓名
    - 自我介紹
    - 興趣
  - 有一個User列表頁，可以看到所有User  清單
  - 點擊列表中的項目,可以看到該User的profile頁面
  - 可以顯示自己的profile頁被誰看過(自己看過不算)
- 以下列出的四種網站安全機制請選擇其中兩種，在不使用現成的套件的機制下，
  自行依據其原理實作完成，並在回信時分別解釋該程式的實作方式:
  - 登入使用Cookie or Session的機制(若使用Cookie/Session則需要考慮到可能的Security Issue)。
  - 編輯送出Profile的Form需要有CSRF token的機制。
  - DB的query 要能避免SQL injection。
  - 要能避免XSS 攻擊。

## Setup

## Operation system and language runtime

- Ubuntu 20.04
- Python 3.8.5

### pyenv and virtualenv

請先安裝 pyenv

```
curl https://pyenv.run | bash
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
```

把下列這行加到 ~/.bash_profile (若使用 zsh，則加到 ~/.zshenv)

```
eval "$(pyenv virtualenv-init -)"
```

Restart your shell/terminal.

### Prepare environment

安裝相依套件

```
pyenv virtualenv ifriend
pyenv activate ifriend
pip install -r requirements.txt
```

## Local development

本地端開發
```
pyenv virtualenv ifriend
pyenv activate ifriend
python app.py
```

