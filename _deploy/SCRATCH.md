# Scratchpad

## Build a container image

### For GitHub Container Registry

Locally:

```sh
# build image `testdjereo:latest`
docker build -t testdjereo -f _deploy/Dockerfile .

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
docker build --platform linux/amd64 -t testdjereo:amd64 --load .
docker build --platform linux/arm64 -t testdjereo:arm64 --load .

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

## Configure Droplet

<https://www.digitalocean.com/community/tutorials/initial-server-setup-with-debian-11>

Locally:

```sh
ssh root@$DO_DROPLET_IP
```

In Droplet:

```sh
adduser alberto
usermod -aG sudo alberto
cp -r ~/.ssh /home/alberto
chown -R alberto:alberto /home/alberto/.ssh
```

Locally:

```sh
ssh alberto@$DO_DROPLET_IP
```

In Droplet:

```sh
sudo apt update
sudo apt install ufw
sudo ufw allow OpenSSH
sudo ufw enable
sudo ufw status
```

## Install docker and run inside Droplet

Locally:

```sh
ssh alberto@$DO_DROPLET_IP
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

sudo groupadd docker
sudo usermod -aG docker alberto
```

## Push image to VPS and run

Locally:

```sh
docker build \
  --file _deploy/deploy.Dockerfile \
  --platform linux/amd64 \
  --tag testdjereo:amd64 \
  --load .
docker save testdjereo:amd64 | gzip > testdjereo_amd64.tar.gz

# docker save testdjereo | ssh -C alberto@DO_DROPLET_IP docker load
tar czf - testdjereo_amd64.tar.gz | ssh alberto@$DO_DROPLET_IP "tar xzf - -C /etc/testdjereo"
ssh alberto@$DO_DROPLET_IP 'docker load < /etc/testdjereo/testdjereo_amd64.tar.gz'

scp _deploy/.env.deploy alberto@$DO_DROPLET_IP:/etc/testdjereo/.env
ssh alberto@$DO_DROPLET_IP "chmod 600 /etc/testdjereo/.env"

scp _deploy/nginx.conf alberto@$DO_DROPLET_IP:/etc/testdjereo/nginx.conf
```

In Droplet:

```sh
cd /etc/testdjereo/

# [ ] ALLOWED_HOSTS must include $DO_DROPLET_IP
# [ ] CSRF_TRUSTED_ORIGINS must include 'https://*.$DO_DROPLET_IP'
nano .env

docker network create testdjereo_net

docker rm -f testdjereo; \
  docker run --detach --name testdjereo \
    --user root \
    --env-file /etc/testdjereo/.env \
    --network testdjereo_net \
    --publish 8000:8000 \
    --volume testdjereo_static:/app/static \
    testdjereo:amd64

docker exec testdjereo python manage.py migrate
docker exec -it testdjereo python manage.py createsuperuser

docker rm -f nginx; \
  docker run --detach --name nginx \
    --restart unless-stopped \
    --network testdjereo_net \
    --publish 443:443 \
    --volume testdjereo_static:/static:ro \
    --volume /etc/testdjereo/etc/nginx/privkey.pem:/etc/nginx/privkey.pem:ro \
    --volume /etc/testdjereo/etc/nginx/fullchain.pem:/etc/nginx/fullchain.pem:ro \
    --volume /etc/testdjereo/etc/nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
    nginx:latest

# check for errors
docker logs testdjereo
docker logs nginx
```

## Create self-signed cert (testing SSL)

Self-signed cert necessary since LetsEncrypt only works with domain name.

In Droplet:

```sh
# ensure .env's ALLOWED_HOSTS includes 'testdjereo' since that is what nginx will use
nano testdjereo/.env

# target dir for Self-Signed Certificate
mkdir -p /etc/testdjereo/etc/nginx/

# generate a Self-Signed Certificate
openssl req -x509 -newkey rsa:4096 \
  -keyout /etc/testdjereo/etc/nginx/privkey.pem \
  -out /etc/testdjereo/etc/nginx/fullchain.pem \
  -days 365 -nodes \
  -subj "/CN=$(curl -s ifconfig.me)"

# update nginx.conf
    ```
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name $DO_DROPLET_IP;

    ssl_certificate /etc/nginx/fullchain.pem;
    ssl_certificate_key /etc/nginx/privkey.pem;

    location /static/ {
        alias   /static/;
        expires 30d;
        autoindex off;
    }

    location / {
        proxy_pass http://testdjereo:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
    ```
# restart nginx
docker restart nginx

sudo ufw allow 443
sudo ufw status
```
