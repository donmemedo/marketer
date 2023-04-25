import jwt
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# This module contains the piece of code described previously
from jwksutils import rsa_pem_from_jwk
from config import setting

# obtain jwks as you wish: configuration file, HTTP GET request to the endpoint returning them;

# configuration, these can be seen in valid JWTs from Azure B2C:
valid_audiences = ['d7f48c21-2a19-4bdb-ace8-48928bff0eb5'] # id of the application prepared previously


class InvalidAuthorizationToken(Exception):
    def __init__(self, details):
        super().__init__('Invalid authorization token: ' + details)


def get_kid(token):
    headers = jwt.get_unverified_header(token)
    if not headers:
        raise InvalidAuthorizationToken('missing headers')
    try:
        return headers['kid']
    except KeyError:
        raise InvalidAuthorizationToken('missing kid')


def get_jwk(kid):
    for jwk in setting.JWKS.get('keys'):
        if jwk.get('kid') == kid:
            return jwk
    raise InvalidAuthorizationToken('kid not recognized')


def get_public_key(token):
    return rsa_pem_from_jwk(get_jwk(get_kid(token)))


def validate_jwt(jwt_to_validate):
    public_key = get_public_key(jwt_to_validate)

    try:
        decoded = jwt.decode(jwt_to_validate,
                             public_key,
                             verify=True,
                             algorithms=['RS256'],
                            #  audience=valid_audiences,
                             issuer=setting.ISSUER)

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
        return True
    except Exception as error:
        print("Wrong JWT")
        return False


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        is_token_valid: bool = False

        try:
            payload = validate_jwt(jwtoken)
        except:
            payload = None
        if payload:
            is_token_valid = True
        return is_token_valid


def get_sub(req: Request):
    token = req.headers.get('authorization').split()[1]
    public_key = get_public_key(token)

    decoded = jwt.decode(token,
                         public_key,
                         verify=True,
                         algorithms=['RS256'],
                         issuer=setting.ISSUER) 
    
    return decoded.get('sub')
