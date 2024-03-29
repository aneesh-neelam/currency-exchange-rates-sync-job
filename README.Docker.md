### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### Actual Push

Docker Hub

* `docker buildx build . --push --platform linux/arm64,linux/amd64,linux/amd64/v2 --tag aneeshneelam/currency-exchange-sync:latest --tag aneeshneelam/currency-exchange-sync:2.0 --attest type=provenance,mode=max`

DigitalOcean Container Registry (Private)

* `docker buildx build . --push --platform linux/amd64 --tag registry.digitalocean.com/aneeshneelam-container-registry-sfo3/currency-exchange-sync --attest type=provenance,mode=max`

### References

* [Docker's Python guide](https://docs.docker.com/language/python/)
