"""_summary_
"""
def marketer_entity(marketer) -> dict:
    """_summary_

    Args:
        marketer (_type_): _description_

    Returns:
        dict: _description_
    """
    return {
    "Id": marketer.get("Id"),
    "FirstName": marketer.get("FirstName"),
    "LastName": marketer.get("LastName"),
    "IsOrganization": marketer.get("IsOrganization"),
    "RefererType": marketer.get("RefererType"),
    "CreatedBy": marketer.get("CreatedBy"),
    "CreateDate": marketer.get("CreateDate"),
    "ModifiedBy": marketer.get("ModifiedBy"),
    "ModifiedDate": marketer.get("ModifiedDate"),
    "IsCustomer": marketer.get("IsCustomer"),
    "IsEmployee": marketer.get("IsEmployee"),
    "CustomerType": marketer.get("CustomerType"),
    "IdpId": marketer.get("IdpId"),
    "InvitationLink": marketer.get("InvitationLink")
    }


def fee_entity(fee) -> dict:
    """_summary_

    Args:
        fee (_type_): _description_

    Returns:
        dict: _description_
    """
    return {
        "TotalFee": fee.get("TotalFee")
    }


def volume_entity(volume) -> dict:
    """_summary_

    Args:
        volume (_type_): _description_

    Returns:
        dict: _description_
    """
    return {
        "TotalVolume": volume.get("TotalVolume")
    }
