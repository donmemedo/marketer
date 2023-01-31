def marketer_entity(marketer) -> dict:
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
    "IdpId": marketer.get("IdpId")
    }


def fee_entity(fee) -> dict:
    return {
        "TotalFee": fee.get("TotalFee")
    }


def volume_entity(volume) -> dict:
    return {
        "TotalVolume": volume.get("TotalVolume")
    }
