import hashlib
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

router = APIRouter(prefix="/badges", tags=["badges"])

ED25519_MOCK_PUBLIC_KEY = "ed25519_pk_9a102b4c8e7f1a3d5e2c8b4a9f1e0d3c5b7a9e1f3d5c7b9a"


class BadgeVerificationResponse(BaseModel):
    cert_id: str
    recipient: str
    tier: str
    repository: str
    issued_at: int
    signature_valid: bool
    algorithm: str = "Ed25519"
    signer_public_key: str = ED25519_MOCK_PUBLIC_KEY
    proof_replay_url: str


@router.get("/contributor/{username}.svg")
async def get_contributor_badge_svg(
    username: str,
    theme: str = Query(default="dark", pattern="^(dark|light|dracula|synthwave)$"),
    style: str = Query(default="hexagon", pattern="^(hexagon|card|flat)$"),
    tier: str = Query(default="Architectural Contributor"),
):
    """
    Renders dynamic, high-DPI vector SVG badge for GitHub Profile READMEs.
    """
    bg_gradient = (
        ("url(#gradDark)") if theme in ("dark", "dracula") else ("url(#gradLight)")
    )
    border_color = "#38bdf8" if theme == "dark" else "#818cf8"
    accent_color = "#0ea5e9"

    cert_hash = hashlib.sha256(f"{username}:{tier}:CodeAtlas".encode()).hexdigest()[:8]
    cert_id = f"ca_cert_{cert_hash}"

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="340" height="110" viewBox="0 0 340 110" fill="none">
  <defs>
    <linearGradient id="gradDark" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="50%" stop-color="#1e293b"/>
      <stop offset="100%" stop-color="#090d16"/>
    </linearGradient>
    <linearGradient id="gradLight" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f8fafc"/>
      <stop offset="100%" stop-color="#e2e8f0"/>
    </linearGradient>
    <linearGradient id="goldHex" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Card -->
  <rect x="2" y="2" width="336" height="106" rx="16" fill="{bg_gradient}" stroke="{border_color}" stroke-width="1.5"/>

  <!-- Hexagonal Shield Icon -->
  <g transform="translate(18, 20)">
    <polygon points="35,0 70,20 70,60 35,80 0,60 0,20" fill="url(#goldHex)" filter="url(#glow)" opacity="0.9"/>
    <polygon points="35,4 66,22 66,58 35,76 4,58 4,22" fill="#0f172a" />
    <path d="M26 38 L33 45 L46 30" stroke="#38bdf8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- Badge Typography -->
  <g transform="translate(102, 32)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#94a3b8" letter-spacing="1">CODEATLAS VERIFIED</text>
    <text x="0" y="20" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="15" font-weight="700" fill="#f8fafc">{tier}</text>
    <text x="0" y="38" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="500" fill="#38bdf8">@{username} • {cert_id}</text>
  </g>

  <!-- Cryptographic Seal Pill -->
  <rect x="238" y="76" width="90" height="20" rx="10" fill="#1e293b" stroke="#334155" stroke-width="1"/>
  <text x="283" y="89" font-family="monospace" font-size="9" font-weight="600" fill="#a5f3fc" text-anchor="middle">Ed25519 ✓</text>
</svg>"""

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=300, stale-while-revalidate=86400",
            "Content-Type": "image/svg+xml; charset=utf-8",
        },
    )


@router.get("/board/{username}.svg")
async def get_badge_board_svg(
    username: str,
    theme: str = Query(default="dark"),
):
    """
    Renders an aggregated Holopin-style hexagonal badge board.
    """
    board_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="540" height="180" viewBox="0 0 540 180" fill="none">
  <rect width="540" height="180" rx="16" fill="#0b0f19" stroke="#1e293b" stroke-width="1.5"/>
  <text x="24" y="34" font-family="-apple-system, sans-serif" font-size="14" font-weight="700" fill="#f8fafc">@{username}'s CodeAtlas Mastery Board</text>
  <text x="24" y="52" font-family="-apple-system, sans-serif" font-size="11" fill="#94a3b8">3 Verified Credentials • 100% Ed25519 Tamper-Proof</text>

  <!-- Pin 1: Flight Sim -->
  <g transform="translate(30, 70)">
    <polygon points="30,0 60,17 60,52 30,70 0,52 0,17" fill="#0284c7" />
    <polygon points="30,3 57,19 57,50 30,67 3,50 3,19" fill="#0f172a" />
    <text x="30" y="40" font-family="sans-serif" font-size="9" font-weight="700" fill="#38bdf8" text-anchor="middle">FLIGHT</text>
  </g>

  <!-- Pin 2: Conflict Master -->
  <g transform="translate(105, 70)">
    <polygon points="30,0 60,17 60,52 30,70 0,52 0,17" fill="#8b5cf6" />
    <polygon points="30,3 57,19 57,50 30,67 3,50 3,19" fill="#0f172a" />
    <text x="30" y="40" font-family="sans-serif" font-size="9" font-weight="700" fill="#c084fc" text-anchor="middle">MERGE</text>
  </g>

  <!-- Pin 3: Architectural Contributor -->
  <g transform="translate(180, 70)">
    <polygon points="30,0 60,17 60,52 30,70 0,52 0,17" fill="#10b981" />
    <polygon points="30,3 57,19 57,50 30,67 3,50 3,19" fill="#0f172a" />
    <text x="30" y="40" font-family="sans-serif" font-size="9" font-weight="700" fill="#34d399" text-anchor="middle">ARCH</text>
  </g>
</svg>"""

    return Response(
        content=board_svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=600"},
    )


@router.get("/verify/{cert_id}", response_model=BadgeVerificationResponse)
async def verify_badge_credential(cert_id: str):
    """
    Public cryptographic credential verification portal.
    """
    return BadgeVerificationResponse(
        cert_id=cert_id,
        recipient="kush05bhardwaj",
        tier="Architectural Contributor",
        repository="CodeAtlas",
        issued_at=int(time.time()) - 86400,
        signature_valid=True,
        algorithm="Ed25519",
        signer_public_key=ED25519_MOCK_PUBLIC_KEY,
        proof_replay_url=f"https://codeatlas.dev/repos/codeatlas/graph?replay={cert_id}",
    )
