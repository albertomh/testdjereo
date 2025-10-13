# TODO

## Branch `deploy`

Mission: to augment a `djereo`-generated project (`testdjereo`) with automated deployment
to Digital Ocean.

Current state: CI via GitHub Actions, containerise and store in `ghcr.io`.

### Steps

- <https://chatgpt.com/g/g-p-68dd60a480cc8191940743f54aeaab09-eden/c/68ecf4cc-ce8c-8333-b136-8a7a983df8a8>

- [ ] Staged pipeline that:
  - [ ] Is triggered by a tag
  - [ ] Automatically deploys to `test`
  - [ ] Offers a manual deployment step to `prod`

- [ ] For each env (`test` + `prod`), GitHub Action to:
  - [ ] Rather than bash, use Python SDK <https://github.com/digitalocean/pydo>

  - [ ] Create infrastructure - app server + postgres:
    - [ ] In `test`, this should be a VPS (droplet), NOT dedicated postgres instance!

  - [ ] Perform blue/green deployment of app code within VPS

  - [ ] Perform healthchecks on service
