# Scratchpad

## Build a container image

Locally:

```sh
# build image `testdjereo:latest`
docker build -t testdjereo .

# verify new image works locally
docker run --env-file .env -p 8000:8000 testdjereo

# generate new PAT (classic), scoped to `testdjereo` repo and with permissions:
# ```
# write:packages
# delete:packages
# ```
<https://github.com/settings/tokens>

# log in to GitHub Container Registry
GHPAT=<GHPAT>
echo $GHPAT | docker login ghcr.io -u albertomh --password-stdin

# tag under the ghcr.io namespace
docker tag testdjereo ghcr.io/albertomh/testdjereo:latest

# push to GitHub Container Registry
docker push ghcr.io/albertomh/testdjereo:latest
```

## Deploy the image to a VPS

Locally:

```sh
# install doctl
brew install doctl

# create a Digital Ocean API token with access to
# ```
# droplets:all
# project:read
# regions:all
# sizes:all
# ssh_keys:all
# ```
DOPAT=<DOPAT>

# log in to DO (using the 'default' access context)
doctl auth init --access-token $DOPAT

# list available regions & sizes for DO Droplets
doctl compute region list
doctl compute size list

# create a Droplet
doctl compute droplet create testdjereo \
 --size s-1vcpu-512mb-10gb \
 --image ghcr.io/albertomh/testdjereo:latest \
 --region lon1

# check Droplet status & ip
doctl compute droplet list
```
