from typing import Any
import json

import jwt
from jwt import PyJWKClient
from pydantic import ValidationError

from ..common.exceptions import AuthError
from ..schema.auth_schema import AuthenticatedUser, KeycloakTokenPayload
from ..config import settings


class KeycloakTokenVerifier:
    """
    Verifies and decodes JWT access tokens issued by Keycloak.
    """
    def __init__(self) -> None:
        """
        Initialize the token verifier using settings from 
        environment variables.
        """
        self.issuer = settings.keycloak_issuer
        self.client_id = settings.keycloak_client_id
        self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        self._jwks_client = PyJWKClient(self.jwks_url)

    def verify(self, token: str) -> AuthenticatedUser:
        """
        Verify a Keycloak JWT token and return an authenticated user.

        Attributes:
        -----------
        - token: The JWT access token string (from Authorization header).

        Returns:
        --------
        - AuthenticatedUser containing Keycloak user ID, username, email, and roles.

        Raises:
        -------
            AuthError: If the token is invalid, expired, or missing required claims.
        """
        raw_payload = self._decode(token)
        payload = self._validate_payload(raw_payload)
        return self._to_user(payload)

    def _decode(self, token: str) -> dict[str, Any]:
        """
        Decode and verify the JWT signature, expiry, and issuer.
        """
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)

            return jwt.decode(
                token,
                signing_key.key,
                algorithms=[settings.keycloak_jwt_algorithm],
                issuer=self.issuer,
                options={"verify_aud": False},
            )

        except jwt.PyJWTError as exc:
            raise AuthError("Invalid access token") from exc

    def _validate_payload(self, raw_payload: dict[str, Any]) -> KeycloakTokenPayload:
        """
        Validate the decoded payload against the KeycloakTokenPayload schema.

        This ensures all required claims (sub, preferred_username, email,
        realm_access.roles) are present and have correct types.
        """
        try:
            return KeycloakTokenPayload.model_validate(raw_payload)
        except ValidationError as exc:
            print("Token payload validation failed")
            print(json.dumps(raw_payload, indent=2))
            print(exc)
            raise AuthError("Token payload is missing required claims") from exc

    @staticmethod
    def _to_user(payload: KeycloakTokenPayload) -> AuthenticatedUser:
        """
        Convert the validated payload to an AuthenticatedUser
        domain object.
        """
        return AuthenticatedUser(
            keycloak_user_id=payload.sub,
            username=payload.preferred_username,
            email=payload.email,
            roles=set(payload.realm_access.roles),
        )