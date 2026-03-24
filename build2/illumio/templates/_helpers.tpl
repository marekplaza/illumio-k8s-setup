{{/*
Expand the name of the chart.
*/}}
{{- define "illumio.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Release namespace override
*/}}
{{- define "illumio.namespace" -}}
{{- default .Release.Namespace .Values.namespaceOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "illumio.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "illumio.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "illumio.labels" -}}
helm.sh/chart: {{ include "illumio.chart" . }}
{{ include "illumio.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "illumio.selectorLabels" -}}
app.kubernetes.io/name: {{ include "illumio.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "illumio.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "illumio.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the pull secret for Illumio images
*/}}
{{- define "illumio.imagePullSecret" }}
{{- with .Values.imagePullSecret}}
{{- printf "{\"auths\":{\"quay.io\":{\"username\":\"%s\",\"password\":\"%s\",\"auth\":\"%s\"}}}" .username .password (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}
{{- end }}

{{/*
Renders a value that contains dictionary
*/}}
{{- define "illumio.renderDictionary" -}}
{{- tpl ((.value | toYaml)) .context }}
{{- end -}}

{{/*
Create etcd root password or reuse the existing one in case of an upgrade
*/}}
{{- define "illumio.etcdRootPassword" -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace "illumio-secret" }}
{{- if and $secret ($secret.data).etcd_root_password }}
etcd_root_password: {{ $secret.data.etcd_root_password | b64dec }}
{{- else }}
etcd_root_password: {{ randAlphaNum 16 | quote }}
{{- end }}
{{- end }}

{{/*
Create a password for Policy Status endpoint or reuse the existing one in case of an upgrade
*/}}
{{- define "illumio.policyStatusPassword" -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace "illumio-secret" }}
{{- if and $secret ($secret.data).policy_status_password }}
policy_status_password: {{ $secret.data.policy_status_password | b64dec }}
{{- else }}
policy_status_password: {{ randAlphaNum 16 | quote }}
{{- end }}
{{- end }}

{{/*
Render Secret Names combining secrets specified under images with the main list of secrets in imagePullSecrets.
Includes the illumio-pull-secret created by the chart if the registry credentials are specified.
*/}}
{{- define "renderPullSecrets" -}}
  {{- $pullSecrets := list -}}
  {{- $context := .context -}}

  {{- if and $context.Values.imagePullSecret $context.Values.imagePullSecret.username $context.Values.imagePullSecret.password -}}
    {{- $pullSecrets = append $pullSecrets "illumio-pull-secret" -}}
  {{- end -}}

  {{- range $context.Values.imagePullSecrets -}}
    {{- if kindIs "map" . -}}
      {{- $pullSecrets = append $pullSecrets .name -}}
    {{- else -}}
      {{- $pullSecrets = append $pullSecrets . -}}
    {{- end -}}
  {{- end -}}

  {{- range .images -}}
    {{- range .pullSecrets -}}
      {{- if kindIs "map" . -}}
        {{- $pullSecrets = append $pullSecrets .name -}}
      {{- else -}}
        {{- $pullSecrets = append $pullSecrets . -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}

  {{- if (not (empty $pullSecrets)) -}}
imagePullSecrets:
    {{- range $pullSecrets | uniq }}
  - name: {{ . }}
    {{- end }}
  {{- end }}
{{- end -}}

{{/*
Renders ignoredNamespaces combining namespaces specified in values with the .Release.Namespace
*/}}
{{- define "renderIgnoredNamespaces" -}}
  {{- $ignoredNamespaces := list -}}
  {{- $context := . -}}

  {{- $ignoredNamespaces = append $ignoredNamespaces "kube-system" -}}
  {{- $ignoredNamespaces = append $ignoredNamespaces (include "illumio.namespace" .) -}}

  {{- range $context.Values.waitForPolicy.ignoredNamespaces -}}
      {{- $ignoredNamespaces = append $ignoredNamespaces . -}}
  {{- end -}}

  {{- if (not (empty $ignoredNamespaces)) -}}
  {{ uniq $ignoredNamespaces | toJson | quote }}
  {{- end }}
{{- end -}}


{{/*
Enables TLS if it's set using useTLS and supported by both Kubelink and C-VEN
*/}}
{{- define "isTLSenabled" -}}
  {{- $semverRegex := "^[0-9]+\\.[0-9]+\\.[0-9]+-.*$" -}}
  {{- $kubelinkMin := ">=5.6.0-0" -}}
  {{- $cvenMin := ">=23.4.8-0" -}}
  {{- $context := . -}}
  {{- if or (eq (lower $context.Values.clusterMode) "migratelegacytoclas") (eq (lower $context.Values.clusterMode) "clas") }}
    {{- if and (regexMatch $semverRegex $context.Values.kubelink.imageTag) (regexMatch $semverRegex $context.Values.cven.imageTag) -}}
      {{- if and $context.Values.useTLS (semverCompare $kubelinkMin $context.Values.kubelink.imageTag) (semverCompare $cvenMin $context.Values.cven.imageTag) -}}
        {{ true }}
      {{- else -}}
        {{ false }}
      {{- end -}}
    {{- else -}}
      {{ $context.Values.useTLS }}
    {{- end -}}
  {{- else -}}
    {{ false }}
  {{- end -}}
{{- end -}}
