import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# This module contains the piece of code described previously
from jwksutils import rsa_pem_from_jwk
from config import setting
from jwt.exceptions import InvalidIssuerError, ExpiredSignatureError

valid_audiences = ['d7f48c21-2a19-4bdb-ace8-48928bff0eb5'] # id of the application prepared previously

# obtain jwks as you wish: configuration file, HTTP GET request to the endpoint returning them;
jwks = {"keys":[{"kty":"RSA","use":"sig","kid":"49C1F3BFFCBF7F5450979CECFDC4B0D177DA8164RS256","x5t":"ScHzv_y_f1RQl5zs_cSw0XfagWQ","e":"AQAB","n":"tZC4age3I9cIj_Utc2lzzCkvYj2bAJcx11rrkQMACbRU--NS7UUqcfZsxBZbVvgZTUPkPHcLmImBoJnw4v17eTJZKkkYn7HjJQLbnuczzAmdypOMYUzgOgRjgYasknvJLkg-0KMZ1uj_8R7QhOziApm9qtCH5GwV5_CpRPtAhT5tfVB_yyFw7p_1putsx6stYzgaW_5FoU97DDkF2wmtxf3mpNgUSzp7dBoSTw8YCu-jqh8iJhfvUOeuC_jR1TgGLDjU9WYTTWYFh09669tHYEqeXwDb1R7W3H3NfKQr3Wamrab84TRmvApQQUSh1IPxMJB9xR471wo5YXXsNCryuQ","x5c":["MIIGYDCCBUigAwIBAgIQEfF3RPSDUtZtUlgFMf5YqzANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMCUEwxIjAgBgNVBAoTGVVuaXpldG8gVGVjaG5vbG9naWVzIFMuQS4xJzAlBgNVBAsTHkNlcnR1bSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTEpMCcGA1UEAxMgQ2VydHVtIERvbWFpbiBWYWxpZGF0aW9uIENBIFNIQTIwHhcNMjIwOTA0MTM1MjAwWhcNMjMwOTA0MTM1MTU5WjAWMRQwEgYDVQQDDAsqLnRlY2gxYS5jbzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALWQuGoHtyPXCI/1LXNpc8wpL2I9mwCXMdda65EDAAm0VPvjUu1FKnH2bMQWW1b4GU1D5Dx3C5iJgaCZ8OL9e3kyWSpJGJ\u002Bx4yUC257nM8wJncqTjGFM4DoEY4GGrJJ7yS5IPtCjGdbo//Ee0ITs4gKZvarQh\u002BRsFefwqUT7QIU\u002BbX1Qf8shcO6f9abrbMerLWM4Glv\u002BRaFPeww5BdsJrcX95qTYFEs6e3QaEk8PGArvo6ofIiYX71Dnrgv40dU4Biw41PVmE01mBYdPeuvbR2BKnl8A29Ue1tx9zXykK91mpq2m/OE0ZrwKUEFEodSD8TCQfcUeO9cKOWF17DQq8rkCAwEAAaOCAzgwggM0MAwGA1UdEwEB/wQCMAAwMgYDVR0fBCswKTAnoCWgI4YhaHR0cDovL2NybC5jZXJ0dW0ucGwvZHZjYXNoYTIuY3JsMHEGCCsGAQUFBwEBBGUwYzArBggrBgEFBQcwAYYfaHR0cDovL2R2Y2FzaGEyLm9jc3AtY2VydHVtLmNvbTA0BggrBgEFBQcwAoYoaHR0cDovL3JlcG9zaXRvcnkuY2VydHVtLnBsL2R2Y2FzaGEyLmNlcjAfBgNVHSMEGDAWgBTlMa2/OhGW9IO8UDzUt5CbkO7eJTAdBgNVHQ4EFgQUVpau/fkXDgXObhLU1ADBgoTHlowwHQYDVR0SBBYwFIESZHZjYXNoYTJAY2VydHVtLnBsMEsGA1UdIAREMEIwCAYGZ4EMAQIBMDYGCyqEaAGG9ncCBQEDMCcwJQYIKwYBBQUHAgEWGWh0dHBzOi8vd3d3LmNlcnR1bS5wbC9DUFMwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMA4GA1UdDwEB/wQEAwIFoDAhBgNVHREEGjAYggsqLnRlY2gxYS5jb4IJdGVjaDFhLmNvMIIBfQYKKwYBBAHWeQIEAgSCAW0EggFpAWcAdgBVgdTCFpA2AUrqC5tXPFPwwOQ4eHAlCBcvo6odBxPTDAAAAYMIxcBrAAAEAwBHMEUCIQCoaBBAkJqOBfY7wi4k80xRiHRtv4cpRMCnY\u002BpRphsyJQIgc/ujvwzEaVv19DCRe4SOM3D2ixys2cjEHirRphNIohMAdgCt9776fP8QyIudPZwePhhqtGcpXc\u002BxDCTKhYY069yCigAAAYMIxcBDAAAEAwBHMEUCIQDWzBu/dfasatNaMjd7TcHLc0oXKw3K0oCV083KpkTACAIgbP61I6kg4LxJhjr3DzUJcyCLoZRbYLNAnvPM5SaNrQ4AdQB6MoxU2LcttiDqOOBSHumEFnAyE4VNO9IrwTpXo1LrUgAAAYMIxcC6AAAEAwBGMEQCIEuZm1yYK3ySLEHBbzur8pmYu\u002BrcU8\u002BYAcR9q8npwSI9AiBbdbfyEYXJFEd2tdHYqyfka3OY\u002BBAEwOms\u002BkhrrztuMTANBgkqhkiG9w0BAQsFAAOCAQEAAA4k428eRjyu/NZSpX9K2H4m\u002BZ4/1Pb4CrzqUnN\u002BDWExFAHjZf24fSR6ueOFJ2HdDmbvEtjt6tR\u002B2u\u002BBYykoyfXfCJ4YR8HoFQBQQvANcs2g24Y0n0u/JPuUV\u002BmEvNjaO0XbaxUDMUoJeRiimpd7mbZXZSXgq3FEvryaDGDNyvLBh6JymIp77xm/YYpBWekk0PFpGWOHdOlAVFXr2KHGeXyFi3aVQCxZM/vag5GJuotGgj2SBvh82Tbj9h\u002BKVOTFVgvXUiUa/tbgK\u002B7Nwq0WWiz1ZeX20bQnUdfwya2I38t2ltKlqzyByxWF50A9aYTL9h1Z8o7sF6aOSq3lTR2xYA=="],"alg":"RS256"},{"kty":"RSA","use":"sig","kid":"2409BFB326FD14C1CABBB7CE04196685","e":"AQAB","n":"s9ZGBddXkYSuAE1tSha30i-RVuzU4SpDLofYmpJFJV-bFnBgSoz_lD20c5YEZuDIhyrx7-sIblEFIr_x0FaymwuD0J5xaeGndV_XoUVnVK9HG_Sq-vVJnWpsFwUwJ9LfQUdiN_VQ08K05sq8lMaPyzK0_ms1HNucTkKv0q5EGaqQc5Ow1hFdUtFEa-Gsoq4hAQH0ZdKO3IoUwkZETyeQeRm6lJNNlH-gA0Y5OFLR6WNsDYxSn5OKk4n5ITSS0rkMzywXo-5pHX-zwQ-m8ysULOqSTJpKlGSm3kXC3gGOphHzM1vUYPpOKevLj-TMAPF-GMaHCvPXZWZ2nPF3zMJ-JQ","alg":"RS256"}]}
# jwks = {
#     "keys": [
# 		{
# 			"kty": "RSA",
# 			"use": "sig",
# 			"kid": "49C1F3BFFCBF7F5450979CECFDC4B0D177DA8164RS256",
# 			"x5t": "ScHzv_y_f1RQl5zs_cSw0XfagWQ",
# 			"e": "AQAB",
# 			"n": "tZC4age3I9cIj_Utc2lzzCkvYj2bAJcx11rrkQMACbRU--NS7UUqcfZsxBZbVvgZTUPkPHcLmImBoJnw4v17eTJZKkkYn7HjJQLbnuczzAmdypOMYUzgOgRjgYasknvJLkg-0KMZ1uj_8R7QhOziApm9qtCH5GwV5_CpRPtAhT5tfVB_yyFw7p_1putsx6stYzgaW_5FoU97DDkF2wmtxf3mpNgUSzp7dBoSTw8YCu-jqh8iJhfvUOeuC_jR1TgGLDjU9WYTTWYFh09669tHYEqeXwDb1R7W3H3NfKQr3Wamrab84TRmvApQQUSh1IPxMJB9xR471wo5YXXsNCryuQ",
# 			"x5c": [
# 				"MIIGYDCCBUigAwIBAgIQEfF3RPSDUtZtUlgFMf5YqzANBgkqhkiG9w0BAQsFADCBhTELMAkGA1UEBhMCUEwxIjAgBgNVBAoTGVVuaXpldG8gVGVjaG5vbG9naWVzIFMuQS4xJzAlBgNVBAsTHkNlcnR1bSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTEpMCcGA1UEAxMgQ2VydHVtIERvbWFpbiBWYWxpZGF0aW9uIENBIFNIQTIwHhcNMjIwOTA0MTM1MjAwWhcNMjMwOTA0MTM1MTU5WjAWMRQwEgYDVQQDDAsqLnRlY2gxYS5jbzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALWQuGoHtyPXCI/1LXNpc8wpL2I9mwCXMdda65EDAAm0VPvjUu1FKnH2bMQWW1b4GU1D5Dx3C5iJgaCZ8OL9e3kyWSpJGJ+x4yUC257nM8wJncqTjGFM4DoEY4GGrJJ7yS5IPtCjGdbo//Ee0ITs4gKZvarQh+RsFefwqUT7QIU+bX1Qf8shcO6f9abrbMerLWM4Glv+RaFPeww5BdsJrcX95qTYFEs6e3QaEk8PGArvo6ofIiYX71Dnrgv40dU4Biw41PVmE01mBYdPeuvbR2BKnl8A29Ue1tx9zXykK91mpq2m/OE0ZrwKUEFEodSD8TCQfcUeO9cKOWF17DQq8rkCAwEAAaOCAzgwggM0MAwGA1UdEwEB/wQCMAAwMgYDVR0fBCswKTAnoCWgI4YhaHR0cDovL2NybC5jZXJ0dW0ucGwvZHZjYXNoYTIuY3JsMHEGCCsGAQUFBwEBBGUwYzArBggrBgEFBQcwAYYfaHR0cDovL2R2Y2FzaGEyLm9jc3AtY2VydHVtLmNvbTA0BggrBgEFBQcwAoYoaHR0cDovL3JlcG9zaXRvcnkuY2VydHVtLnBsL2R2Y2FzaGEyLmNlcjAfBgNVHSMEGDAWgBTlMa2/OhGW9IO8UDzUt5CbkO7eJTAdBgNVHQ4EFgQUVpau/fkXDgXObhLU1ADBgoTHlowwHQYDVR0SBBYwFIESZHZjYXNoYTJAY2VydHVtLnBsMEsGA1UdIAREMEIwCAYGZ4EMAQIBMDYGCyqEaAGG9ncCBQEDMCcwJQYIKwYBBQUHAgEWGWh0dHBzOi8vd3d3LmNlcnR1bS5wbC9DUFMwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMA4GA1UdDwEB/wQEAwIFoDAhBgNVHREEGjAYggsqLnRlY2gxYS5jb4IJdGVjaDFhLmNvMIIBfQYKKwYBBAHWeQIEAgSCAW0EggFpAWcAdgBVgdTCFpA2AUrqC5tXPFPwwOQ4eHAlCBcvo6odBxPTDAAAAYMIxcBrAAAEAwBHMEUCIQCoaBBAkJqOBfY7wi4k80xRiHRtv4cpRMCnY+pRphsyJQIgc/ujvwzEaVv19DCRe4SOM3D2ixys2cjEHirRphNIohMAdgCt9776fP8QyIudPZwePhhqtGcpXc+xDCTKhYY069yCigAAAYMIxcBDAAAEAwBHMEUCIQDWzBu/dfasatNaMjd7TcHLc0oXKw3K0oCV083KpkTACAIgbP61I6kg4LxJhjr3DzUJcyCLoZRbYLNAnvPM5SaNrQ4AdQB6MoxU2LcttiDqOOBSHumEFnAyE4VNO9IrwTpXo1LrUgAAAYMIxcC6AAAEAwBGMEQCIEuZm1yYK3ySLEHBbzur8pmYu+rcU8+YAcR9q8npwSI9AiBbdbfyEYXJFEd2tdHYqyfka3OY+BAEwOms+khrrztuMTANBgkqhkiG9w0BAQsFAAOCAQEAAA4k428eRjyu/NZSpX9K2H4m+Z4/1Pb4CrzqUnN+DWExFAHjZf24fSR6ueOFJ2HdDmbvEtjt6tR+2u+BYykoyfXfCJ4YR8HoFQBQQvANcs2g24Y0n0u/JPuUV+mEvNjaO0XbaxUDMUoJeRiimpd7mbZXZSXgq3FEvryaDGDNyvLBh6JymIp77xm/YYpBWekk0PFpGWOHdOlAVFXr2KHGeXyFi3aVQCxZM/vag5GJuotGgj2SBvh82Tbj9h+KVOTFVgvXUiUa/tbgK+7Nwq0WWiz1ZeX20bQnUdfwya2I38t2ltKlqzyByxWF50A9aYTL9h1Z8o7sF6aOSq3lTR2xYA=="
# 			],
# 			"alg": "RS256"
# 		},
# 		{
# 			"kty": "RSA",
# 			"use": "sig",
# 			"kid": "91DF7D4D4140ED7B6EBD0B1D9BE8C2EF",
# 			"e": "AQAB",
# 			"n": "67qbw1RlmIlX7M22AWVk1MkxCUkluo_2FPe4tmrzmitV2MHyNaL2uGrIcnU3dFreEWcM13dcqLsmKsyxHu9nmDgCmJDZ-do6H7VC32mdD2AsBOF5RD7nAl8DbcA2eqMVxldkfDa4Qb8W-WcsxIcmZaDmquCb_jRsSXSLXaTK-iivi1AoeFXM2zWYXWzN_vno_oyGrvY_Op5N9uE1kX8SA40-YG1-PXLCmFJNt_2VN7DuVj870qUegMFs0JkdKqiTfeWrsdG_x3L7pGt0TKN2OWQACT3vUsZyVYov7GGoxl2q_2xpFLHQWJGvDHqSjfiLZA12seOJY72_DHvUSMcrVQ",
# 			"alg": "RS256"
# 		}
#     ]
# }

# configuration, these can be seen in valid JWTs from Azure B2C:
# valid_audiences = ['d7f48c21-2a19-4bdb-ace8-48928bff0eb5'] # id of the application prepared previously
issuer = 'https://cluster.tech1a.co' # iss


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

    # do what you wish with decoded token:
    # if we get here, the JWT is validated
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
