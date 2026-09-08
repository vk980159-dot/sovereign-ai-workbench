"""
Result & Grounding Verification Tool (SIH26117).
Verifies that generated recommendations and claims are grounded in retrieved evidence
and verifies that generated output files exist and are non-empty.
"""

import os
from typing import Dict, Any, List, Optional


def verification_tool(
    claims: List[str],
    evidence_texts: List[str],
    artifact_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates claims against retrieved evidence texts and checks artifact files.
    """
    from app.config import settings

    verified_claims = []
    combined_evidence = " ".join(evidence_texts).lower()

    for claim in claims:
        # Simple token presence check
        tokens = [t.lower() for t in claim.split() if len(t) > 4]
        matches = [t for t in tokens if t in combined_evidence]
        grounded = len(matches) >= max(1, len(tokens) // 3) if tokens else True
        verified_claims.append({
            "claim": claim,
            "grounded": grounded,
            "matched_tokens": matches[:5]
        })

    # Artifact verification
    artifact_verified = True
    artifact_error = None
    artifact_details = None
    if artifact_filename:
        clean_name = os.path.basename(artifact_filename)
        path = os.path.join(settings.OUTPUT_DIR, clean_name)
        try:
            from app.agents.deliverables.validator import ArtifactValidator
            v_res = ArtifactValidator.validate_artifact(path)
            artifact_verified = v_res.get("verified", False)
            artifact_details = v_res
            if not artifact_verified:
                artifact_error = v_res.get("error", "Artifact verification failed.")
        except Exception as e:
            # Fallback to basic file existence & non-empty check
            if not os.path.isfile(path):
                artifact_verified = False
                artifact_error = f"Artifact '{clean_name}' does not exist on disk: {str(e)}"
            elif os.path.getsize(path) == 0:
                artifact_verified = False
                artifact_error = f"Artifact '{clean_name}' exists but is empty (0 bytes)."
            else:
                artifact_verified = True

    all_grounded = all(c["grounded"] for c in verified_claims) if verified_claims else True
    overall_passed = all_grounded and artifact_verified

    return {
        "passed": overall_passed,
        "claims_verified": len(verified_claims),
        "grounded_count": sum(1 for c in verified_claims if c["grounded"]),
        "claim_details": verified_claims,
        "artifact_verified": artifact_verified,
        "artifact_error": artifact_error,
        "artifact_details": artifact_details
    }
