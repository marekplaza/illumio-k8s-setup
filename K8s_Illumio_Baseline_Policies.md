# Kubernetes Infrastructure Baseline Policies for Illumio

Template polityk infrastrukturalnych wymaganych do prawidłowego działania klastra Kubernetes
pod **full enforcement** w Illumio z trybem **CLAS** (Cluster Local Actor Store).

## Wymagane labele

| Key | Value | Opis |
|-----|-------|------|
| `role` | `Kubernetes Node` | Wszystkie node'y klastra (control-plane + worker) |
| `env` | `<nazwa-klastra>` | Identyfikator środowiska/klastra (np. Nuvira, Production) |
| `app` | `K8s-Infrastructure` | Oznaczenie infrastruktury klastra |

## Polityki infrastrukturalne (wymagane)

### 1. Kubelet → Pods (health probes)

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | role: `Kubernetes Node` (extra-scope) |
| **Provider** | All Managed Workloads |
| **Porty** | All TCP, All UDP |
| **Priorytet** | KRYTYCZNY — bez tego pody tracą readiness/liveness |

**Dlaczego:** Kubelet na każdym node wysyła HTTP health probes do podów. Blokada = pody
przechodzą w NotReady → restart → CrashLoopBackOff.

---

### 2. Pods → CoreDNS

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | All Managed Workloads |
| **Provider** | role: `Kubernetes Node` |
| **Porty** | 53/TCP, 53/UDP |
| **Priorytet** | KRYTYCZNY — bez DNS pody nie rozwiążą nazw serwisów |

**Dlaczego:** Każdy pod używa CoreDNS (kube-system) do rozwiązywania `svc.cluster.local`.
Blokada = połączenia między mikroserwisami nie działają (NXDOMAIN).

---

### 3. Pods → Kube API Server

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | All Managed Workloads |
| **Provider** | role: `Kubernetes Node` |
| **Porty** | 6443/TCP |
| **Priorytet** | WYSOKI — wymagany dla service accounts, RBAC, kubectl exec |

**Dlaczego:** Pody komunikują się z API server na potrzeby:
- Automontowania service account tokenów
- Kubernetes API watches (np. Kubelink)
- `kubectl exec/logs/port-forward`
- Admission webhooks

---

### 4. Node ↔ Node — CNI Overlay

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | role: `Kubernetes Node` |
| **Provider** | role: `Kubernetes Node` |
| **Porty** | 6081/UDP (Antrea/Geneve), 4789/UDP (VXLAN) |
| **Priorytet** | KRYTYCZNY — bez tego ruch pod-to-pod między node'ami nie przechodzi |

**Dlaczego:** CNI plugin (Antrea, Calico, Flannel) enkapsuluje ruch pod-to-pod w tunelu
overlay. Blokada = pody na różnych node'ach nie mogą się komunikować.

**Uwaga:** Porty zależą od CNI:

| CNI | Protokół | Port |
|-----|----------|------|
| Antrea | Geneve | 6081/UDP |
| Calico (VXLAN mode) | VXLAN | 4789/UDP |
| Flannel | VXLAN | 8472/UDP |
| Cilium | Geneve | 6081/UDP |
| Cilium (VXLAN) | VXLAN | 8472/UDP |

---

### 5. Control-plane ↔ Control-plane — etcd

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | role: `Kubernetes Node` |
| **Provider** | role: `Kubernetes Node` |
| **Porty** | 2379/TCP (client), 2380/TCP (peer) |
| **Priorytet** | KRYTYCZNY — bez tego klaster traci quorum |

**Dlaczego:** etcd przechowuje cały stan klastra. Blokada komunikacji peer = split brain,
utrata quorum, klaster przestaje działać.

**Uwaga:** Idealnie ograniczyć do node'ów control-plane (osobny label `role: K8s-ControlPlane`).

---

### 6. K8s Nodes → PCE (Illumio)

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | role: `Kubernetes Node` |
| **Provider** | IP List: Any (lub dedykowany PCE IP) |
| **Porty** | 8443/TCP |
| **Priorytet** | WYSOKI — bez tego C-VEN/Kubelink tracą kontakt z PCE |

**Dlaczego:** C-VEN i Kubelink wysyłają heartbeaty i pobierają polityki z PCE.
Blokada = brak aktualizacji polityk, utrata widoczności w PCE.

**Best practice:** Zamiast `Any`, stworzyć dedykowaną IP List z adresem PCE.

---

### 7. CLAS Internal (C-VEN ↔ Kubelink)

| Parametr | Wartość |
|----------|---------|
| **Scope** | env: `<klaster>` |
| **Consumer** | role: `Kubernetes Node` |
| **Provider** | role: `Kubernetes Node` |
| **Porty** | 9000/TCP, 9001/TCP, 9002/TCP |
| **Priorytet** | WYSOKI (tylko CLAS mode) |

**Dlaczego:** W trybie CLAS, C-VEN na każdym node pobiera polityki i token agenta
od Kubelink przez gRPC. Blokada = C-VEN nie otrzymuje polityk.

**Uwaga:** Wymagane tylko w trybie `clusterMode: clas`. W legacy mode — nie potrzebne.

---

## Polityki aplikacyjne (per-aplikacja)

Oprócz infrastruktury, każda aplikacja wymaga dedykowanych rulesetów. Przykład dla 3-tier app:

| Ruleset | Consumer → Provider | Port |
|---------|-------------------|------|
| `App-Frontend-to-API` | role: Web → role: API | 8080/TCP |
| `App-API-to-Database` | role: API → role: Database | 5432/TCP |

**Zasada:** Allow only what is required. Brak reguły = deny (w full enforcement).

---

## Kolejność wdrażania

1. **Stwórz labele** (`Kubernetes Node`, `K8s-Infrastructure`, env label)
2. **Przypisz labele** do node workloadów w PCE
3. **Stwórz rulesets infrastrukturalne** (1-7) w trybie draft
4. **Sprowizjonuj** wszystkie na raz
5. **Przetestuj w visibility_only** — sprawdź czy PCE widzi flow'y jako allowed
6. **Przełącz na full enforcement** — najpierw node workloads, potem CWP

---

## Weryfikacja

Po włączeniu full enforcement sprawdź:

```bash
# Czy pody są Ready?
kubectl get pods -A | grep -v Running

# Czy DNS działa?
kubectl run -it --rm dns-test --image=busybox -- nslookup kubernetes.default

# Czy API server dostępny?
kubectl auth can-i get pods

# Czy overlay działa (cross-node)?
kubectl run -it --rm net-test --image=busybox -- wget -qO- http://<pod-ip-on-other-node>

# Czy Illumio jest online?
kubectl logs deploy/illumio-kubelink -n illumio-system --tail=5
```

---

## Uwagi

- Template zakłada **jeden klaster per env label**. Dla wielu klastrów użyj osobnych env labels
- Porty CNI overlay zależą od pluginu — sprawdź `kubectl get pods -n kube-system` i dokumentację CNI
- Ruleset #1 (kubelet→pods) jest celowo szeroki (all TCP+UDP) — kubelet potrzebuje dowolnego portu probes
- Rozważ osobne labele `role: K8s-ControlPlane` vs `role: K8s-Worker` dla bardziej granularnych polityk etcd
- W produkcji zamień `IP List: Any` w regule #6 na dedykowany adres PCE
