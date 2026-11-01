# Verifiable Badges & Reputation Network Component Specification

## Purpose
The Verifiable Badges & Reputation Network provides dynamic, embeddable vector graphics (SVGs) and cryptographic proofs of real-world developer competencies. Inspired by Holopin and verifiable digital credentials, it awards tamper-proof badges for completed Flight Simulator missions, high-quality open-source pull requests, and architectural maintainership, enabling developers to showcase verified engineering accomplishments on their GitHub profile READMEs and portfolios.

## System Dependencies
- **FastAPI (`routers/badges.py`)**: Dynamic SVG templating, public credential verification API, and leaderboard rankings.
- **Cryptography Subsystem (`services/badge_signer.py`)**: Asymmetric Ed25519 digital signature generation and verification.
- **Redis Cache**: High-throughput sub-15ms edge caching for public SVG badge requests from GitHub proxies (`camo.githubusercontent.com`).
- **PostgreSQL / SQLAlchemy**: Credential issuance records, user achievement matrices, and public key registries.
- **Frontend (`apps/web`)**: Collectible hexagonal badge board, embed snippet modal, and public verification portal (`/verify/{cert_id}`).

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Dynamic SVG Rendering | $O(S)$ | $O(S)$ | Assembling vector paths, badge gradients, and text tokens for $S$ badge elements ($< 5\text{ms}$) |
| Ed25519 Signature Generation | $O(B)$ | $O(1)$ | Signing canonical JSON credential payload of size $B$ bytes using private key |
| Ed25519 Signature Verification | $O(B)$ | $O(1)$ | Verifying signature against CodeAtlas public key for incoming verification request |
| Hexagonal Badge Board Layout | $O(N)$ | $O(N)$ | Calculating coordinate grid offsets for $N$ unlocked user badges |

## Cryptographic Credential Protocol

```
┌─────────────────────────────────┐
│     Developer Mission / PR      │
│  (Completed Flight Sim or PR)   │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Canonical JSON Payload        │
│   { cert_id, user, tier, ... }  │
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│    Ed25519 Private Key Signer   │ ───▶ │ Tamper-Proof Cryptographic  │
│    (SHA-512 + Curve25519 Curve) │      │ Signature String            │
└─────────────────────────────────┘      └─────────────────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│  Dynamic SVG Generator          │ ───▶ │ Public Verification Portal  │
│  (Embeds Signature & Proof URL) │      │ (/verify/ca_cert_...)       │
└─────────────────────────────────┘      └─────────────────────────────┘
```

### 1. Dynamic SVG Badge Endpoint
- Endpoint: `GET /api/v1/badges/contributor/{username}.svg?theme=dark|light&style=hexagon|card`.
- Optimized with `ETag` and `Cache-Control: public, max-age=300, stale-while-revalidate=86400` headers to ensure instant loading inside GitHub markdown previews.
- Renders user tier, verified PR count, blast radius containment rating, and cryptographic issue stamp.

### 2. Ed25519 Digital Signing
- All issued credentials contain a canonical JSON structure signed with the CodeAtlas Ed25519 private key:
  $$\sigma = \text{Sign}_{\text{sk}}(H(\text{Payload}))$$
- Prevents tampering, client spoofing, or fraudulent badge alterations.

### 3. Public Verification Portal
- Accessible at `https://codeatlas.dev/verify/{cert_id}`.
- Allows hiring managers, peers, and open-source maintainers to independently verify the cryptographic signature using the CodeAtlas public key.
- Renders an interactive replay of the verified contribution or flight simulation directly on the CodeAtlas repository canvas.

### 4. Holopin-Style Collectible Badge Board
- Renders an interactive, hexagonal sticker board at `/u/{username}`.
- Provides a single aggregated dynamic board SVG (`/api/v1/badges/board/{username}.svg`) for embedding full badge collections in GitHub READMEs.

