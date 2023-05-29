import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tools.jwksutils import rsa_pem_from_jwk
from tools.config import setting
from jwt.exceptions import InvalidIssuerError, ExpiredSignatureError
from requests.exceptions import ConnectionError
import requests
from json import loads
from src.tools.logger import logger

valid_audiences = [setting.APPLICATION_ID] # id of the application prepared previously


try:
    jwks_req = requests.get(setting.JWKS_CONFIGURATION_URL)
    if jwks_req.status_code == 200:
        jwks = loads(jwks_req.content)

except ConnectionError as err:
    logger.error("Cannot connect to get IDP configurations")
except Exception as err:
    logger.error(f"Error in getting IDP Configurations: {err}") 
else:
    logger.info("Successfully got the IDP configurations")


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
    for jwk in jwks.get('keys'):
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
        return True
    except InvalidIssuerError as err:
        logger.info("Invalid issuer")
    except ExpiredSignatureError as err:
        logger.info("Signature has expired")
    except Exception as error:
        logger.info(f"Wrong JWT {error}")
    
    return False


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Invalid authentication scheme."
                    )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Invalid token or expired token."
                    )
            return credentials.credentials
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid authorization code."
            )

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
