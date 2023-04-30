import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# This module contains the piece of code described previously
from jwksutils import rsa_pem_from_jwk
from config import setting
from jwt.exceptions import InvalidIssuerError, ExpiredSignatureError

# obtain jwks as you wish: configuration file, HTTP GET request to the endpoint returning them;

# configuration, these can be seen in valid JWTs from Azure B2C:
valid_audiences = ['d7f48c21-2a19-4bdb-ace8-48928bff0eb5'] # id of the application prepared previously

jwks = {"keys":[{"kty":"RSA","use":"sig","kid":"433168608B265F60ADD25B4D33679222DA9DE0FFRS256","x5t":"QzFoYIsmX2Ct0ltNM2eSItqd4P8","e":"AQAB","n":"3yApnhhNZhLf5Z1XpIFC-rUJtJ_3BzR-SMcsAryWLggu11xv7oRJZSugstcgh-Ohbma1VK1Yfv_ZrfRh-pSBZWN3vCqXR2tBMz-cdXvRREMB-H_ANfmvdZKWcLn8myJcjCmAS7mrd21tC1Bpvr5Bt-SPqeaxFj52hnZFD1hXq0L3V7WpFtqpOjvW2_Xfov01N0lhoGtKrl8jCTMPmy-wZEC1fGcpfSSnlNor-q5FQm4QRpjzRaVL4PkzT137CLwfiSlXiUEy3Sqxqn_fQ4vsVI7gaY3nQIba7SaDRFwr62ikFxQhDD-zsllXGRy4lCpF0njDT9FQ_CvZzGKknHw1pQ","x5c":["MIIGdDCCBVygAwIBAgIQGglwTzShkJAHdRCE/ovcPjANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMCUEwxIjAgBgNVBAoTGVVuaXpldG8gVGVjaG5vbG9naWVzIFMuQS4xJzAlBgNVBAsTHkNlcnR1bSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTEpMCcGA1UEAxMgQ2VydHVtIERvbWFpbiBWYWxpZGF0aW9uIENBIFNIQTIwHhcNMjMwMzE4MTU1MjU4WhcNMjQwMzE3MTU1MjU3WjAcMRowGAYDVQQDDBEqLnRhdmFuYWJyb2tlci5pcjCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAN8gKZ4YTWYS3\u002BWdV6SBQvq1CbSf9wc0fkjHLAK8li4ILtdcb\u002B6ESWUroLLXIIfjoW5mtVStWH7/2a30YfqUgWVjd7wql0drQTM/nHV70URDAfh/wDX5r3WSlnC5/JsiXIwpgEu5q3dtbQtQab6\u002BQbfkj6nmsRY\u002BdoZ2RQ9YV6tC91e1qRbaqTo71tv136L9NTdJYaBrSq5fIwkzD5svsGRAtXxnKX0kp5TaK/quRUJuEEaY80WlS\u002BD5M09d\u002Bwi8H4kpV4lBMt0qsap/30OL7FSO4GmN50CG2u0mg0RcK\u002BtopBcUIQw/s7JZVxkcuJQqRdJ4w0/RUPwr2cxipJx8NaUCAwEAAaOCA0YwggNCMAwGA1UdEwEB/wQCMAAwMgYDVR0fBCswKTAnoCWgI4YhaHR0cDovL2NybC5jZXJ0dW0ucGwvZHZjYXNoYTIuY3JsMHEGCCsGAQUFBwEBBGUwYzArBggrBgEFBQcwAYYfaHR0cDovL2R2Y2FzaGEyLm9jc3AtY2VydHVtLmNvbTA0BggrBgEFBQcwAoYoaHR0cDovL3JlcG9zaXRvcnkuY2VydHVtLnBsL2R2Y2FzaGEyLmNlcjAfBgNVHSMEGDAWgBTlMa2/OhGW9IO8UDzUt5CbkO7eJTAdBgNVHQ4EFgQU3d9Ep3zOcc\u002BIDBQpjBVxp2WQamAwHQYDVR0SBBYwFIESZHZjYXNoYTJAY2VydHVtLnBsMEsGA1UdIAREMEIwCAYGZ4EMAQIBMDYGCyqEaAGG9ncCBQEDMCcwJQYIKwYBBQUHAgEWGWh0dHBzOi8vd3d3LmNlcnR1bS5wbC9DUFMwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMA4GA1UdDwEB/wQEAwIFoDAtBgNVHREEJjAkghEqLnRhdmFuYWJyb2tlci5pcoIPdGF2YW5hYnJva2VyLmlyMIIBfwYKKwYBBAHWeQIEAgSCAW8EggFrAWkAdgDuzdBk1dsazsVct520zROiModGfLzs3sNRSFlGcR\u002B1mwAAAYb1bJQMAAAEAwBHMEUCIQCz5\u002BWGuo\u002BEoorEnCyFDnsdCvrNIgkCTIdX30EEAmpjmgIgIVvksSkDq6p/wNUn7heJX3qcjMZlDmZGi\u002BBUmdCfPfQAdwBIsONr2qZHNA/lagL6nTDrHFIBy1bdLIHZu7\u002BrOdiEcwAAAYb1bJQlAAAEAwBIMEYCIQCYGohwv7ccikmR1JDlUyNVU3qIAsG0wJ81A45/dqA\u002BhQIhAP0HhrEpo4KX1ll416QSPvWMz/FOU1eP1VpCycPbqtL3AHYA2ra/az\u002B1tiKfm8K7XGvocJFxbLtRhIU0vaQ9MEjX\u002B6sAAAGG9WyUQAAABAMARzBFAiADC4UJRbLEzImXStxjX0oa0rPdbSuUMKJ0y9LsMMq1gwIhAN0a2MzMqdM3pnaqUYmsxdhdsJ0BBpm0dCcODHoUabWYMA0GCSqGSIb3DQEBCwUAA4IBAQBAlpoOhiJ6S0s5UNN2XXZK/5mPut9qc1mhxCk1SCzOp95yZJcMA/wBBrAjbpFr\u002Bwrg\u002B/jM\u002BOiJED1KORmJruzNW4A7cC4zxkWZTx9M3X47CxLKNoF3g2EzHvdLUZfKLOxOiWn/meA9reTIFxIv35IwhGZJFJ9Dqjix2AflVCS6um40Z79EvCwcFWItTKutlfUekMgF/7MHt/rWCyyO0FWA1/fZdzBwVdRqmkzzo3C\u002BlAM2WWZ\u002BtZUWGUZPgpDBvMCClE4iJOP0csADk9K06oUCai9/5OhDhiIjT6TTupj98TeJO0iekpAZUbOc8KtKF83CTtOqZlTM30z2esjOIt4h"],"alg":"RS256"},{"kty":"RSA","use":"sig","kid":"A087D976CED23FEF148EA55B5CEC6E2D","e":"AQAB","n":"28vro-wzAhDEstFRj_w_8sEOkIKKcauLaaSvVmaZtXvrvA7BijG93LpKwQaZrMsJyanH-4aP-iplN3yneYNsF6ir5ZloMKjhb3qg5sKRRyhozeA2JZ8mteZo_t7kWNf2F3tK8FCkNejSoT-g4O6scksTGlmZAeJh3ciTyjj6epNpWhcY7cXisP-KfFp-qUpr_-LNJ1r1Qs-R7j4PM3R4rR-FnyMf2BFOxROifb6DXUjhPts24ins4WVGPksN0bzijDrdmF3qEWB-_alRfOY7ex1hBC5OR6neLaJAfrMvrmZCD0WEGRrRUHdDgh1pBL_xLU7TOaPz3wm07kQK0CHT5w","alg":"RS256"}]} 

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
        print("Invalid Issuer")
    except ExpiredSignatureError as err:
        print("Signature has expired")
    except Exception as error:
        print("Wrong JWT", error)
    
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
