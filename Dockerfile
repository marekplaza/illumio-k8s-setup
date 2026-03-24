# Runner image for Illumio K8s onboarding pipeline
# Contains: kubectl, helm, python3 (with yaml + requests)
FROM alpine:3.21

RUN apk add --no-cache \
      python3 py3-yaml py3-requests \
      curl bash jq \
    && curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install kubectl /usr/local/bin/ && rm kubectl \
    && curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash \
    && rm -rf /var/cache/apk/*

# Verify installations
RUN kubectl version --client && helm version && python3 --version
