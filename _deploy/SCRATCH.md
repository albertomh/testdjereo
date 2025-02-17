# Scratchpad

## Build a container image

### For GitHub Container Registry

Locally:

```sh
# build image `testdjereo:latest`
docker build -t testdjereo .

# verify new image works locally
docker run --env-file _deploy/.env.deploy -p 8000:8000 testdjereo

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

### Separate architecture builds for local vs Droplet

```sh
docker buildx build --platform linux/amd64 -t testdjereo:amd64 --load .
docker buildx build --platform linux/arm64 -t testdjereo:arm64 --load .

# skip since `docker save` does not work with manifest lists and so would have to recreate
# manifest on VPS.
# docker manifest create testdjereo:latest \
#  testdjereo:amd64 \
#  testdjereo:arm64
# docker manifest inspect testdjereo:latest
```

## Create a Droplet

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

# get MD5 fingerprint of public key
# ssh-keygen -l -E md5 -f  ~/.ssh/id_ed25519.pub
# SSH_FINGERPRINT=<fingerprint>


# create a Droplet
# prereq: public key added to DO account (for later SSHing in)
doctl compute droplet create testdjereo \
 --size s-1vcpu-512mb-10gb \
 --region ams3 \
 --image debian-12-x64 \
 --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
 --wait

# check Droplet status & IP address
doctl compute droplet list
```

## Install docker and run inside Droplet

Locally:

```sh
ssh root@<IPv4address>
```

In Droplet:

```sh
# https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-debian-10
sudo apt update
sudo apt install apt-transport-https ca-certificates curl gnupg2 software-properties-common

curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" -y
sudo apt update

sudo apt install docker-ce -y
sudo systemctl status docker
```

## Push image to VPS and run

Locally:

```sh
docker buildx build --platform linux/amd64 -t testdjereo:amd64 --load .
docker save testdjereo:amd64 | gzip > testdjereo_amd64.tar.gz

# docker save testdjereo | ssh -C root@<IPv4address> docker load
tar czf - testdjereo_amd64.tar.gz | ssh root@$DO_DROPLET_IP "tar xzf - -C ~"
ssh root@$DO_DROPLET_IP 'docker load < testdjereo_amd64.tar.gz'

scp _deploy/.env.deploy root@$DO_DROPLET_IP:/root/testdjereo/.env
ssh root@<IPv4address> "chmod 600 /root/testdjereo/.env"

scp _deploy/nginx.conf root@$DO_DROPLET_IP:/root/testdjereo/nginx.conf
```

In Droplet:

```sh
cd testdjereo/

docker network create testdjereo_net

docker run --detach --name testdjereo \
  --env-file /root/testdjereo/.env \
  --network testdjereo_net \
  --publish 8000:8000 \
  --volume testdjereo_static:/app/static \
  testdjereo:amd64

docker exec testdjereo python manage.py migrate
docker exec -it testdjereo python manage.py createsuperuser

docker run --detach --name nginx \
  --restart unless-stopped \
  --network testdjereo_net \
  --publish 80:80 \
  --volume testdjereo_static:/static:ro \
  --volume /root/testdjereo/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:latest

# check any errors
docker logs testdjereo
```
